import heapq
import numpy as np
import torch
import networkx as nx

class ReverseGenesisReconstruction:
    """
    Module 6: Optimized RGAR with Sub-Graph Extraction for Scalability.
    """
    def __init__(self, max_search_depth=5, k_hop=2):
        self.max_depth = max_search_depth
        self.k_hop = k_hop

    def _hash_adj(self, adj_np):
        return hash(adj_np.tobytes())

    def extract_subgraph_around_anomaly(self, full_adj, target_node):
        """Isolates k-hop neighborhood to restrict A* search space."""
        G = nx.from_numpy_array(full_adj)
        nodes = set([target_node])
        for _ in range(self.k_hop):
            neighbors = set()
            for n in nodes:
                neighbors.update(G.neighbors(n))
            nodes.update(neighbors)
        
        sub_nodes = sorted(list(nodes))
        sub_adj = full_adj[np.ix_(sub_nodes, sub_nodes)]
        return sub_adj, sub_nodes

    def reconstruct_attack_path(self, observed_anomalous_adj, baseline_adj, target_node=0):
        obs_full = observed_anomalous_adj.cpu().numpy().astype(int)
        base_full = baseline_adj.cpu().numpy().astype(int)

        # Extract localized sub-graphs for scalability
        obs_np, sub_nodes = self.extract_subgraph_around_anomaly(obs_full, target_node)
        base_np = base_full[np.ix_(sub_nodes, sub_nodes)]

        start_hash = self._hash_adj(obs_np)
        pq = [(0, 0, start_hash, obs_np, [])]
        visited = {start_hash}

        while pq:
            _, g_cost, _, curr_mat, path = heapq.heappop(pq)

            if np.array_equal(curr_mat, base_np) or len(path) >= self.max_depth:
                # Map local sub-graph edge indices back to global network IP indices
                global_path = [(sub_nodes[u], sub_nodes[v]) for u, v in path]
                return global_path

            active_edges = np.argwhere(curr_mat > 0)
            for u, v in active_edges:
                if u < v:
                    next_mat = curr_mat.copy()
                    next_mat[u, v] = 0
                    next_mat[v, u] = 0
                    h_val = self._hash_adj(next_mat)

                    if h_val not in visited:
                        visited.add(h_val)
                        heuristic = np.sum(np.abs(next_mat - base_np)) / 2.0
                        heapq.heappush(pq, (g_cost + 1 + heuristic, g_cost + 1, h_val, next_mat, path + [(u, v)]))

        return []

class CounterfactualGenesisBarrier:
    """
    Module 7: CGB with Betweenness Centrality Disruption Penalty.
    """
    def __init__(self, model, decoder):
        self.model = model
        self.decoder = decoder

    def compute_edge_disruption_cost(self, adj_tensor, u, v):
        """
        Calculates non-uniform intervention cost using Betweenness Centrality.
        Cutting core routing links penalizes the system higher than cutting endpoint links.
        """
        G = nx.from_numpy_array(adj_tensor.cpu().numpy())
        centrality = nx.edge_betweenness_centrality(G)
        edge = (min(u, v), max(u, v))
        return 1.0 + 5.0 * centrality.get(edge, 0.0)

    def find_minimal_intervention(self, target_snapshot, h_state):
        adj = target_snapshot['adj'].clone()
        x = target_snapshot['x']
        active_edges = torch.nonzero(torch.triu(adj, diagonal=1))

        candidates = []

        for edge in active_edges:
            u, v = edge[0].item(), edge[1].item()

            mod_adj = adj.clone()
            mod_adj[u, v] = 0.0
            mod_adj[v, u] = 0.0
            mod_edge_index = torch.nonzero(mod_adj).t()

            with torch.no_grad():
                node_emb, _ = self.model(x, mod_edge_index, h_state)
                # Predict edges
                pred_probs = torch.sigmoid(self.decoder(node_emb, mod_edge_index)).view(-1)
                
            residual_risk = torch.mean(torch.abs(1.0 - pred_probs)).item()
            disruption_cost = self.compute_edge_disruption_cost(adj, u, v)

            # Combined Objective: Minimize (Residual Risk + Disruption Cost)
            total_objective = residual_risk + 0.1 * disruption_cost

            candidates.append({
                'edge': (u, v),
                'cost': disruption_cost,
                'residual_risk': residual_risk,
                'objective': total_objective
            })

        candidates.sort(key=lambda item: item['objective'])
        return candidates[0] if candidates else None