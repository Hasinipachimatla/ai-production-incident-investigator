import json
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.core.config import settings

class RetrievalEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            token_pattern=r"(?u)\b[a-zA-Z0-9_\-\.]{2,}\b",
            ngram_range=(1, 2),
            sublinear_tf=True
        )
        self.cases: List[Dict[str, Any]] = []
        self.case_corpus: List[str] = []
        self.is_fitted: bool = False
        
        # Auto-load historical incidents from data path if present
        if settings.HISTORICAL_INCIDENTS_PATH.exists():
            try:
                with open(settings.HISTORICAL_INCIDENTS_PATH, "r", encoding="utf-8") as f:
                    initial_cases = json.load(f)
                    self.load_cases(initial_cases)
            except Exception:
                pass

    def load_cases(self, cases: List[Dict[str, Any]]):
        self.cases = cases
        self.case_corpus = [self._case_to_document(c) for c in cases]
        if self.case_corpus:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.case_corpus)
            self.is_fitted = True

    def _case_to_document(self, case: Dict[str, Any]) -> str:
        parts = [
            str(case.get("title") or ""),
            str(case.get("symptoms") or ""),
            str(case.get("category") or ""),
            str(case.get("service") or ""),
            str(case.get("root_cause") or ""),
            " ".join([str(t) for t in (case.get("tags") or [])])
        ]
        logs = case.get("log_patterns") or []
        if isinstance(logs, list):
            parts.extend([str(l) for l in logs])
        elif isinstance(logs, str):
            try:
                parsed = json.loads(logs)
                if isinstance(parsed, list):
                    parts.extend([str(l) for l in parsed])
                else:
                    parts.append(logs)
            except Exception:
                parts.append(logs)
        return " ".join(parts).lower()

    def _score_candidates(self, query_text: str, service_hint: Optional[str] = None) -> List[Tuple[Dict[str, Any], float, Dict[str, Any]]]:
        if not self.is_fitted or not self.cases:
            return []

        clean_query = (query_text or "").lower()
        stop_words = {'slo', 'anomaly', 'detected', 'current', 'breached', 'threshold', 'status', 'value', 'operator', 'signal', 'metrics'}
        clean_tokens = [t for t in clean_query.replace(".", " ").replace(",", " ").replace(":", " ").replace("-", " ").replace("(", " ").replace(")", " ").replace("%", " ").split() if len(t) > 2 and t not in stop_words]
        query_tokens = set(clean_tokens)
        if not clean_query.strip():
            return []

        query_vec = self.vectorizer.transform([clean_query])
        raw_sims = cosine_similarity(query_vec, self.tfidf_matrix)[0]

        scored = []
        for idx, case in enumerate(self.cases):
            tfidf_sim = float(raw_sims[idx])
            
            # Query token coverage in case document
            doc_text = self.case_corpus[idx]
            doc_tokens = set(doc_text.split())
            if query_tokens:
                matched_tokens = sorted(list(query_tokens & doc_tokens))
                coverage = len(matched_tokens) / len(query_tokens)
            else:
                matched_tokens = []
                coverage = 0.0

            # Service and category alignment bonus
            service_match = False
            if service_hint:
                svc_h = service_hint.lower()
                case_svc = str(case.get("service", "")).lower()
                case_cat = str(case.get("category", "")).lower()
                if svc_h == case_svc or svc_h in case_svc or case_svc in svc_h:
                    service_match = True
                elif ("database" in svc_h or "postgres" in svc_h or "db" in svc_h) and ("database" in case_cat or "database" in case_svc or "postgres" in case_svc):
                    service_match = True
                elif "cache" in svc_h and ("cache" in case_cat or "cache" in case_svc or "redis" in case_svc):
                    service_match = True
                elif ("breaker" in svc_h or "circuit" in svc_h or "inventory" in svc_h) and ("circuit" in case_cat or "inventory" in case_svc or "breaker" in case_cat):
                    service_match = True
                elif "catalog" in svc_h and ("catalog" in case_svc or "latency" in case_cat):
                    service_match = True
                elif "order" in svc_h and ("order" in case_svc or "error" in case_cat):
                    service_match = True

            service_bonus = 0.10 if service_match else 0.0

            # Calibrated composite similarity score
            sim = (0.50 * tfidf_sim) + (0.50 * coverage) + service_bonus
            sim = min(1.0, max(0.0, sim))

            evidence_detail = {
                "matched_tokens": matched_tokens[:8],
                "token_coverage_pct": round(coverage * 100, 1),
                "tfidf_similarity": round(tfidf_sim, 4),
                "service_alignment_bonus": service_bonus,
                "service_match": service_match
            }
            scored.append((case, sim, evidence_detail))

        # Deterministic sort: score descending, case ID ascending on ties
        scored.sort(key=lambda x: (-x[1], str(x[0].get("id", ""))))
        return scored

    def retrieve_fixed_top_k(
        self,
        query_text: str,
        k: int = 3,
        service_hint: Optional[str] = None,
        ground_truth_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Baseline Method: Unconditionally returns top K cases."""
        scored = self._score_candidates(query_text, service_hint)
        selected = scored[:k]

        candidates = []
        retrieved_ids = []
        for case, score, matching_ev in selected:
            retrieved_ids.append(case["id"])
            is_irrelevant = None
            if ground_truth_ids is not None:
                is_irrelevant = case["id"] not in ground_truth_ids
            candidates.append({
                "id": case["id"],
                "title": case.get("title", ""),
                "category": case.get("category", "general"),
                "service": case.get("service", "unknown"),
                "symptoms": case.get("symptoms", ""),
                "root_cause": case.get("root_cause", ""),
                "recommended_remediation": case.get("recommended_remediation", ""),
                "similarity_score": round(score, 4),
                "is_irrelevant": is_irrelevant,
                "matching_evidence": matching_ev
            })

        metrics = self.calculate_metrics(retrieved_ids, ground_truth_ids) if ground_truth_ids is not None else {}

        return {
            "method": "fixed_top_k",
            "k_applied": k,
            "threshold_applied": None,
            "retrieved_count": len(candidates),
            "irrelevant_count": metrics.get("irrelevant_count"),
            "precision": metrics.get("precision"),
            "recall": metrics.get("recall"),
            "f1_score": metrics.get("f1_score"),
            "candidates": candidates
        }

    def retrieve_adaptive_threshold(
        self,
        query_text: str,
        threshold: float = 0.55,
        max_k: int = 5,
        service_hint: Optional[str] = None,
        ground_truth_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Proposed Method: Relevance-threshold-based adaptive retrieval.
        Filters candidates below similarity threshold and avoids forcing irrelevant cases.
        """
        scored = self._score_candidates(query_text, service_hint)
        # Filter by threshold
        filtered = [item for item in scored if item[1] >= threshold]

        # Dynamic truncation if top score is high and subsequent drops off sharply
        if len(filtered) > 1:
            top_score = filtered[0][1]
            dynamic_kept = [filtered[0]]
            for item in filtered[1:max_k]:
                # If score drop is less than 0.35 from top score and still above threshold
                if (top_score - item[1]) < 0.35 and item[1] >= threshold:
                    dynamic_kept.append(item)
                else:
                    break
            selected = dynamic_kept
        else:
            selected = filtered[:max_k]

        candidates = []
        retrieved_ids = []
        for case, score, matching_ev in selected:
            retrieved_ids.append(case["id"])
            is_irrelevant = None
            if ground_truth_ids is not None:
                is_irrelevant = case["id"] not in ground_truth_ids
            candidates.append({
                "id": case["id"],
                "title": case.get("title", ""),
                "category": case.get("category", "general"),
                "service": case.get("service", "unknown"),
                "symptoms": case.get("symptoms", ""),
                "root_cause": case.get("root_cause", ""),
                "recommended_remediation": case.get("recommended_remediation", ""),
                "similarity_score": round(score, 4),
                "is_irrelevant": is_irrelevant,
                "matching_evidence": matching_ev
            })

        metrics = self.calculate_metrics(retrieved_ids, ground_truth_ids) if ground_truth_ids is not None else {}

        return {
            "method": "adaptive_threshold",
            "k_applied": len(candidates),
            "threshold_applied": threshold,
            "retrieved_count": len(candidates),
            "irrelevant_count": metrics.get("irrelevant_count"),
            "precision": metrics.get("precision"),
            "recall": metrics.get("recall"),
            "f1_score": metrics.get("f1_score"),
            "candidates": candidates
        }

    def compare_methods(
        self,
        query_text: str,
        threshold: float = 0.55,
        top_k: int = 3,
        service_hint: Optional[str] = None,
        ground_truth_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        fixed = self.retrieve_fixed_top_k(query_text, k=top_k, service_hint=service_hint, ground_truth_ids=ground_truth_ids)
        adaptive = self.retrieve_adaptive_threshold(query_text, threshold=threshold, service_hint=service_hint, ground_truth_ids=ground_truth_ids)

        # Formulate comparative analysis summary
        fixed_count = fixed["retrieved_count"]
        adapt_count = adaptive["retrieved_count"]
        fixed_irrel = fixed.get("irrelevant_count", 0) or 0
        adapt_irrel = adaptive.get("irrelevant_count", 0) or 0
        noise_diff = fixed_irrel - adapt_irrel

        if adapt_count == 0:
            analysis = (
                f"Adaptive retrieval filtered out all irrelevant cases (noise reduced by {noise_diff}), "
                f"recognizing this as an out-of-domain or novel incident pattern, whereas Top-K={top_k} "
                f"unconditionally forced {fixed_count} low-confidence cases into context."
            )
        elif noise_diff > 0:
            analysis = (
                f"Adaptive retrieval eliminated {noise_diff} irrelevant case(s) (Precision: {adaptive.get('precision', 0):.2f} "
                f"vs Baseline: {fixed.get('precision', 0):.2f}), improving signal-to-noise ratio for downstream RCA."
            )
        else:
            analysis = (
                f"Both methods identified matching historical precedents. Adaptive retrieval retained "
                f"{adapt_count} high-confidence case(s) above threshold {threshold}."
            )

        return {
            "query_text": query_text,
            "ground_truth_case_ids": ground_truth_ids,
            "fixed_top_k": fixed,
            "adaptive": adaptive,
            "analysis": analysis
        }

    @staticmethod
    def calculate_metrics(retrieved_ids: List[str], ground_truth_ids: Optional[List[str]]) -> Dict[str, Any]:
        if ground_truth_ids is None:
            return {}

        ret_set = set(retrieved_ids)
        gt_set = set(ground_truth_ids)

        tp = len(ret_set & gt_set)
        fp = len(ret_set - gt_set)  # irrelevant cases retrieved
        fn = len(gt_set - ret_set)

        # Handle edge cases (empty ground truth or empty retrieval)
        if len(ret_set) == 0:
            precision = 1.0 if len(gt_set) == 0 else 0.0
        else:
            precision = tp / (tp + fp)

        if len(gt_set) == 0:
            recall = 1.0 if len(ret_set) == 0 else 0.0
        else:
            recall = tp / (tp + fn)

        if (precision + recall) > 0:
            f1 = 2 * (precision * recall) / (precision + recall)
        else:
            f1 = 0.0

        return {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "irrelevant_count": fp,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4)
        }

retrieval_engine = RetrievalEngine()
