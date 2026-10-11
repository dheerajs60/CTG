import numpy as np
import torch
import pytest
from detection.genesis_violation import compute_topology_metrics

def test_gv_true_positives():
    preds = np.array([1, 1])
    targets = np.array([1, 1])
    pos_edge = torch.tensor([[0, 1], [1, 2]])
    neg_edge = torch.tensor([[], []], dtype=torch.long)
    ev, deg_d, den_d, u_rt, m_rt = compute_topology_metrics(preds, targets, pos_edge, neg_edge, 3)
    assert ev == 0.0
    assert deg_d == 0.0
    assert den_d == 0.0
    assert u_rt == 0.0
    assert m_rt == 0.0

def test_gv_false_positives():
    preds = np.array([1, 1, 1]) # 3rd is FP
    targets = np.array([1, 1, 0])
    pos_edge = torch.tensor([[0, 1], [1, 2]])
    neg_edge = torch.tensor([[0], [2]]) # random neg edge
    ev, deg_d, den_d, u_rt, m_rt = compute_topology_metrics(preds, targets, pos_edge, neg_edge, 3)
    assert np.isclose(ev, 1/3)
    assert np.isclose(den_d, 1/3)
    assert np.isclose(u_rt, 1/2) # 1 FP / 2 actual
    assert m_rt == 0.0

def test_gv_duplicates_and_undirected():
    preds = np.array([1, 1, 1])
    targets = np.array([1, 1, 0])
    # pos_edges have (0,1) and (1,0) - same undirected edge!
    pos_edge = torch.tensor([[0, 1], [1, 0]])
    neg_edge = torch.tensor([[0], [1]]) # neg_edge is ALSO (0,1)!
    
    ev, deg_d, den_d, u_rt, m_rt = compute_topology_metrics(preds, targets, pos_edge, neg_edge, 3)
    assert np.isclose(ev, 1/3)
    assert den_d == 0.0
    assert u_rt == 1.0

