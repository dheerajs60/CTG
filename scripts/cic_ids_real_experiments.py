import os
import pandas as pd
import networkx as nx
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

def main():
    print("Running CIC-IDS2017 Real Temporal Topology Experiments...")
    
    file_path = "data/cic_ids2017/TrafficLabelling /Wednesday-workingHours.pcap_ISCX.csv"
    
    if not os.path.exists(file_path):
        print(f"Error: Dataset not found at {file_path}")
        return
        
    df = pd.read_csv(file_path, encoding='latin1', low_memory=False)
    df.columns = df.columns.str.strip()
    
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    df = df.dropna(subset=['Timestamp']).sort_values('Timestamp')
    
    # Take a manageable sample sorted by time for quick processing in sandbox
    # Using the first 20,000 flows
    df = df.head(20000).copy()
    
    # Split into 10 snapshots
    num_snapshots = 10
    chunk_size = len(df) // num_snapshots
    
    snapshots = []
    labels = []
    
    for i in range(num_snapshots):
        start_idx = i * chunk_size
        end_idx = start_idx + chunk_size
        chunk = df.iloc[start_idx:end_idx]
        
        G = nx.DiGraph()
        attack_count = 0
        
        for _, row in chunk.iterrows():
            src = row['Source IP']
            dst = row['Destination IP']
            lbl = row['Label']
            
            if lbl != 'BENIGN':
                attack_count += 1
                
            if G.has_edge(src, dst):
                G[src][dst]['weight'] += 1
            else:
                G.add_edge(src, dst, weight=1)
                
        snapshots.append(G)
        labels.append(1 if attack_count > (chunk_size * 0.05) else 0) # 1 if >5% attack flows
        
    # Phase 1: Temporal Topology Change Analysis
    changes = []
    transitions_data = []
    for i in range(1, num_snapshots):
        g_prev = snapshots[i-1]
        g_curr = snapshots[i]
        
        added_edges_set = set(g_curr.edges()) - set(g_prev.edges())
        removed_edges_set = set(g_prev.edges()) - set(g_curr.edges())
        added_nodes_set = set(g_curr.nodes()) - set(g_prev.nodes())
        removed_nodes_set = set(g_prev.nodes()) - set(g_curr.nodes())
        
        added_edges = len(added_edges_set)
        removed_edges = len(removed_edges_set)
        
        changes.append({
            'Snapshot': i,
            'Prev_Snapshot': i-1,
            'Added_Edges': added_edges,
            'Removed_Edges': removed_edges,
            'Node_Count': g_curr.number_of_nodes(),
            'Density': nx.density(g_curr),
            'Is_Attack_Associated': labels[i]
        })
        
        transitions_data.append({
            't': i-1,
            't_next': i,
            'added_edges': str(list(added_edges_set)),
            'removed_edges': str(list(removed_edges_set)),
            'added_nodes': str(list(added_nodes_set)),
            'removed_nodes': str(list(removed_nodes_set)),
            'timestamp_interval': f"Snapshot {i-1} to {i}"
        })
        
    os.makedirs('results/metrics', exist_ok=True)
    os.makedirs('results/real', exist_ok=True)
    df_changes = pd.DataFrame(changes)
    df_changes.to_csv('results/metrics/cic_ids_temporal_changes.csv', index=False)
    
    df_transitions = pd.DataFrame(transitions_data)
    df_transitions.to_csv('results/real/genesis_transitions.csv', index=False)
    
    # Phase 2 & 3: Attack-associated Topology Anomaly Detection
    # Using edge additions as a simple anomaly feature
    
    train_end = 4
    val_end = 6
    
    train_features = df_changes['Added_Edges'].iloc[:train_end].values
    train_labels = df_changes['Is_Attack_Associated'].iloc[:train_end].values
    
    # Threshold based on train mean + 1 std
    threshold = np.mean(train_features) + np.std(train_features)
    
    test_features = df_changes['Added_Edges'].iloc[val_end:].values
    test_labels = df_changes['Is_Attack_Associated'].iloc[val_end:].values
    
    preds = (test_features > threshold).astype(int)
    
    try:
        f1 = f1_score(test_labels, preds, zero_division=0)
        prec = precision_score(test_labels, preds, zero_division=0)
        rec = recall_score(test_labels, preds, zero_division=0)
    except:
        f1, prec, rec = 0, 0, 0
        
    df_gv = pd.DataFrame([{
        'Model': 'CTG Statistical Topology Anomaly',
        'F1': f1,
        'Precision': prec,
        'Recall': rec
    }])
    df_gv.to_csv('results/metrics/cic_ids_gv_real.csv', index=False)
    
    # Phase 4: Grammar Evolution
    # Learn valid edges from train (benign)
    grammar_rules = set()
    for i in range(train_end):
        if df_changes['Is_Attack_Associated'].iloc[i] == 0:
            grammar_rules.update(snapshots[i+1].edges())
            
    test_snapshots = snapshots[val_end+1:]
    test_snapshot_labels = labels[val_end+1:]
    
    acc_legit = 0
    rej_legit = 0
    acc_mal = 0
    rej_mal = 0
    
    for i, g in enumerate(test_snapshots):
        new_edges = set(g.edges()) - set(snapshots[val_end + i].edges())
        is_malicious = test_snapshot_labels[i] == 1
        
        for edge in new_edges:
            if edge in grammar_rules:
                if is_malicious: acc_mal += 1
                else: acc_legit += 1
            else:
                if is_malicious: rej_mal += 1
                else: rej_legit += 1
                
    df_grammar = pd.DataFrame([{
        'Legit_Accepted': acc_legit,
        'Legit_Rejected': rej_legit,
        'Malicious_Accepted': acc_mal,
        'Malicious_Rejected': rej_mal
    }])
    df_grammar.to_csv('results/metrics/cic_ids_grammar_real.csv', index=False)
    print("Completed real topological experiments.")

if __name__ == "__main__":
    main()
