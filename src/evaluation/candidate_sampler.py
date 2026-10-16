"""
Candidate Sampling and Edge Stratification Module for Temporal Link Prediction.
Enforces strict anti-leakage constraints, explicit stratification, and hard-negative sampling.
"""

import random
import numpy as np
from typing import Set, Tuple, List, Dict, Any, Optional

def stratify_edges(
    G_curr_edges: Set[Tuple[str, str]],
    G_next_edges: Set[Tuple[str, str]],
    historical_nodes: Optional[Set[str]] = None
) -> Dict[str, Set[Tuple[str, str]]]:
    """
    Stratifies positive edges in G_next into three disjoint categories:
    1. recurring: present in both G_curr and G_next (e in G_curr and e in G_next)
    2. new_between_known: in G_next, not in G_curr, but both endpoints are known (observed in historical_nodes or G_curr)
    3. unseen_nodes: in G_next, where at least one endpoint was never observed before G_next
    """
    if historical_nodes is None:
        known_nodes = set()
        for u, v in G_curr_edges:
            known_nodes.add(u)
            known_nodes.add(v)
    else:
        known_nodes = set(historical_nodes)
        for u, v in G_curr_edges:
            known_nodes.add(u)
            known_nodes.add(v)
            
    recurring = set()
    new_between_known = set()
    unseen_nodes = set()
    
    for u, v in G_next_edges:
        if (u, v) in G_curr_edges:
            recurring.add((u, v))
        elif u in known_nodes and v in known_nodes:
            new_between_known.add((u, v))
        else:
            unseen_nodes.add((u, v))
            
    return {
        "recurring": recurring,
        "new_between_known": new_between_known,
        "unseen_nodes": unseen_nodes
    }

def sample_hard_historical_negatives(
    historical_edges: Set[Tuple[str, str]],
    target_edges: Set[Tuple[str, str]],
    num_negatives: int,
    seed: int
) -> List[Tuple[str, str]]:
    """
    Setting A: Samples directed edges that were observed in historical telemetry
    prior to target snapshot, but are absent in target_edges.
    
    Raises ValueError if available unique hard negatives are fewer than requested.
    NEVER pads or duplicates.
    """
    rng = random.Random(seed)
    
    # Pool = historical edges absent at target
    # Stably sort to eliminate Python hash randomization across independent processes
    candidate_pool = sorted(list(historical_edges - target_edges))
    
    if len(candidate_pool) < num_negatives:
        raise ValueError(
            f"Insufficient unique hard historical negatives: requested {num_negatives}, "
            f"but only {len(candidate_pool)} unique inactive historical edges are available. "
            f"Silent padding is strictly forbidden."
        )
        
    rng.shuffle(candidate_pool)
    return candidate_pool[:num_negatives]

def sample_mixed_negatives(
    known_nodes: List[str],
    target_edges: Set[Tuple[str, str]],
    num_negatives: int,
    seed: int,
    max_attempts_factor: int = 20
) -> List[Tuple[str, str]]:
    """
    Setting B: Samples non-edges (u, v) uniformly without replacement from known_nodes x known_nodes.
    Ensures:
    1. (u, v) is not in target_edges.
    2. u != v (no self-loops).
    3. No duplicate negatives.
    
    Raises ValueError if requested count cannot be sampled without duplication.
    """
    # Stably sort known_nodes to ensure deterministic indexing across processes
    nodes = sorted(list(known_nodes))
    if len(nodes) < 2:
        raise ValueError(f"Cannot sample negatives: known_nodes has fewer than 2 nodes ({len(nodes)}).")
        
    rng = random.Random(seed)
    n = len(nodes)
    
    neg_set = set()
    attempts = 0
    max_attempts = num_negatives * max_attempts_factor
    
    while len(neg_set) < num_negatives and attempts < max_attempts:
        attempts += 1
        u_idx = rng.randint(0, n - 1)
        v_idx = rng.randint(0, n - 1)
        if u_idx == v_idx:
            continue
            
        u = nodes[u_idx]
        v = nodes[v_idx]
        edge = (u, v)
        
        if edge not in target_edges and edge not in neg_set:
            neg_set.add(edge)
            
    if len(neg_set) < num_negatives:
        raise ValueError(
            f"Could not sample {num_negatives} unique mixed negatives after {attempts} attempts "
            f"(only {len(neg_set)} unique sampled). Target graph may be too dense or node set too small. "
            f"Duplication or padding is strictly forbidden."
        )
        
    # Stably sort sampled negatives before final deterministic shuffle
    neg_list = sorted(list(neg_set))
    rng.shuffle(neg_list)
    return neg_list

def create_evaluation_dataset(
    pos_edges: List[Tuple[str, str]],
    neg_edges: List[Tuple[str, str]],
    seed: int
) -> Tuple[List[Tuple[str, str]], List[int]]:
    """
    Combines positive and negative edge lists into a shuffled candidate list and label vector.
    Validates disjointness and absence of duplicate candidates.
    """
    pos_set = set(pos_edges)
    neg_set = set(neg_edges)
    
    # Strict validation checks
    overlap = pos_set.intersection(neg_set)
    if len(overlap) > 0:
        raise ValueError(f"Candidate dataset error: {len(overlap)} edges appear in both positive and negative sets!")
        
    if len(pos_set) != len(pos_edges):
        raise ValueError("Candidate dataset error: duplicate positive edges detected!")
        
    if len(neg_set) != len(neg_edges):
        raise ValueError("Candidate dataset error: duplicate negative edges detected!")
        
    candidates = pos_edges + neg_edges
    labels = [1] * len(pos_edges) + [0] * len(neg_edges)
    
    # Joint deterministic shuffle
    paired = list(zip(candidates, labels))
    rng = random.Random(seed)
    rng.shuffle(paired)
    
    shuffled_candidates, shuffled_labels = zip(*paired)
    return list(shuffled_candidates), list(shuffled_labels)
