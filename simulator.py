import torch
import numpy as np
import networkx as nx
import copy

class ReverseGenesisAttackSimulator:
    """
    Simulates a structural perturbation (Reverse Genesis Attack) on an isolated graph.
    Modifies edges to create an anomaly.
    """
    def __init__(self, seed=42):
        self.seed = seed
        np.random.seed(seed)
        torch.manual_seed(seed)

    def perturb_graph(self, graph_dict, num_edges_to_add=5, num_edges_to_remove=2):
        """
        Perturbs the graph by adding/removing edges in the edge_index.
        Returns a new graph dictionary.
        """
        perturbed = copy.deepcopy(graph_dict)
        edge_index = perturbed['edge_index'] # shape (2, E)
        num_nodes = perturbed['nodes']
        
        edges = set(tuple(e) for e in edge_index.t().tolist())
        
        # Remove edges
        edges_list = list(edges)
        if len(edges_list) > num_edges_to_remove:
            indices_to_remove = np.random.choice(len(edges_list), num_edges_to_remove, replace=False)
            for idx in indices_to_remove:
                edges.remove(edges_list[idx])
                
        # Add edges
        added = 0
        while added < num_edges_to_add:
            u = np.random.randint(0, num_nodes)
            v = np.random.randint(0, num_nodes)
            if u != v and (u, v) not in edges and (v, u) not in edges:
                edges.add((u, v))
                added += 1
                
        new_edge_index = torch.tensor(list(edges), dtype=torch.long).t().contiguous()
        perturbed['edge_index'] = new_edge_index
        
        # Update nx stats
        G = nx.Graph()
        G.add_nodes_from(range(num_nodes))
        G.add_edges_from(list(edges))
        perturbed['edges'] = G.number_of_edges()
        perturbed['density'] = nx.density(G) if num_nodes > 1 else 0
        perturbed['avg_degree'] = np.mean([d for n, d in G.degree()]) if num_nodes > 0 else 0
        
        return perturbed

class AdaptiveDefenseSimulator:
    """
    Sandboxed mitigation using CounterfactualGenesisBarrier.
    """
    def __init__(self, cgb_module):
        self.cgb = cgb_module

    def apply_defense(self, target_snapshot, h_state):
        best_intervention = self.cgb.find_minimal_intervention(target_snapshot, h_state)
        if not best_intervention:
            return None, target_snapshot
            
        edge_to_cut = best_intervention['edge']
        
        # Apply mitigation to a copy
        mitigated = copy.deepcopy(target_snapshot)
        edges = set(tuple(e) for e in mitigated['edge_index'].t().tolist())
        
        u, v = edge_to_cut
        if (u, v) in edges: edges.remove((u, v))
        if (v, u) in edges: edges.remove((v, u))
            
        mitigated['edge_index'] = torch.tensor(list(edges), dtype=torch.long).t().contiguous()
        
        # Update stats
        G = nx.Graph()
        G.add_nodes_from(range(mitigated['nodes']))
        G.add_edges_from(list(edges))
        mitigated['edges'] = G.number_of_edges()
        
        return best_intervention, mitigated
