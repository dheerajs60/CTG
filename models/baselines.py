"""
Temporal and Topological Link Prediction Baselines.
Includes:
- Persistence Baseline
- EdgeBank-∞ (Unlimited Memory)
- EdgeBank-tw (Time-Windowed Memory)
- Common Neighbors (CN)
- Jaccard Coefficient (JC)
- Adamic-Adar (AA)

Each baseline adheres to a unified interface:
- update(snapshot_edges, timestamp=None)
- predict_scores(candidate_edges) -> np.ndarray
- predict_binary(candidate_edges, threshold=0.5) -> np.ndarray
"""

import math
from collections import defaultdict, deque
from typing import Set, Tuple, List, Dict, Optional, Union, Any
import numpy as np


class BaseLinkPredictor:
    """Base class for link prediction baselines."""
    def __init__(self, name: str, is_ranking_eligible: bool):
        self.name = name
        self.is_ranking_eligible = is_ranking_eligible

    def update(self, edges: Set[Tuple[str, str]], timestamp: Optional[Any] = None):
        raise NotImplementedError

    def predict_scores(self, candidate_edges: List[Tuple[str, str]]) -> np.ndarray:
        raise NotImplementedError

    def predict_binary(self, candidate_edges: List[Tuple[str, str]], threshold: float = 0.5) -> np.ndarray:
        scores = self.predict_scores(candidate_edges)
        return (scores >= threshold).astype(int)


class PersistenceBaseline(BaseLinkPredictor):
    """
    Persistence Baseline:
    Predicts an edge exists at t+1 if and only if it existed in the immediately preceding snapshot t.
    Output is discrete binary {0.0, 1.0}. Not eligible for continuous ranking metrics.
    """
    def __init__(self):
        super().__init__(name="Persistence", is_ranking_eligible=False)
        self.prev_edges: Set[Tuple[str, str]] = set()

    def update(self, edges: Set[Tuple[str, str]], timestamp: Optional[Any] = None):
        self.prev_edges = set(edges)

    def predict_scores(self, candidate_edges: List[Tuple[str, str]]) -> np.ndarray:
        scores = np.zeros(len(candidate_edges), dtype=np.float32)
        for i, edge in enumerate(candidate_edges):
            if edge in self.prev_edges:
                scores[i] = 1.0
        return scores


class EdgeBankUnlimited(BaseLinkPredictor):
    """
    EdgeBank-∞ (Poursafaei et al., NeurIPS 2022):
    Maintains an unbounded memory of all directed edges observed since the start of telemetry.
    Can operate in:
    - 'binary' mode: score = 1.0 if in memory, else 0.0 (ranking ineligible)
    - 'frequency' mode: score = occurrence count / total snapshots observed (ranking eligible)
    """
    def __init__(self, mode: str = "binary"):
        is_ranking = (mode == "frequency")
        super().__init__(name=f"EdgeBank-∞ ({mode})", is_ranking_eligible=is_ranking)
        self.mode = mode
        self.edge_counts: Dict[Tuple[str, str], int] = defaultdict(int)
        self.total_snapshots = 0

    def update(self, edges: Set[Tuple[str, str]], timestamp: Optional[Any] = None):
        self.total_snapshots += 1
        for e in edges:
            self.edge_counts[e] += 1

    def predict_scores(self, candidate_edges: List[Tuple[str, str]]) -> np.ndarray:
        scores = np.zeros(len(candidate_edges), dtype=np.float32)
        if self.total_snapshots == 0:
            return scores

        for i, edge in enumerate(candidate_edges):
            cnt = self.edge_counts.get(edge, 0)
            if self.mode == "binary":
                scores[i] = 1.0 if cnt > 0 else 0.0
            else:
                scores[i] = float(cnt) / float(self.total_snapshots)
        return scores


class EdgeBankTimeWindow(BaseLinkPredictor):
    """
    EdgeBank-tw (Time-Windowed Memory):
    Maintains a sliding window of the last W snapshots:
    M_t = Union_{tau = t - W + 1}^t E_tau
    """
    def __init__(self, window_size: int = 3, mode: str = "binary"):
        is_ranking = (mode == "frequency")
        super().__init__(name=f"EdgeBank-tw(W={window_size}, {mode})", is_ranking_eligible=is_ranking)
        self.window_size = window_size
        self.mode = mode
        self.window_history: deque = deque(maxlen=window_size)
        self.edge_counts: Dict[Tuple[str, str], int] = defaultdict(int)

    def update(self, edges: Set[Tuple[str, str]], timestamp: Optional[Any] = None):
        # If queue is full, evict oldest
        if len(self.window_history) == self.window_size:
            oldest_edges = self.window_history[0]
            for e in oldest_edges:
                self.edge_counts[e] -= 1
                if self.edge_counts[e] <= 0:
                    del self.edge_counts[e]
                    
        self.window_history.append(set(edges))
        for e in edges:
            self.edge_counts[e] += 1

    def predict_scores(self, candidate_edges: List[Tuple[str, str]]) -> np.ndarray:
        scores = np.zeros(len(candidate_edges), dtype=np.float32)
        w_len = len(self.window_history)
        if w_len == 0:
            return scores

        for i, edge in enumerate(candidate_edges):
            cnt = self.edge_counts.get(edge, 0)
            if self.mode == "binary":
                scores[i] = 1.0 if cnt > 0 else 0.0
            else:
                scores[i] = float(cnt) / float(w_len)
        return scores


class HeuristicGraphState:
    """Helper structure maintaining current graph adjacency for heuristic scoring."""
    def __init__(self, directed: bool = True):
        self.directed = directed
        self.out_adj: Dict[str, Set[str]] = defaultdict(set)
        self.in_adj: Dict[str, Set[str]] = defaultdict(set)
        self.all_adj: Dict[str, Set[str]] = defaultdict(set)

    def update(self, edges: Set[Tuple[str, str]]):
        self.out_adj.clear()
        self.in_adj.clear()
        self.all_adj.clear()
        for u, v in edges:
            self.out_adj[u].add(v)
            self.in_adj[v].add(u)
            self.all_adj[u].add(v)
            self.all_adj[v].add(u)


class CommonNeighborsBaseline(BaseLinkPredictor):
    """
    Common Neighbors (CN):
    For directed graph (u -> v): overlap between out-neighbors of u and in-neighbors of v:
    score = |N_out(u) ∩ N_in(v)|
    Or for undirected neighbor representation: |N(u) ∩ N(v)|.
    Produces continuous non-negative integer scores eligible for ranking.
    """
    def __init__(self, directed: bool = True):
        mode_str = "directed" if directed else "undirected"
        super().__init__(name=f"Common Neighbors ({mode_str})", is_ranking_eligible=True)
        self.directed = directed
        self.graph_state = HeuristicGraphState(directed=directed)

    def update(self, edges: Set[Tuple[str, str]], timestamp: Optional[Any] = None):
        self.graph_state.update(edges)

    def predict_scores(self, candidate_edges: List[Tuple[str, str]]) -> np.ndarray:
        scores = np.zeros(len(candidate_edges), dtype=np.float32)
        for i, (u, v) in enumerate(candidate_edges):
            if self.directed:
                # Intermediary nodes z where u -> z and z -> v
                common = self.graph_state.out_adj[u].intersection(self.graph_state.in_adj[v])
            else:
                common = self.graph_state.all_adj[u].intersection(self.graph_state.all_adj[v])
            scores[i] = float(len(common))
        return scores


class JaccardBaseline(BaseLinkPredictor):
    """
    Jaccard Coefficient (JC):
    score = |N(u) ∩ N(v)| / |N(u) ∪ N(v)|
    Produces continuous scores in [0.0, 1.0].
    """
    def __init__(self, directed: bool = False):
        mode_str = "directed" if directed else "undirected"
        super().__init__(name=f"Jaccard Coefficient ({mode_str})", is_ranking_eligible=True)
        self.directed = directed
        self.graph_state = HeuristicGraphState(directed=directed)

    def update(self, edges: Set[Tuple[str, str]], timestamp: Optional[Any] = None):
        self.graph_state.update(edges)

    def predict_scores(self, candidate_edges: List[Tuple[str, str]]) -> np.ndarray:
        scores = np.zeros(len(candidate_edges), dtype=np.float32)
        for i, (u, v) in enumerate(candidate_edges):
            if self.directed:
                set_u = self.graph_state.out_adj[u]
                set_v = self.graph_state.in_adj[v]
            else:
                set_u = self.graph_state.all_adj[u]
                set_v = self.graph_state.all_adj[v]
                
            intersection_len = len(set_u.intersection(set_v))
            if intersection_len == 0:
                scores[i] = 0.0
            else:
                union_len = len(set_u.union(set_v))
                scores[i] = float(intersection_len) / float(union_len) if union_len > 0 else 0.0
        return scores


class AdamicAdarBaseline(BaseLinkPredictor):
    """
    Adamic-Adar Index (AA):
    score = sum_{z in N(u) ∩ N(v)} 1 / log(|N(z)|)
    Produces continuous non-negative scores.
    """
    def __init__(self, directed: bool = False):
        mode_str = "directed" if directed else "undirected"
        super().__init__(name=f"Adamic-Adar ({mode_str})", is_ranking_eligible=True)
        self.directed = directed
        self.graph_state = HeuristicGraphState(directed=directed)

    def update(self, edges: Set[Tuple[str, str]], timestamp: Optional[Any] = None):
        self.graph_state.update(edges)

    def predict_scores(self, candidate_edges: List[Tuple[str, str]]) -> np.ndarray:
        scores = np.zeros(len(candidate_edges), dtype=np.float32)
        for i, (u, v) in enumerate(candidate_edges):
            if self.directed:
                common = self.graph_state.out_adj[u].intersection(self.graph_state.in_adj[v])
            else:
                common = self.graph_state.all_adj[u].intersection(self.graph_state.all_adj[v])
                
            score = 0.0
            for z in common:
                deg = len(self.graph_state.all_adj[z])
                if deg > 1:
                    score += 1.0 / math.log(deg)
            scores[i] = float(score)
        return scores
