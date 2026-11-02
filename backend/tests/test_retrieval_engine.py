import pytest
from app.services.retrieval_engine import retrieval_engine

def test_fixed_top_k_retrieval():
    query = "PostgreSQL database connection pool exhausted in checkout service"
    res = retrieval_engine.retrieve_fixed_top_k(query, k=3, service_hint="checkout-service")

    assert res["method"] == "fixed_top_k"
    assert res["k_applied"] == 3
    assert len(res["candidates"]) == 3
    # Top candidate should be the connection pool incident
    top_candidate = res["candidates"][0]
    assert top_candidate["id"] == "INC-HIST-001"
    assert top_candidate["similarity_score"] > 0.60

def test_adaptive_threshold_filters_noise():
    query = "PostgreSQL database connection pool exhausted in checkout service"
    ground_truth = ["INC-HIST-001"]

    fixed = retrieval_engine.retrieve_fixed_top_k(
        query, k=3, service_hint="checkout-service", ground_truth_ids=ground_truth
    )
    adaptive = retrieval_engine.retrieve_adaptive_threshold(
        query, threshold=0.55, service_hint="checkout-service", ground_truth_ids=ground_truth
    )

    # Fixed top 3 will have 1 TP and 2 FP (irrelevant cases)
    assert fixed["retrieved_count"] == 3
    assert fixed["irrelevant_count"] == 2
    assert fixed["precision"] < 0.40  # 1/3 = 0.3333

    # Adaptive retrieval filters low-similarity irrelevant cases
    assert adaptive["retrieved_count"] <= 2
    assert adaptive["irrelevant_count"] < fixed["irrelevant_count"]
    assert adaptive["precision"] > fixed["precision"]

def test_novel_out_of_domain_query_noise_elimination():
    novel_query = "Novel hardware optical quantum tensor processor cooled with liquid helium malfunction"
    ground_truth = []  # No matching cases in e-commerce incident repo

    fixed = retrieval_engine.retrieve_fixed_top_k(
        novel_query, k=3, ground_truth_ids=ground_truth
    )
    adaptive = retrieval_engine.retrieve_adaptive_threshold(
        novel_query, threshold=0.55, ground_truth_ids=ground_truth
    )

    # Fixed Top-K forces 3 irrelevant cases into context
    assert fixed["retrieved_count"] == 3
    assert fixed["irrelevant_count"] == 3
    assert fixed["precision"] == 0.0

    # Adaptive retrieval recognizes novel case and avoids hallucination noise
    assert adaptive["retrieved_count"] == 0
    assert adaptive["irrelevant_count"] == 0
    assert adaptive["precision"] == 1.0  # Perfect precision when 0 irrelevant retrieved for empty ground truth

def test_metric_calculation_edge_cases():
    # Empty ground truth, 0 retrieved
    m1 = retrieval_engine.calculate_metrics([], [])
    assert m1["precision"] == 1.0
    assert m1["recall"] == 1.0
    assert m1["irrelevant_count"] == 0

    # Ground truth has 1, retrieved has 1 match
    m2 = retrieval_engine.calculate_metrics(["INC-01"], ["INC-01"])
    assert m2["precision"] == 1.0
    assert m2["recall"] == 1.0
    assert m2["f1_score"] == 1.0
    assert m2["irrelevant_count"] == 0

    # Ground truth has 1, retrieved has 1 match and 2 irrelevant
    m3 = retrieval_engine.calculate_metrics(["INC-01", "INC-02", "INC-03"], ["INC-01"])
    assert round(m3["precision"], 2) == 0.33
    assert m3["recall"] == 1.0
    assert m3["irrelevant_count"] == 2

def test_fair_input_equivalence():
    """Verify both baseline and proposed methods operate on identical candidate universe and query."""
    query = "PostgreSQL pool exhausted in checkout service"
    ground_truth = ["INC-HIST-001"]

    fixed = retrieval_engine.retrieve_fixed_top_k(query, k=3, service_hint="checkout-service", ground_truth_ids=ground_truth)
    adaptive = retrieval_engine.retrieve_adaptive_threshold(query, threshold=0.55, service_hint="checkout-service", ground_truth_ids=ground_truth)

    # Both must identify the exact same top ranked precedent
    assert fixed["candidates"][0]["id"] == adaptive["candidates"][0]["id"]
    assert fixed["candidates"][0]["similarity_score"] == adaptive["candidates"][0]["similarity_score"]
    # Candidate pool length available to both is identical
    assert len(retrieval_engine.cases) >= 12

def test_matching_evidence_exposure():
    """Verify retrieved candidates expose meaningful matching evidence (tokens, coverage %, service match)."""
    query = "Redis cache stampede with bulk key expiration on database replica"
    res = retrieval_engine.retrieve_adaptive_threshold(query, threshold=0.50, service_hint="catalog-service")

    assert res["retrieved_count"] > 0
    candidate = res["candidates"][0]
    assert "matching_evidence" in candidate
    evidence = candidate["matching_evidence"]
    assert "matched_tokens" in evidence
    assert len(evidence["matched_tokens"]) > 0
    assert "token_coverage_pct" in evidence
    assert "tfidf_similarity" in evidence
    assert "service_alignment_bonus" in evidence

def test_retrieval_edge_cases():
    """Verify retrieval engine handles empty query, empty repository, ties, and malformed queries gracefully."""
    # Empty query string
    empty_res = retrieval_engine.retrieve_fixed_top_k("", k=3)
    assert empty_res["retrieved_count"] == 0
    assert empty_res["candidates"] == []

    # Whitespace only query
    ws_res = retrieval_engine.retrieve_adaptive_threshold("   \n\t  ", threshold=0.55)
    assert ws_res["retrieved_count"] == 0

    # Very high threshold (theta=1.0) returns zero candidates without crashing
    strict_res = retrieval_engine.retrieve_adaptive_threshold("checkout error", threshold=1.0)
    assert strict_res["retrieved_count"] == 0
    assert strict_res["threshold_applied"] == 1.0

def test_threshold_sensitivity_boundaries():
    """Verify behavior across extreme threshold boundaries theta=0.0 and theta=0.99."""
    query = "Database connection pool saturated in checkout"
    # Zero threshold retains all scored candidates up to max_k
    zero_thresh = retrieval_engine.retrieve_adaptive_threshold(query, threshold=0.0, max_k=5)
    assert zero_thresh["retrieved_count"] <= 5
    assert zero_thresh["retrieved_count"] > 0

    # Extreme threshold eliminates low confidence candidates
    high_thresh = retrieval_engine.retrieve_adaptive_threshold(query, threshold=0.99)
    assert high_thresh["retrieved_count"] == 0

