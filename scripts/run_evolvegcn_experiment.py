import os
import random
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import networkx as nx
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score, f1_score, precision_score, recall_score
from models.evolve_gcn import EvolveGCNH

# Config
CONFIG = {
    "num_snapshots": 10,
    "chunk_size": 2000,
    "train_snapshots": 4,
    "val_snapshots": 2,
    "test_snapshots": 4,
    "epochs": 10,
    "lr": 0.005,
    "hidden_dim": 32,
    "seeds": [42, 123, 999]
}

def generate_candidates(G_curr, G_next, seed):
    np.random.seed(seed)
    random.seed(seed)
    
    pos_edges = list(G_next.edges())
    num_pos = len(pos_edges)
    
    if num_pos == 0:
        return torch.zeros((2, 0), dtype=torch.long), torch.zeros(0)
        
    # FIX: Only use nodes seen up to G_curr to prevent leaking future nodes from G_next
    nodes_seen = list(set(G_curr.nodes()))
    if len(nodes_seen) < 2:
        return torch.zeros((2, 0), dtype=torch.long), torch.zeros(0)
        
    neg_edges = []
    # simple uniform negative sampling
    while len(neg_edges) < num_pos:
        u = random.choice(nodes_seen)
        v = random.choice(nodes_seen)
        if u != v and not G_next.has_edge(u, v):
            neg_edges.append((u, v))
            
    all_edges = pos_edges + neg_edges
    labels = [1]*num_pos + [0]*num_pos
    
    # Shuffle
    c = list(zip(all_edges, labels))
    random.shuffle(c)
    all_edges, labels = zip(*c)
    
    # Encode node strings to ints for this step (we need a global mapping really)
    # Return raw text edges, we'll map them
    return list(all_edges), list(labels)

def build_snapshots():
    file_path = "datasets/cic_ids2017/TrafficLabelling /Wednesday-workingHours.pcap_ISCX.csv"
    df = pd.read_csv(file_path, encoding='latin1', low_memory=False)
    df.columns = df.columns.str.strip()
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    df = df.dropna(subset=['Timestamp']).sort_values('Timestamp').head(CONFIG['chunk_size'] * CONFIG['num_snapshots'])
    
    snapshots = []
    global_nodes = set()
    
    for i in range(CONFIG['num_snapshots']):
        start = i * CONFIG['chunk_size']
        end = start + CONFIG['chunk_size']
        chunk = df.iloc[start:end]
        G = nx.DiGraph()
        for _, row in chunk.iterrows():
            G.add_edge(row['Source IP'], row['Destination IP'])
            global_nodes.add(row['Source IP'])
            global_nodes.add(row['Destination IP'])
        snapshots.append(G)
        
    node2id = {n: i for i, n in enumerate(global_nodes)}
    return snapshots, node2id

def calc_metrics(y_true, y_pred, y_prob):
    try:
        roc = roc_auc_score(y_true, y_prob)
        pr = average_precision_score(y_true, y_prob)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        return roc, pr, f1, prec, rec
    except:
        return 0,0,0,0,0

def run_experiment(seed, snapshots, node2id):
    torch.manual_seed(seed)
    
    model = EvolveGCNH(num_nodes=len(node2id), in_channels=CONFIG['hidden_dim'], out_channels=CONFIG['hidden_dim'])
    optimizer = optim.Adam(model.parameters(), lr=CONFIG['lr'])
    criterion = nn.BCEWithLogitsLoss()
    
    # Static node features (random init for now, could be degree based)
    x = torch.randn((len(node2id), CONFIG['hidden_dim']))
    
    # Training Loop
    model.train()
    for epoch in range(CONFIG['epochs']):
        h_state = None
        epoch_loss = 0
        for t in range(CONFIG['train_snapshots']):
            G_t = snapshots[t]
            G_next = snapshots[t+1]
            
            # Map edges
            edge_idx = torch.tensor([[node2id[u], node2id[v]] for u, v in G_t.edges()], dtype=torch.long).T
            if edge_idx.numel() == 0: edge_idx = torch.zeros((2,0), dtype=torch.long)
            
            emb, h_state = model.forward_graph(x, edge_idx, h_state)
            
            cands, labels = generate_candidates(G_t, G_next, seed+t)
            if len(cands) == 0: continue
            
            cands_idx = torch.tensor([[node2id[u], node2id[v]] for u, v in cands], dtype=torch.long).T
            labels_t = torch.tensor(labels, dtype=torch.float)
            
            optimizer.zero_grad()
            logits = model.predict_edges(emb, cands_idx)
            loss = criterion(logits, labels_t)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            # detach h_state
            h_state = h_state.detach()
            
    # Evaluation
    model.eval()
    h_state = None
    
    # Catch up state
    with torch.no_grad():
        for t in range(CONFIG['train_snapshots'] + CONFIG['val_snapshots']):
            G_t = snapshots[t]
            edge_idx = torch.tensor([[node2id[u], node2id[v]] for u, v in G_t.edges()], dtype=torch.long).T
            if edge_idx.numel() == 0: edge_idx = torch.zeros((2,0), dtype=torch.long)
            _, h_state = model.forward_graph(x, edge_idx, h_state)
            
    # Test Window
    all_y_true = []
    all_y_prob = []
    all_y_pred = []
    
    all_pers_prob = []
    all_pers_pred = []
    
    with torch.no_grad():
        for t in range(CONFIG['train_snapshots'] + CONFIG['val_snapshots'], len(snapshots)-1):
            G_t = snapshots[t]
            G_next = snapshots[t+1]
            
            edge_idx = torch.tensor([[node2id[u], node2id[v]] for u, v in G_t.edges()], dtype=torch.long).T
            if edge_idx.numel() == 0: edge_idx = torch.zeros((2,0), dtype=torch.long)
            
            emb, h_state = model.forward_graph(x, edge_idx, h_state)
            
            cands, labels = generate_candidates(G_t, G_next, seed+t)
            if len(cands) == 0: continue
            
            cands_idx = torch.tensor([[node2id[u], node2id[v]] for u, v in cands], dtype=torch.long).T
            labels_t = torch.tensor(labels, dtype=torch.float)
            
            logits = model.predict_edges(emb, cands_idx)
            probs = torch.sigmoid(logits)
            preds = (probs > 0.5).float()
            
            all_y_true.extend(labels)
            all_y_prob.extend(probs.tolist())
            all_y_pred.extend(preds.tolist())
            
            # Persistence Baseline
            for u, v in cands:
                pers = 1.0 if G_t.has_edge(u, v) else 0.0
                all_pers_prob.append(pers)
                all_pers_pred.append(pers)
                
    gcn_metrics = calc_metrics(all_y_true, all_y_pred, all_y_prob)
    pers_metrics = calc_metrics(all_y_true, all_pers_pred, all_pers_prob)
    
    return gcn_metrics, pers_metrics

def main():
    print("Running EvolveGCN-H Temporal Prediction vs Persistence...")
    snapshots, node2id = build_snapshots()
    
    results = []
    for s in CONFIG['seeds']:
        print(f"Running Seed {s}...")
        gcn, pers = run_experiment(s, snapshots, node2id)
        
        results.append({
            'Model': 'EvolveGCN-H',
            'Seed': s,
            'ROC-AUC': gcn[0],
            'PR-AUC': gcn[1],
            'F1': gcn[2],
            'Precision': gcn[3],
            'Recall': gcn[4]
        })
        results.append({
            'Model': 'Persistence Baseline',
            'Seed': s,
            'ROC-AUC': pers[0],
            'PR-AUC': pers[1],
            'F1': pers[2],
            'Precision': pers[3],
            'Recall': pers[4]
        })
        
    df = pd.DataFrame(results)
    # Aggregation
    agg = df.groupby('Model').agg(['mean', 'std']).reset_index()
    # Flatten columns
    agg.columns = ['_'.join(col).strip() if col[1] else col[0] for col in agg.columns.values]
    
    os.makedirs('results/metrics', exist_ok=True)
    df.to_csv('results/metrics/topology_prediction_benchmark_raw.csv', index=False)
    agg.to_csv('results/metrics/topology_prediction_benchmark.csv', index=False)
    print("Saved results/metrics/topology_prediction_benchmark.csv")
    print(agg)

if __name__ == "__main__":
    main()
