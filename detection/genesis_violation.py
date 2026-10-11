import numpy as np
import torch
import networkx as nx

def compute_topology_metrics(preds_binary, targets_binary, pos_edge_index, neg_edge_index, num_nodes):
    intersection = np.sum(preds_binary * targets_binary)
    union = np.sum(preds_binary) + np.sum(targets_binary) - intersection
    jaccard = intersection / max(union, 1)
    
    unexpected_count = np.sum((preds_binary == 1) & (targets_binary == 0))
    missed_count = np.sum((preds_binary == 0) & (targets_binary == 1))
    
    G_actual = nx.Graph()
    G_actual.add_nodes_from(range(num_nodes))
    pos_edges = pos_edge_index.t().tolist()
    neg_edges = neg_edge_index.t().tolist() if neg_edge_index is not None else []
    edges = pos_edges + neg_edges
    for i, (u, v) in enumerate(edges):
        if targets_binary[i] == 1:
            G_actual.add_edge(u, v)
            
    G_pred = nx.Graph()
    G_pred.add_nodes_from(range(num_nodes))
    for i, (u, v) in enumerate(edges):
        if preds_binary[i] == 1:
            G_pred.add_edge(u, v)
            
    den_pred = nx.density(G_pred)
    den_actual = nx.density(G_actual)
    density_difference = abs(den_pred - den_actual)
    
    deg_pred = np.mean([d for n, d in G_pred.degree()]) if len(G_pred.nodes) > 0 else 0
    deg_actual = np.mean([d for n, d in G_actual.degree()]) if len(G_actual.nodes) > 0 else 0
    
    max_possible_deg = max(num_nodes - 1, 1)
    degree_difference = abs(deg_pred - deg_actual) / max_possible_deg
    
    unexpected_edge_ratio = unexpected_count / max(G_actual.number_of_edges(), 1)
    missed_edge_ratio = missed_count / max(G_actual.number_of_edges(), 1)
        
    return 1.0 - jaccard, degree_difference, density_difference, unexpected_edge_ratio, missed_edge_ratio

def calculate_gv_score(edge_violation, degree_difference, density_difference, unexpected_edge_ratio, missed_edge_ratio, w1=0.40, w2=0.20, w3=0.10, w4=0.15, w5=0.15):
    gv_score = (w1 * edge_violation) + (w2 * degree_difference) + (w3 * density_difference) + (w4 * unexpected_edge_ratio) + (w5 * missed_edge_ratio)
    return gv_score

def compute_gv_methods(preds_binary, targets_binary, pos_edge_index, neg_edge_index, num_nodes):
    intersection = np.sum(preds_binary * targets_binary)
    union = np.sum(preds_binary) + np.sum(targets_binary) - intersection
    jaccard = intersection / max(union, 1)
    
    unexpected_count = np.sum((preds_binary == 1) & (targets_binary == 0))
    missed_count = np.sum((preds_binary == 0) & (targets_binary == 1))
    
    G_actual = nx.Graph()
    G_actual.add_nodes_from(range(num_nodes))
    edges = pos_edge_index.t().tolist() + (neg_edge_index.t().tolist() if neg_edge_index is not None else [])
    for i, (u, v) in enumerate(edges):
        if targets_binary[i] == 1: G_actual.add_edge(u, v)
            
    G_pred = nx.Graph()
    G_pred.add_nodes_from(range(num_nodes))
    for i, (u, v) in enumerate(edges):
        if preds_binary[i] == 1: G_pred.add_edge(u, v)
            
    den_pred = nx.density(G_pred)
    den_actual = nx.density(G_actual)
    deg_pred = np.mean([d for n, d in G_pred.degree()]) if len(G_pred.nodes) > 0 else 0
    deg_actual = np.mean([d for n, d in G_actual.degree()]) if len(G_actual.nodes) > 0 else 0
    max_deg = max(num_nodes - 1, 1)
    
    # Method 1
    ev = 1.0 - jaccard
    deg_d = abs(deg_pred - deg_actual) / max_deg
    den_d = abs(den_pred - den_actual)
    u_ratio = unexpected_count / max(G_actual.number_of_edges(), 1)
    m_ratio = missed_count / max(G_actual.number_of_edges(), 1)
    gv_standard = 0.40 * ev + 0.20 * deg_d + 0.10 * den_d + 0.15 * u_ratio + 0.15 * m_ratio
    
    # Method 2
    rel_den_d = abs(den_pred - den_actual) / max(den_actual, 1e-5)
    rel_deg_d = abs(deg_pred - deg_actual) / max(deg_actual, 1e-5)
    u_ratio_clip = min(u_ratio, 1.0)
    gv_density_aware = 0.40 * ev + 0.20 * rel_deg_d + 0.10 * rel_den_d + 0.15 * u_ratio_clip + 0.15 * m_ratio
    
    # Method 3
    gv_reconstruction = (unexpected_count + missed_count) / max(len(preds_binary), 1)
    
    return gv_standard, gv_density_aware, gv_reconstruction
