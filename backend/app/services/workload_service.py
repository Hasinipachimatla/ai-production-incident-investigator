import logging
from typing import Dict, Any, Optional
import sys
import os

# Ensure scripts dir is accessible for import
scripts_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../scripts"))
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

from customer_workload_generator import CustomerWorkloadGenerator
from app.core.config import settings

logger = logging.getLogger("incident_investigator.workload")

class WorkloadService:
    """
    Manages customer workload generation lifecycle against ShopEase.
    """
    def __init__(self):
        self._generator: Optional[CustomerWorkloadGenerator] = None

    def start_workload(
        self,
        concurrency: int = 35,
        ramp_seconds: float = 6.0,
        request_delay_sec: float = 0.04
    ) -> Dict[str, Any]:
        """Starts background customer workload generator."""
        if self._generator and self._generator.is_running():
            return {
                "success": True,
                "message": "Customer workload generator is already active.",
                "stats": self._generator.get_stats()
            }

        target_url = settings.SHOP_EASE_BASE_URL
        self._generator = CustomerWorkloadGenerator(
            base_url=target_url,
            target_concurrency=concurrency,
            ramp_seconds=ramp_seconds,
            request_delay_sec=request_delay_sec
        )
        self._generator.start()
        logger.info(f"[Workload Service] Started customer workload generator with concurrency={concurrency} against {target_url}")
        return {
            "success": True,
            "message": f"Customer workload generator started with target concurrency={concurrency}.",
            "stats": self._generator.get_stats()
        }

    def stop_workload(self) -> Dict[str, Any]:
        """Stops active customer workload generator."""
        if not self._generator or not self._generator.is_running():
            return {
                "success": True,
                "message": "Customer workload generator is not running.",
                "stats": {"is_running": False}
            }

        self._generator.stop()
        logger.info("[Workload Service] Customer workload generator stopped.")
        return {
            "success": True,
            "message": "Customer workload generator stopped.",
            "stats": self._generator.get_stats()
        }

    def get_status(self) -> Dict[str, Any]:
        """Returns current workload statistics."""
        if not self._generator:
            return {
                "is_running": False,
                "target_concurrency": 0,
                "active_workers": 0,
                "total_requests": 0,
                "current_rps": 0.0,
                "error_rate_pct": 0.0,
                "p99_latency_ms": 0.0
            }
        return self._generator.get_stats()

workload_service = WorkloadService()

