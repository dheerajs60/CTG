import torch
import pandas as pd
from pathlib import Path
import json
import time
from models.evolve_gcn import EvolveGCNH
EDGE_LISTS_DIR = Path("results/apex_ids2026/graphs/edge_lists")

import sys
sys.path.append('.')

CONFIG = {
    "train_end": "2026-07-15",
    "val_end": "2026-07-22",
    "test_end": "2026-08-03",
    "hidden_dim": 64,
    "seeds": [42, 100, 1234],
}

def load_snapshots():
    windows = sorted([d.name for d in EDGE_LISTS_DIR.iterdir() if d.is_dir()])
    
    snapshots = []
    global_nodes = set()
    
    for w in windows:
        date_str = w.split('=')[1]
        df = pd.read_parquet(EDGE_LISTS_DIR / w)
        edges = set(zip(df['src_ip'], df['dst_ip']))
        snapshots.append({
            'date': date_str,
            'edges': edges
        })
        for u, v in edges:
            global_nodes.add(u)
            global_nodes.add(v)
            
    node2id = {n: i for i, n in enumerate(sorted(list(global_nodes)))}
    return snapshots, node2id

def generate_candidates(G_curr_edges, G_next_edges, node2id, seed_val):
    import numpy as np
    import random
    np.random.seed(seed_val)
    random.seed(seed_val)
    
    nodes_seen_set = set()
    for u, v in G_curr_edges:
        nodes_seen_set.add(u)
        nodes_seen_set.add(v)
        
    nodes_seen = list(nodes_seen_set)
    if len(nodes_seen) < 2:
        return [], []
        
    pos_edges = [(u, v) for u, v in G_next_edges if u in nodes_seen_set and v in nodes_seen_set]
    num_pos = len(pos_edges)
    
    if num_pos == 0:
        return [], []
        
    neg_edges = []
    next_edge_set = set(G_next_edges)
    num_nodes = len(nodes_seen)
    
    if num_nodes > 1:
        u_idx = np.random.randint(0, num_nodes, size=num_pos * 3)
        v_idx = np.random.randint(0, num_nodes, size=num_pos * 3)
        
        for u_i, v_i in zip(u_idx, v_idx):
            if len(neg_edges) >= num_pos:
                break
            u = nodes_seen[u_i]
            v = nodes_seen[v_i]
            if u != v and (u, v) not in next_edge_set:
                neg_edges.append((u, v))
                
        while len(neg_edges) < num_pos and len(neg_edges) > 0:
            neg_edges.append(neg_edges[0])
            
    if len(neg_edges) < num_pos:
        return [], []
            
    all_edges = pos_edges + neg_edges
    labels = [1]*len(pos_edges) + [0]*len(neg_edges)
    return all_edges, labels

def evaluate_and_save(seed, snapshots, node2id):
    out_dir = Path("results/apex_ids2026/predictions")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    val_end_idx = 0
    for i, s in enumerate(snapshots):
        if s['date'] <= CONFIG['val_end']:
            val_end_idx = i
            
    model_path = Path(f"results/apex_ids2026/evolvegcn/evolvegcn_apex_seed{seed}.pt")
    if not model_path.exists():
        print(f"Missing {model_path}")
        return
        
    torch.manual_seed(seed)
    
    model = EvolveGCNH(num_nodes=len(node2id), in_channels=CONFIG['hidden_dim'], out_channels=CONFIG['hidden_dim'])
    model.load_state_dict(torch.load(model_path))
    model.eval()
    
    x_init = torch.randn((len(node2id), CONFIG['hidden_dim']))
    h_state = None
    
    # We must run forward pass through train+val to build up h_state
    with torch.no_grad():
        for t in range(val_end_idx + 1):
            G_curr = snapshots[t]
            edge_idx = torch.tensor([[node2id[u], node2id[v]] for u, v in G_curr['edges']], dtype=torch.long).T
            if edge_idx.numel() == 0: edge_idx = torch.zeros((2,0), dtype=torch.long)
            emb, h_state = model.forward_graph(x_init, edge_idx, h_state)
            
        predictions = []
        
        # Test Phase
        for t in range(val_end_idx + 1, len(snapshots) - 1):
            G_curr = snapshots[t]
            G_next = snapshots[t+1]
            
            cands, labels = generate_candidates(G_curr['edges'], G_next['edges'], node2id, seed + 888 + t)
            if len(cands) == 0:
                edge_idx = torch.tensor([[node2id[u], node2id[v]] for u, v in G_curr['edges']], dtype=torch.long).T
                if edge_idx.numel() == 0: edge_idx = torch.zeros((2,0), dtype=torch.long)
                emb, h_state = model.forward_graph(x_init, edge_idx, h_state)
                continue
                
            cands_idx = torch.tensor([[node2id[u], node2id[v]] for u, v in cands], dtype=torch.long).T
            
            logits = model.predict_edges(emb, cands_idx)
            probs = torch.sigmoid(logits)
            preds = (probs > 0.5).float()
            
            curr_edge_set = set(G_curr['edges'])
            
            for i, (u, v) in enumerate(cands):
                pers = 1.0 if (u, v) in curr_edge_set else 0.0
                predictions.append({
                    'snapshot_id': t,
                    'snapshot_date': G_curr['date'],
                    'src': u,
                    'dst': v,
                    'label': labels[i],
                    'gcn_prob': probs[i].item(),
                    'gcn_pred': int(preds[i].item()),
                    'pers_prob': pers,
                    'pers_pred': int(pers)
                })
                
            # Forward graph for next step
            edge_idx = torch.tensor([[node2id[u], node2id[v]] for u, v in G_curr['edges']], dtype=torch.long).T
            if edge_idx.numel() == 0: edge_idx = torch.zeros((2,0), dtype=torch.long)
            emb, h_state = model.forward_graph(x_init, edge_idx, h_state)
            
    df = pd.DataFrame(predictions)
    df.to_parquet(out_dir / f"test_predictions_seed{seed}.parquet", index=False)
    print(f"Saved {len(df)} predictions for Seed {seed}")

if __name__ == "__main__":
    print("Loading snapshots...")
    snapshots, node2id = load_snapshots()
    for s in CONFIG['seeds']:
        evaluate_and_save(s, snapshots, node2id)
