import networkx as nx
import torch
import numpy as np
import pandas as pd
from graph.flow_signature import compute_signatures, build_node_mapping

class TemporalGraphBuilder:
    def __init__(self, window_size=2000):
        self.window_size = window_size
        self.node_map = {}
        self.all_nodes = set()
        
    def fit(self, df):
        """Fits the node mapping on the training data to ensure all subsequent nodes are known."""
        src_sigs, dst_sigs = compute_signatures(df)
        self.node_map, self.all_nodes = build_node_mapping(src_sigs, dst_sigs)
        return self
        
    def transform(self, df):
        """Converts a dataframe of flows into a sequence of graph snapshots."""
        graphs = []
        num_nodes = len(self.all_nodes)
        
        # If the dataframe is empty or node_map is empty, return early
        if df.empty or num_nodes == 0:
            return graphs
            
        src_sigs, dst_sigs = compute_signatures(df)
        df_copy = df.copy()
        df_copy['src_sig'] = src_sigs
        df_copy['dst_sig'] = dst_sigs
        
        for i in range(0, len(df_copy), self.window_size):
            window = df_copy.iloc[i:i+self.window_size]
            if len(window) < 10: continue
                
            edges_u = window['src_sig'].map(self.node_map).values
            edges_v = window['dst_sig'].map(self.node_map).values
            valid_idx = (~np.isnan(edges_u)) & (~np.isnan(edges_v))
            edges_u = edges_u[valid_idx].astype(int)
            edges_v = edges_v[valid_idx].astype(int)
            
            edges_uv = list(set(zip(edges_u, edges_v)))
            edges_uv = [e for e in edges_uv if e[0] != e[1]]
            if len(edges_uv) == 0: continue
                
            edge_index = torch.tensor(edges_uv, dtype=torch.long).t().contiguous()
            x = torch.ones((num_nodes, 4), dtype=torch.float)
            
            attack_count = window['label'].sum() if 'label' in window else 0
            total_flows = len(window)
            attack_ratio = attack_count / total_flows if total_flows > 0 else 0
            
            num_pos = edge_index.size(1)
            neg_u = torch.randint(0, num_nodes, (num_pos,))
            neg_v = torch.randint(0, num_nodes, (num_pos,))
            neg_edge_index = torch.stack([neg_u, neg_v], dim=0)
            
            nx_g = nx.Graph()
            nx_g.add_edges_from(edge_index.t().tolist())
            nodes_cnt = nx_g.number_of_nodes()
            edges_cnt = nx_g.number_of_edges()
            density = nx.density(nx_g) if nodes_cnt > 1 else 0
            avg_deg = np.mean([d for n, d in nx_g.degree()]) if nodes_cnt > 0 else 0
            
            mean_risk = window['flow_risk'].mean() if 'flow_risk' in window else 0
            
            graphs.append({
                'x': x, 'edge_index': edge_index, 'neg_edge_index': neg_edge_index,
                'label': 0, 'attack_ratio': attack_ratio, 'attack_count': attack_count,
                'total_flows': total_flows, 'window_id': len(graphs), 'nodes': nodes_cnt,
                'edges': edges_cnt, 'density': density, 'avg_degree': avg_deg,
                'mean_risk': mean_risk, 'num_total_nodes': num_nodes
            })
            
        return graphs
