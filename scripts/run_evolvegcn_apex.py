import os
import random
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
import time
from pathlib import Path
from sklearn.metrics import roc_auc_score, average_precision_score, f1_score, precision_score, recall_score, confusion_matrix
import json

from models.evolve_gcn import EvolveGCNH

# Paths
GRAPHS_DIR = Path("/Users/kovoordheeraj/Documents/CN Lab CTG/results/apex_ids2026/graphs")
EDGE_LISTS_DIR = GRAPHS_DIR / "edge_lists"
OUTPUT_DIR = Path("/Users/kovoordheeraj/Documents/CN Lab CTG/results/apex_ids2026/evolvegcn")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Config
CONFIG = {
    "train_end": "2026-07-15",
    "val_end": "2026-07-22",
    "epochs": 10,  # Max epochs
    "lr": 0.001,
    "hidden_dim": 64,
    "patience": 5, # Early stopping
    "seeds": [42, 100, 1234],
    "debug_only": False, # Set to False for real runs
    "debug_snapshots": 5
}

def load_snapshots():
    print("Loading graph snapshots...")
    # List all window partitions
    windows = sorted([d.name for d in EDGE_LISTS_DIR.iterdir() if d.is_dir()])
    
    snapshots = []
    global_nodes = set()
    
    if CONFIG['debug_only']:
        print("DEBUG MODE: Only loading first few snapshots.")
        windows = windows[:CONFIG['debug_snapshots']]
        
    for w in windows:
        date_str = w.split('=')[1]
        df = pd.read_parquet(EDGE_LISTS_DIR / w)
        
        edges = set(zip(df['src_ip'], df['dst_ip']))
        for u, v in edges:
            global_nodes.add(u)
            global_nodes.add(v)
            
        snapshots.append({
            'date': date_str,
            'edges': edges
        })
        
    node2id = {n: i for i, n in enumerate(sorted(list(global_nodes)))}
    print(f"Total unique nodes: {len(node2id)}")
    print(f"Total snapshots loaded: {len(snapshots)}")
    return snapshots, node2id

def generate_candidates(G_curr_edges, G_next_edges, node2id, seed):
    np.random.seed(seed)
    random.seed(seed)
    
    # We predict the presence of edges in G_next.
    # Positive edges: edges in G_next where both nodes exist in G_curr (no future-node leakage)
    # The candidate universe is restricted to nodes observed up to and including G_curr
    
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
    # Fast negative sampling
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
                
        # If still not enough, pad
        while len(neg_edges) < num_pos and len(neg_edges) > 0:
            neg_edges.append(neg_edges[0])
            
    if len(neg_edges) < num_pos:
        return [], []
            
    all_edges = pos_edges + neg_edges
    labels = [1]*len(pos_edges) + [0]*len(neg_edges)
    
    # Shuffle
    c = list(zip(all_edges, labels))
    random.shuffle(c)
    all_edges, labels = zip(*c)
    
    return list(all_edges), list(labels)

def calc_metrics(y_true, y_pred, y_prob):
    try:
        roc = roc_auc_score(y_true, y_prob)
        pr = average_precision_score(y_true, y_prob)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        cm = confusion_matrix(y_true, y_pred)
        return roc, pr, f1, prec, rec, cm
    except Exception as e:
        print("Metric Error:", e)
        return 0,0,0,0,0, None

def evaluate(model, snapshots, node2id, start_idx, end_idx, seed_offset, x_init, h_state_in):
    model.eval()
    all_y_true, all_y_prob, all_y_pred = [], [], []
    all_pers_prob, all_pers_pred = [], []
    
    h_state = h_state_in
    
    with torch.no_grad():
        for t in range(start_idx, end_idx - 1):
            G_curr = snapshots[t]
            G_next = snapshots[t+1]
            
            edge_idx = torch.tensor([[node2id[u], node2id[v]] for u, v in G_curr['edges']], dtype=torch.long).T
            if edge_idx.numel() == 0: edge_idx = torch.zeros((2,0), dtype=torch.long)
            
            emb, h_state = model.forward_graph(x_init, edge_idx, h_state)
            
            cands, labels = generate_candidates(G_curr['edges'], G_next['edges'], node2id, seed_offset+t)
            if len(cands) == 0: continue
            
            cands_idx = torch.tensor([[node2id[u], node2id[v]] for u, v in cands], dtype=torch.long).T
            labels_t = torch.tensor(labels, dtype=torch.float)
            
            logits = model.predict_edges(emb, cands_idx)
            probs = torch.sigmoid(logits)
            preds = (probs > 0.5).float()
            
            all_y_true.extend(labels)
            all_y_prob.extend(probs.tolist())
            all_y_pred.extend(preds.tolist())
            
            # Persistence Baseline predictions on EXACT same candidates
            curr_edge_set = set(G_curr['edges'])
            for i, (u, v) in enumerate(cands):
                pers = 1.0 if (u, v) in curr_edge_set else 0.0
                all_pers_prob.append(pers)
                all_pers_pred.append(pers)
                
    gcn_m = calc_metrics(all_y_true, all_y_pred, all_y_prob)
    pers_m = calc_metrics(all_y_true, all_pers_pred, all_pers_prob)
    
    raw_results = {
        'y_true': all_y_true,
        'gcn_prob': all_y_prob,
        'gcn_pred': all_y_pred,
        'pers_prob': all_pers_prob,
        'pers_pred': all_pers_pred
    }
    
    return gcn_m, pers_m, h_state, raw_results

def run_seed(seed, snapshots, node2id):
    torch.manual_seed(seed)
    
    # 1. Temporal Splits
    train_end_idx = 0
    val_end_idx = 0
    if CONFIG['debug_only']:
        train_end_idx = 2
        val_end_idx = 3
    else:
        for i, s in enumerate(snapshots):
            if s['date'] <= CONFIG['train_end']:
                train_end_idx = i
            if s['date'] <= CONFIG['val_end']:
                val_end_idx = i
            
    if train_end_idx == 0 or val_end_idx == 0:
        print("Check temporal splits!")
        return None, None
        
    print(f"Splits: Train [0-{train_end_idx}], Val [{train_end_idx+1}-{val_end_idx}], Test [{val_end_idx+1}-{len(snapshots)-1}]")
    
    # 2. Model Init
    model = EvolveGCNH(num_nodes=len(node2id), in_channels=CONFIG['hidden_dim'], out_channels=CONFIG['hidden_dim'])
    optimizer = optim.Adam(model.parameters(), lr=CONFIG['lr'])
    criterion = nn.BCEWithLogitsLoss()
    
    x_init = torch.randn((len(node2id), CONFIG['hidden_dim']))
    
    best_val_f1 = -1
    best_state = None
    patience_ctr = 0
    
    train_start_time = time.time()
    
    # 3. Training Loop
    # SKIP TRAINING
    best_state = torch.load(OUTPUT_DIR / f"evolvegcn_apex_seed{seed}.pt")
    train_time = 0.0
    
    # 4. Testing
    print("Evaluating Best Model on Test Set...")
    model.load_state_dict(best_state)
    
    # Catch up h_state through train AND val
    model.eval()
    h_state_test = None
    with torch.no_grad():
        for t in range(val_end_idx):
            G_curr = snapshots[t]
            edge_idx = torch.tensor([[node2id[u], node2id[v]] for u, v in G_curr['edges']], dtype=torch.long).T
            if edge_idx.numel() == 0: edge_idx = torch.zeros((2,0), dtype=torch.long)
            _, h_state_test = model.forward_graph(x_init, edge_idx, h_state_test)
            
    test_gcn, test_pers, _, raw_res = evaluate(model, snapshots, node2id, val_end_idx, len(snapshots), seed+888, x_init, h_state_test)
    
    # Save predictions
    out_dir = Path("results/apex_ids2026/predictions")
    out_dir.mkdir(exist_ok=True, parents=True)
    pd.DataFrame(raw_res).to_parquet(out_dir / f"test_predictions_seed{seed}.parquet", index=False)
    print(f"Saved {len(raw_res['y_true'])} predictions for Seed {seed}")
    
    # Log Checkpoint
    ckpt_path = OUTPUT_DIR / f"evolvegcn_apex_seed{seed}.pt"
    # torch.save(best_state, ckpt_path) # skip save since it's already saved
    
    metrics = {
        'Seed': seed,
        'Runtime_sec': train_time,
        'GCN_Test_AUC': test_gcn[0],
        'GCN_Test_PR': test_gcn[1],
        'GCN_Test_F1': test_gcn[2],
        'GCN_Test_Prec': test_gcn[3],
        'GCN_Test_Rec': test_gcn[4],
        'Pers_Test_AUC': test_pers[0],
        'Pers_Test_PR': test_pers[1],
        'Pers_Test_F1': test_pers[2],
        'Pers_Test_Prec': test_pers[3],
        'Pers_Test_Rec': test_pers[4]
    }
    
    return metrics

def main():
    print("=== Starting EvolveGCN-H Evaluation for APEX-IDS2026 ===")
    snapshots, node2id = load_snapshots()
    
    results = []
    
    if CONFIG['debug_only']:
        print("RUNNING DEBUG SMOKE TEST")
        CONFIG['seeds'] = [42]
        CONFIG['epochs'] = 2
        
    for s in CONFIG['seeds']:
        print(f"\n--- Running Seed {s} ---")
        metrics = run_seed(s, snapshots, node2id)
        if metrics:
            results.append(metrics)
            
    if not CONFIG['debug_only'] and results:
        df = pd.DataFrame(results)
        df.to_csv(OUTPUT_DIR / "evolvegcn_vs_persistence_results.csv", index=False)
        
        # Aggregate
        agg = df.drop(columns=['Seed']).mean().to_dict()
        with open(OUTPUT_DIR / "evolvegcn_aggregate_summary.json", "w") as f:
            json.dump(agg, f, indent=4)
            
        print("\n=== Final Aggregated Results ===")
        for k, v in agg.items():
            print(f"{k}: {v:.4f}")

if __name__ == "__main__":
    main()
