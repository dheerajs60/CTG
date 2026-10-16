"""
Unit Tests for Phase 1 Baselines and Candidate Sampling Module.
Tests:
- Candidate disjointness
- Temporal leakage prevention
- No duplicate candidates or negative padding
- Unseen node stratification
- Empty snapshot handling
- Directed vs undirected edge handling
- PRNG seed reproducibility
- Baseline state updates and scoring
- Ranking metrics eligibility enforcement
"""

import pytest
import numpy as np
from src.evaluation.candidate_sampler import (
    stratify_edges,
    sample_hard_historical_negatives,
    sample_mixed_negatives,
    create_evaluation_dataset
)
from models.baselines import (
    PersistenceBaseline,
    EdgeBankUnlimited,
    EdgeBankTimeWindow,
    CommonNeighborsBaseline,
    JaccardBaseline,
    AdamicAdarBaseline
)
from src.evaluation.metrics import (
    compute_classification_metrics,
    compute_ranking_metrics
)


def test_unseen_node_stratification():
    # G_curr has nodes {A, B, C} and edges {(A, B), (B, C)}
    G_curr = {("A", "B"), ("B", "C")}
    # G_next has:
    # ("A", "B"): recurring
    # ("A", "C"): new between known nodes
    # ("A", "D"): involves unseen node D
    G_next = {("A", "B"), ("A", "C"), ("A", "D")}
    
    strat = stratify_edges(G_curr, G_next)
    
    assert strat["recurring"] == {("A", "B")}
    assert strat["new_between_known"] == {("A", "C")}
    assert strat["unseen_nodes"] == {("A", "D")}


def test_candidate_disjointness_and_no_duplicates():
    pos = [("A", "B"), ("B", "C")]
    neg = [("C", "A"), ("B", "A")]
    
    cands, labels = create_evaluation_dataset(pos, neg, seed=42)
    
    assert len(cands) == 4
    assert len(labels) == 4
    assert set(pos).isdisjoint(set(neg))
    assert len(cands) == len(set(cands))
    
    # Overlapping sets must fail
    with pytest.raises(ValueError, match="appear in both positive and negative sets"):
        create_evaluation_dataset([("A", "B")], [("A", "B")], seed=42)
        
    # Duplicates in pos must fail
    with pytest.raises(ValueError, match="duplicate positive edges"):
        create_evaluation_dataset([("A", "B"), ("A", "B")], [("C", "D")], seed=42)


def test_no_negative_padding_or_silent_duplication():
    # Only 1 hard negative available
    hist_edges = {("A", "B"), ("B", "C")}
    target_edges = {("A", "B")} # ("B", "C") is the only absent historical edge
    
    # Requesting 1 should succeed
    neg = sample_hard_historical_negatives(hist_edges, target_edges, num_negatives=1, seed=42)
    assert neg == [("B", "C")]
    
    # Requesting 2 when only 1 is available must raise ValueError, NEVER duplicate
    with pytest.raises(ValueError, match="Insufficient unique hard historical negatives"):
        sample_hard_historical_negatives(hist_edges, target_edges, num_negatives=2, seed=42)


def test_temporal_leakage_prevention():
    hist_edges = {("A", "B"), ("B", "C"), ("C", "D")}
    target_edges = {("A", "B"), ("X", "Y")} # ("X", "Y") is future
    
    negs = sample_hard_historical_negatives(hist_edges, target_edges, num_negatives=2, seed=100)
    
    # Every sampled negative must be drawn strictly from historical edges
    for u, v in negs:
        assert (u, v) in hist_edges
        assert (u, v) not in target_edges


def test_empty_snapshot_handling():
    # Empty snapshot
    strat = stratify_edges(set(), set())
    assert len(strat["recurring"]) == 0
    assert len(strat["new_between_known"]) == 0
    assert len(strat["unseen_nodes"]) == 0
    
    pers = PersistenceBaseline()
    pers.update(set())
    scores = pers.predict_scores([("A", "B")])
    assert scores[0] == 0.0


def test_directed_vs_undirected_heuristics():
    # Graph has directed edge A -> B and B -> C
    edges = {("A", "B"), ("B", "C")}
    
    # In directed CN: path is A -> B -> C, so A and C have common intermediary B
    # Candidate (A, C): out(A)={B}, in(C)={B} -> intersection {B} -> score = 1
    # Candidate (C, A): out(C)={}, in(A)={} -> intersection {} -> score = 0
    cn_dir = CommonNeighborsBaseline(directed=True)
    cn_dir.update(edges)
    scores = cn_dir.predict_scores([("A", "C"), ("C", "A")])
    assert scores[0] == 1.0
    assert scores[1] == 0.0
    
    # In undirected CN: both (A, C) and (C, A) have common neighbor B
    cn_undir = CommonNeighborsBaseline(directed=False)
    cn_undir.update(edges)
    scores_undir = cn_undir.predict_scores([("A", "C"), ("C", "A")])
    assert scores_undir[0] == 1.0
    assert scores_undir[1] == 1.0


def test_reproducibility_with_seed():
    nodes = [f"N{i}" for i in range(50)]
    target = {("N0", "N1")}
    hist = {("N0", "N1"), ("N1", "N2"), ("N2", "N3"), ("N3", "N4"), ("N4", "N5")}
    
    # Setting B (Mixed Random Negatives)
    run1 = sample_mixed_negatives(nodes, target, num_negatives=10, seed=1234)
    run2 = sample_mixed_negatives(nodes, target, num_negatives=10, seed=1234)
    run3 = sample_mixed_negatives(nodes, target, num_negatives=10, seed=5678)
    assert run1 == run2, "Sampling with identical seed must be deterministic and bit-exact!"
    assert run1 != run3, "Sampling with different seeds should produce different orders/samples."
    
    # Setting A (Hard Historical Negatives)
    h_run1 = sample_hard_historical_negatives(hist, target, num_negatives=3, seed=1234)
    h_run2 = sample_hard_historical_negatives(hist, target, num_negatives=3, seed=1234)
    h_run3 = sample_hard_historical_negatives(hist, target, num_negatives=3, seed=5678)
    assert h_run1 == h_run2, "Setting A sampling with identical seed must be deterministic!"
    assert h_run1 != h_run3, "Setting A sampling with different seeds should produce different samples."


def test_edgebank_memory_evolution():
    t0_edges = {("A", "B")}
    t1_edges = {("B", "C")}
    t2_edges = {("C", "D")}
    
    # EdgeBank-∞ remembers everything
    eb_inf = EdgeBankUnlimited(mode="binary")
    eb_inf.update(t0_edges)
    eb_inf.update(t1_edges)
    eb_inf.update(t2_edges)
    
    scores = eb_inf.predict_scores([("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")])
    assert scores.tolist() == [1.0, 1.0, 1.0, 0.0]
    
    # EdgeBank-tw with W=2 should forget t0
    eb_tw = EdgeBankTimeWindow(window_size=2, mode="binary")
    eb_tw.update(t0_edges)
    eb_tw.update(t1_edges)
    eb_tw.update(t2_edges) # window now has t1 and t2 only
    
    scores_tw = eb_tw.predict_scores([("A", "B"), ("B", "C"), ("C", "D")])
    assert scores_tw.tolist() == [0.0, 1.0, 1.0] # ("A", "B") was evicted


def test_ranking_eligibility_enforcement():
    y_true = [1, 0, 1, 0]
    binary_scores = np.array([1.0, 0.0, 1.0, 0.0])
    
    # Persistence is not ranking eligible
    pers_rank = compute_ranking_metrics(y_true, binary_scores, is_ranking_eligible=False)
    assert "NOT EVALUABLE" in str(pers_rank["roc_auc"])
    assert "NOT EVALUABLE" in str(pers_rank["mrr"])
    
    # Continuous scorer is ranking eligible
    cont_scores = np.array([0.9, 0.2, 0.8, 0.1])
    cont_rank = compute_ranking_metrics(y_true, cont_scores, is_ranking_eligible=True)
    assert isinstance(cont_rank["roc_auc"], float)
    assert cont_rank["roc_auc"] == 1.0
    assert cont_rank["mrr"] > 0.0


def test_process_hash_seed_invariance():
    """Verify that candidate generation produces identical candidates across different PYTHONHASHSEEDs."""
    import subprocess
    import sys
    
    code = """
import json, hashlib
from src.evaluation.candidate_sampler import sample_hard_historical_negatives, sample_mixed_negatives, create_evaluation_dataset

hist = {("192.168.1." + str(i), "10.0.0." + str(j)) for i in range(25) for j in range(25)}
target = {("192.168.1." + str(i), "10.0.0." + str(i)) for i in range(25)}
nodes = [f"node_{i}" for i in range(120)]

hard = sample_hard_historical_negatives(hist, target, num_negatives=40, seed=42)
mixed = sample_mixed_negatives(nodes, target, num_negatives=40, seed=42)
cands, labels = create_evaluation_dataset(sorted(list(target))[:20], hard[:20], seed=100)

h = hashlib.sha256(json.dumps([hard, mixed, cands, labels]).encode()).hexdigest()
print(h)
"""
    hashes = []
    for h_seed in ["0", "42", "999", "12345"]:
        out = subprocess.check_output(
            [sys.executable, "-c", code],
            env={"PYTHONHASHSEED": h_seed, "PATH": subprocess.os.environ.get("PATH", "")}
        ).decode().strip()
        hashes.append(out)
        
    assert len(set(hashes)) == 1, f"Candidate generation varied across PYTHONHASHSEEDs: {hashes}"


def test_same_candidates_shared_across_models():
    """Verify that all models within one evaluation step evaluate on the identical candidate list and labels for both Setting A and Setting B."""
    pos = [("A", "B"), ("B", "C"), ("C", "D")]
    hist = {("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"), ("E", "F")}
    target = {("A", "B"), ("B", "C"), ("C", "D")}
    nodes = ["A", "B", "C", "D", "E", "F"]
    
    # Setting A: Hard Historical Negatives
    neg_hard = sample_hard_historical_negatives(hist, target, num_negatives=2, seed=42)
    cands_a, labels_a = create_evaluation_dataset(pos[:2], neg_hard, seed=142)
    
    # Setting B: Mixed Random Negatives
    neg_mixed = sample_mixed_negatives(nodes, target, num_negatives=2, seed=42)
    cands_b, labels_b = create_evaluation_dataset(pos[:2], neg_mixed, seed=142)
    
    # Instantiate models
    p = PersistenceBaseline()
    p.update(target)
    eb = EdgeBankUnlimited(mode="binary")
    eb.update(hist)
    cn = CommonNeighborsBaseline(directed=True)
    cn.update(target)
    
    # Setting A candidate consistency across models
    p_scores_a = p.predict_scores(cands_a)
    eb_scores_a = eb.predict_scores(cands_a)
    cn_scores_a = cn.predict_scores(cands_a)
    assert len(p_scores_a) == len(cands_a) == len(labels_a)
    assert len(eb_scores_a) == len(cands_a) == len(labels_a)
    assert len(cn_scores_a) == len(cands_a) == len(labels_a)
    
    # Setting B candidate consistency across models
    p_scores_b = p.predict_scores(cands_b)
    eb_scores_b = eb.predict_scores(cands_b)
    cn_scores_b = cn.predict_scores(cands_b)
    assert len(p_scores_b) == len(cands_b) == len(labels_b)
    assert len(eb_scores_b) == len(cands_b) == len(labels_b)
    assert len(cn_scores_b) == len(cands_b) == len(labels_b)


def test_seed_reproducibility_and_cross_seed_variation():
    """Verify individual seed determinism and cross-seed variation for both Setting A and Setting B."""
    nodes = [f"node_{i}" for i in range(80)]
    target = {("node_0", "node_1")}
    hist = {("node_0", "node_1"), ("node_1", "node_2"), ("node_2", "node_3"), ("node_3", "node_4"), ("node_4", "node_5"), ("node_5", "node_6")}
    
    # Setting B: Mixed Negatives
    s42_run1 = sample_mixed_negatives(nodes, target, num_negatives=15, seed=42)
    s42_run2 = sample_mixed_negatives(nodes, target, num_negatives=15, seed=42)
    assert s42_run1 == s42_run2
    
    s100_run1 = sample_mixed_negatives(nodes, target, num_negatives=15, seed=100)
    s100_run2 = sample_mixed_negatives(nodes, target, num_negatives=15, seed=100)
    assert s100_run1 == s100_run2
    assert s42_run1 != s100_run1
    
    # Setting A: Hard Historical Negatives
    s42_hard1 = sample_hard_historical_negatives(hist, target, num_negatives=3, seed=42)
    s42_hard2 = sample_hard_historical_negatives(hist, target, num_negatives=3, seed=42)
    assert s42_hard1 == s42_hard2
    
    s100_hard1 = sample_hard_historical_negatives(hist, target, num_negatives=3, seed=100)
    s100_hard2 = sample_hard_historical_negatives(hist, target, num_negatives=3, seed=100)
    assert s100_hard1 == s100_hard2
    assert s42_hard1 != s100_hard1


