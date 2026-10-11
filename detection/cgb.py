import copy
import networkx as nx
import torch

class CounterfactualGenesisBarrier:
    """
    Module 7: Counterfactual Genesis Barrier (CGB).
    Optimizes intervention cost vs prevention.
    """
    def __init__(self, lambda_collateral=1.0, mu_residual=1.0):
        self.lambda_collateral = lambda_collateral
        self.mu_residual = mu_residual
        
    def find_minimal_intervention(self, anomalous_snapshot, h_state=None):
        """
        Finds a graph edit that prevents the target attack trajectory with minimal cost.
        J(Delta G) = intervention_cost + lambda * collateral_damage + mu * residual_risk
        """
        edges = set(tuple(e) for e in anomalous_snapshot['edge_index'].t().tolist())
        num_nodes = anomalous_snapshot['nodes']
        
        G = nx.Graph()
        G.add_nodes_from(range(num_nodes))
        G.add_edges_from(list(edges))
        
        if len(edges) == 0:
            return None
            
        best_intervention = None
        min_cost = float('inf')
        
        # Candidate generation (greedy edge removal)
        # In a full implementation, this uses edge betweenness or a learned policy.
        # Here we simulate evaluating candidate cuts.
        
        for candidate_edge in list(edges)[:5]: # Limit to 5 candidates for simulation speed
            cost = 1.0 # Base intervention cost
            
            # Simulate collateral damage (e.g. disconnected components)
            G_temp = G.copy()
            G_temp.remove_edge(*candidate_edge)
            
            collateral = 0
            if nx.number_connected_components(G_temp) > nx.number_connected_components(G):
                collateral = 5.0 # High penalty for breaking connectivity
                
            residual_risk = 0.5 # Proxy value for residual attack probability
            
            j_cost = cost + (self.lambda_collateral * collateral) + (self.mu_residual * residual_risk)
            
            if j_cost < min_cost:
                min_cost = j_cost
                best_intervention = {
                    'edge': candidate_edge,
                    'cost': min_cost,
                    'collateral': collateral,
                    'residual': residual_risk
                }
                
        return best_intervention
