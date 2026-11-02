import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.shopease_adapter import shopease_adapter
from app.api.incident_routes import detect_and_investigate

logger = logging.getLogger("incident_investigator.monitoring")

class BackgroundMonitoringService:
    """
    Continuous Autonomous Background Monitoring Daemon for ShopEase.
    Monitors operational health, error rates, latencies, resource pools, and circuits.
    Automatically triggers evidence collection, RCA, and incident creation upon sustained anomalies.
    Runs independently of any frontend or browser presence.
    """
    def __init__(self):
        self.enabled: bool = settings.ENABLE_BACKGROUND_MONITORING
        self.interval_seconds: float = settings.MONITORING_INTERVAL_SECONDS
        self.consecutive_anomalies_threshold: int = settings.CONSECUTIVE_ANOMALIES_THRESHOLD
        
        self.is_running: bool = False
        self._task: Optional[asyncio.Task] = None
        
        # Operational telemetry state
        self.last_poll_timestamp: Optional[str] = None
        self.last_poll_success: bool = False
        self.last_error: Optional[str] = None
        self.polls_count: int = 0
        self.consecutive_anomalies: int = 0
        self.consecutive_healthy: int = 0
        self.last_anomaly_details: List[Dict[str, Any]] = []
        self.active_incident_id: Optional[str] = None
        self.incidents_created_count: int = 0

    def start(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        """Starts the background monitoring task."""
        if self.is_running:
            return
        self.is_running = True
        try:
            active_loop = loop or asyncio.get_running_loop()
            self._task = active_loop.create_task(self._monitor_loop())
        except RuntimeError:
            try:
                active_loop = asyncio.get_event_loop()
                self._task = active_loop.create_task(self._monitor_loop())
            except Exception as e:
                logger.warning(f"[Monitoring Service] Could not bind background task to loop: {e}")
        logger.info(
            f"[Monitoring Service] Started background monitor on ShopEase ({settings.SHOP_EASE_BASE_URL}) "
            f"polling every {self.interval_seconds}s (sustained threshold={self.consecutive_anomalies_threshold})."
        )

    def stop(self):
        """Stops the background monitoring task cleanly."""
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("[Monitoring Service] Background monitoring service stopped.")

    def reset_state(self):
        """Resets daemon streak counters and active incident tracking to clean nominal baseline."""
        self.consecutive_anomalies = 0
        self.consecutive_healthy = 0
        self.last_anomaly_details = []
        self.active_incident_id = None
        logger.info("[Monitoring Service] Background monitoring state reset to nominal baseline.")

    async def _monitor_loop(self):
        """Infinite polling loop running in the background."""
        while self.is_running:
            try:
                await self.poll_cycle()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.last_poll_success = False
                self.last_error = str(e)
                logger.error(f"[Monitoring Service] Unexpected error in poll cycle: {e}")

            try:
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                break

    async def poll_cycle(self) -> Dict[str, Any]:
        """Executes a single monitoring inspection cycle against ShopEase."""
        now_iso = datetime.utcnow().isoformat() + "Z"
        self.polls_count += 1
        self.last_poll_timestamp = now_iso

        # 1. Collect telemetry snapshot via adapter
        try:
            # Run blocking HTTP call in executor to keep event loop unblocked
            loop = asyncio.get_running_loop()
            snapshot = await loop.run_in_executor(None, shopease_adapter.collect_snapshot)
            self.last_poll_success = True
            self.last_error = None
        except Exception as e:
            self.last_poll_success = False
            self.last_error = f"ShopEase unreachable: {str(e)}"
            # Temporary connectivity drop is tracked but not treated as a new internal fault
            return {
                "success": False,
                "timestamp": now_iso,
                "error": self.last_error
            }

        anomaly_detected = snapshot.get("anomaly_detected", False)
        anomalies = snapshot.get("anomalies", [])

        # 2. Evaluate sustained anomaly condition
        if not anomaly_detected:
            self.consecutive_anomalies = 0
            self.consecutive_healthy += 1
            self.last_anomaly_details = []
            if self.consecutive_healthy >= 2:
                self.active_incident_id = None
            return {
                "success": True,
                "timestamp": now_iso,
                "anomaly_detected": False,
                "consecutive_anomalies": 0,
                "consecutive_healthy": self.consecutive_healthy,
                "active_incident_id": self.active_incident_id
            }

        # Anomaly is present
        self.consecutive_anomalies += 1
        self.consecutive_healthy = 0
        self.last_anomaly_details = anomalies

        logger.warning(
            f"[Monitoring Service] Anomaly detected in ShopEase (streak: {self.consecutive_anomalies}/"
            f"{self.consecutive_anomalies_threshold}): {[a['metric'] for a in anomalies]}"
        )

        # 3. Check if sustained threshold reached for automatic incident creation
        if self.consecutive_anomalies >= self.consecutive_anomalies_threshold:
            db = SessionLocal()
            try:
                # Trigger autonomous detection and RCA investigation using the sustained anomaly snapshot
                result = detect_and_investigate(source="shopease", db=db, preloaded_snapshot=snapshot)
                if result.get("incident_created"):
                    inc_data = result["incident"]
                    self.active_incident_id = getattr(inc_data, "id", None) or (inc_data.get("id") if isinstance(inc_data, dict) else str(inc_data))
                    culprit_name = getattr(inc_data, "culprit_service", None) or (inc_data.get("culprit_service") if isinstance(inc_data, dict) else "unknown-service")
                    self.incidents_created_count += 1
                    logger.critical(
                        f"[Monitoring Service] 🚨 SUSTAINED ANOMALY CONFIRMED! Automatically created incident "
                        f"[{self.active_incident_id}] for culprit '{culprit_name}'. "
                        "Incident placed in AWAITING_APPROVAL."
                    )
                elif result.get("is_duplicate"):
                    existing = result.get("incident")
                    self.active_incident_id = getattr(existing, "id", None) or (existing.get("id") if isinstance(existing, dict) else str(existing))
                    logger.info(
                        f"[Monitoring Service] Sustained anomaly tracked by ongoing active incident [{self.active_incident_id}]. "
                        "Duplicate incident prevented."
                    )
            finally:
                db.close()

        return {
            "success": True,
            "timestamp": now_iso,
            "anomaly_detected": True,
            "anomalies": anomalies,
            "consecutive_anomalies": self.consecutive_anomalies,
            "active_incident_id": self.active_incident_id
        }

    def get_status(self) -> Dict[str, Any]:
        """Returns the current operational monitoring status."""
        return {
            "enabled": self.enabled,
            "is_running": self.is_running,
            "target_system": "shopease",
            "target_url": settings.SHOP_EASE_BASE_URL,
            "polling_interval_seconds": self.interval_seconds,
            "consecutive_threshold": self.consecutive_anomalies_threshold,
            "polls_count": self.polls_count,
            "last_poll_timestamp": self.last_poll_timestamp,
            "last_poll_success": self.last_poll_success,
            "last_error": self.last_error,
            "consecutive_anomalies": self.consecutive_anomalies,
            "consecutive_healthy": self.consecutive_healthy,
            "last_anomaly_details": self.last_anomaly_details,
            "active_incident_id": self.active_incident_id,
            "incidents_created_count": self.incidents_created_count
        }

monitoring_service = BackgroundMonitoringService()

