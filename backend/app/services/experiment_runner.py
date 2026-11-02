import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from app.core.config import settings
from app.services.retrieval_engine import retrieval_engine

class ExperimentRunner:
    def __init__(self):
        pass

    def run_benchmark_experiment(
        self,
        threshold: float = 0.55,
        top_k: int = 3,
        eval_dataset_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        path = eval_dataset_path or settings.EVAL_DATASET_PATH
        if not path.exists():
            raise FileNotFoundError(f"Evaluation dataset file not found at: {path}")

        with open(path, "r", encoding="utf-8") as f:
            eval_queries = json.load(f)

        query_results: List[Dict[str, Any]] = []

        baseline_precisions = []
        baseline_recalls = []
        baseline_f1s = []
        baseline_retrieved_total = 0
        baseline_irrelevant_total = 0

        adaptive_precisions = []
        adaptive_recalls = []
        adaptive_f1s = []
        adaptive_retrieved_total = 0
        adaptive_irrelevant_total = 0

        for item in eval_queries:
            qid = item.get("query_id")
            qtext = item.get("query_text")
            service = item.get("service")
            gt_ids = item.get("ground_truth_case_ids", [])

            # Run Baseline Top-K
            fixed_res = retrieval_engine.retrieve_fixed_top_k(
                query_text=qtext,
                k=top_k,
                service_hint=service,
                ground_truth_ids=gt_ids
            )

            # Run Proposed Adaptive Threshold
            adaptive_res = retrieval_engine.retrieve_adaptive_threshold(
                query_text=qtext,
                threshold=threshold,
                service_hint=service,
                ground_truth_ids=gt_ids
            )

            top_k_ids = [c["id"] for c in fixed_res["candidates"]]
            adapt_ids = [c["id"] for c in adaptive_res["candidates"]]

            p_base = fixed_res.get("precision", 0.0)
            r_base = fixed_res.get("recall", 0.0)
            f_base = fixed_res.get("f1_score", 0.0)
            count_base = fixed_res["retrieved_count"]
            irrel_base = fixed_res.get("irrelevant_count", 0)

            p_adapt = adaptive_res.get("precision", 0.0)
            r_adapt = adaptive_res.get("recall", 0.0)
            f_adapt = adaptive_res.get("f1_score", 0.0)
            count_adapt = adaptive_res["retrieved_count"]
            irrel_adapt = adaptive_res.get("irrelevant_count", 0)

            baseline_precisions.append(p_base)
            baseline_recalls.append(r_base)
            baseline_f1s.append(f_base)
            baseline_retrieved_total += count_base
            baseline_irrelevant_total += irrel_base

            adaptive_precisions.append(p_adapt)
            adaptive_recalls.append(r_adapt)
            adaptive_f1s.append(f_adapt)
            adaptive_retrieved_total += count_adapt
            adaptive_irrelevant_total += irrel_adapt

            noise_reduction = irrel_base - irrel_adapt

            query_results.append({
                "query_id": qid,
                "query_text": qtext,
                "service": service,
                "ground_truth_count": len(gt_ids),
                "ground_truth_ids": gt_ids,
                "top_k_retrieved_ids": top_k_ids,
                "top_k_precision": p_base,
                "top_k_recall": r_base,
                "top_k_f1": f_base,
                "top_k_retrieved_count": count_base,
                "top_k_irrelevant_count": irrel_base,
                "adaptive_retrieved_ids": adapt_ids,
                "adaptive_precision": p_adapt,
                "adaptive_recall": r_adapt,
                "adaptive_f1": f_adapt,
                "adaptive_retrieved_count": count_adapt,
                "adaptive_irrelevant_count": irrel_adapt,
                "irrelevant_noise_reduction": noise_reduction
            })

        n = len(eval_queries)
        baseline_summary = {
            "mean_precision": round(float(np.mean(baseline_precisions)), 4) if n else 0.0,
            "mean_recall": round(float(np.mean(baseline_recalls)), 4) if n else 0.0,
            "mean_f1": round(float(np.mean(baseline_f1s)), 4) if n else 0.0,
            "total_retrieved": baseline_retrieved_total,
            "total_irrelevant": baseline_irrelevant_total,
            "avg_retrieved_per_query": round(baseline_retrieved_total / n, 2) if n else 0.0,
            "avg_irrelevant_per_query": round(baseline_irrelevant_total / n, 2) if n else 0.0
        }

        adaptive_summary = {
            "mean_precision": round(float(np.mean(adaptive_precisions)), 4) if n else 0.0,
            "mean_recall": round(float(np.mean(adaptive_recalls)), 4) if n else 0.0,
            "mean_f1": round(float(np.mean(adaptive_f1s)), 4) if n else 0.0,
            "total_retrieved": adaptive_retrieved_total,
            "total_irrelevant": adaptive_irrelevant_total,
            "avg_retrieved_per_query": round(adaptive_retrieved_total / n, 2) if n else 0.0,
            "avg_irrelevant_per_query": round(adaptive_irrelevant_total / n, 2) if n else 0.0
        }

        ord_results = [q for q in query_results if q["ground_truth_count"] > 0]
        nov_results = [q for q in query_results if q["ground_truth_count"] == 0]

        ordinary_summary = {
            "num_queries": len(ord_results),
            "baseline_mean_precision": round(float(np.mean([q["top_k_precision"] for q in ord_results])), 4) if ord_results else 0.0,
            "baseline_mean_recall": round(float(np.mean([q["top_k_recall"] for q in ord_results])), 4) if ord_results else 0.0,
            "baseline_mean_f1": round(float(np.mean([q["top_k_f1"] for q in ord_results])), 4) if ord_results else 0.0,
            "adaptive_mean_precision": round(float(np.mean([q["adaptive_precision"] for q in ord_results])), 4) if ord_results else 0.0,
            "adaptive_mean_recall": round(float(np.mean([q["adaptive_recall"] for q in ord_results])), 4) if ord_results else 0.0,
            "adaptive_mean_f1": round(float(np.mean([q["adaptive_f1"] for q in ord_results])), 4) if ord_results else 0.0,
        }

        novel_summary = {
            "num_queries": len(nov_results),
            "baseline_mean_precision": round(float(np.mean([q["top_k_precision"] for q in nov_results])), 4) if nov_results else 0.0,
            "baseline_mean_recall": round(float(np.mean([q["top_k_recall"] for q in nov_results])), 4) if nov_results else 0.0,
            "baseline_mean_f1": round(float(np.mean([q["top_k_f1"] for q in nov_results])), 4) if nov_results else 0.0,
            "adaptive_mean_precision": round(float(np.mean([q["adaptive_precision"] for q in nov_results])), 4) if nov_results else 0.0,
            "adaptive_mean_recall": round(float(np.mean([q["adaptive_recall"] for q in nov_results])), 4) if nov_results else 0.0,
            "adaptive_mean_f1": round(float(np.mean([q["adaptive_f1"] for q in nov_results])), 4) if nov_results else 0.0,
        }

        irrel_reduction_pct = 0.0
        if baseline_irrelevant_total > 0:
            irrel_reduction_pct = round(
                ((baseline_irrelevant_total - adaptive_irrelevant_total) / baseline_irrelevant_total) * 100,
                2
            )

        findings = (
            f"Evaluated {n} incident queries against identical historical cases (Corpus: {len(retrieval_engine.cases)} cases). "
            f"Adaptive retrieval (threshold={threshold}) achieved Mean Precision of {adaptive_summary['mean_precision']:.2%} "
            f"vs Baseline Top-K={top_k} of {baseline_summary['mean_precision']:.2%}. "
            f"On ordinary queries (n={len(ord_results)}), Precision improved from {ordinary_summary['baseline_mean_precision']:.2%} "
            f"to {ordinary_summary['adaptive_mean_precision']:.2%}. "
            f"Adaptive retrieval reduced irrelevant noise cases from {baseline_irrelevant_total} down to {adaptive_irrelevant_total} "
            f"({irrel_reduction_pct}% reduction in irrelevant case intrusion). "
            f"Mean F1 changed from {baseline_summary['mean_f1']:.2f} (baseline) to {adaptive_summary['mean_f1']:.2f} (adaptive)."
        )

        report = {
            "experiment_id": f"EXP-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "executed_at": datetime.utcnow().isoformat(),
            "active_corpus_cases": len(retrieval_engine.cases),
            "num_queries": n,
            "parameters": {
                "threshold": threshold,
                "top_k": top_k
            },
            "baseline_top_k": baseline_summary,
            "adaptive_threshold": adaptive_summary,
            "ordinary_queries_summary": ordinary_summary,
            "novel_queries_summary": novel_summary,
            "irrelevant_noise_reduction_pct": irrel_reduction_pct,
            "empty_ground_truth_convention": (
                "For queries with 0 ground-truth matches (novel incidents), retrieving 0 cases is assigned "
                "P=1.0, R=1.0, F1=1.0 (perfect noise elimination); retrieving >=1 case is assigned P=0.0, R=0.0, F1=0.0. "
                "To prevent empty-set conventions from masking ordinary retrieval quality, ordinary-query performance "
                "is independently tracked and reported."
            ),
            "threshold_calibration_disclosure": (
                "Threshold theta=0.55 was calibrated empirically on this 15-query evaluation dataset. "
                "Evaluating generalizability on a separate unseen corporate corpus is documented as future work."
            ),
            "query_breakdown": query_results,
            "summary_findings": findings
        }

        # Persist results in JSON
        results_file_json = settings.DATA_DIR / "last_experiment_results.json"
        try:
            with open(results_file_json, "w", encoding="utf-8") as rf:
                json.dump(report, rf, indent=2)
        except Exception:
            pass

        # Persist results in CSV (per-query breakdown & aggregate metadata)
        results_file_csv = settings.DATA_DIR / "last_experiment_results.csv"
        try:
            import csv
            with open(results_file_csv, "w", encoding="utf-8", newline="") as cf:
                writer = csv.writer(cf)
                writer.writerow([
                    "query_id", "service", "ground_truth_count", "ground_truth_ids",
                    "top_k_k", "top_k_retrieved_count", "top_k_precision", "top_k_recall", "top_k_f1", "top_k_irrelevant", "top_k_ids",
                    "adaptive_threshold", "adaptive_retrieved_count", "adaptive_precision", "adaptive_recall", "adaptive_f1", "adaptive_irrelevant", "adaptive_ids",
                    "irrelevant_noise_reduction"
                ])
                for q in query_results:
                    writer.writerow([
                        q["query_id"],
                        q["service"],
                        q["ground_truth_count"],
                        ";".join(q["ground_truth_ids"]),
                        top_k,
                        q["top_k_retrieved_count"],
                        q["top_k_precision"],
                        q["top_k_recall"],
                        q["top_k_f1"],
                        q["top_k_irrelevant_count"],
                        ";".join(q["top_k_retrieved_ids"]),
                        threshold,
                        q["adaptive_retrieved_count"],
                        q["adaptive_precision"],
                        q["adaptive_recall"],
                        q["adaptive_f1"],
                        q["adaptive_irrelevant_count"],
                        ";".join(q["adaptive_retrieved_ids"]),
                        q["irrelevant_noise_reduction"]
                    ])
                # Write summary aggregate row
                writer.writerow([])
                writer.writerow(["AGGREGATE_METRIC", "BASELINE_TOP_K", "ADAPTIVE_THRESHOLD", "DELTA_IMPROVEMENT"])
                writer.writerow(["mean_precision", baseline_summary["mean_precision"], adaptive_summary["mean_precision"], round(adaptive_summary["mean_precision"] - baseline_summary["mean_precision"], 4)])
                writer.writerow(["mean_recall", baseline_summary["mean_recall"], adaptive_summary["mean_recall"], round(adaptive_summary["mean_recall"] - baseline_summary["mean_recall"], 4)])
                writer.writerow(["mean_f1", baseline_summary["mean_f1"], adaptive_summary["mean_f1"], round(adaptive_summary["mean_f1"] - baseline_summary["mean_f1"], 4)])
                writer.writerow(["total_retrieved", baseline_summary["total_retrieved"], adaptive_summary["total_retrieved"], adaptive_summary["total_retrieved"] - baseline_summary["total_retrieved"]])
                writer.writerow(["total_irrelevant", baseline_summary["total_irrelevant"], adaptive_summary["total_irrelevant"], adaptive_summary["total_irrelevant"] - baseline_summary["total_irrelevant"]])
                writer.writerow(["noise_reduction_pct", "0.0%", f"{irrel_reduction_pct}%", f"-{irrel_reduction_pct}%"])
        except Exception:
            pass

        return report

experiment_runner = ExperimentRunner()
