import os
import pandas as pd
import networkx as nx

def main():
    print("Building CIC-IDS2017 Temporal Graph Pipeline...")
    # Load Wednesday data as an example for building the graph (manageable size)
    file_path = "datasets/cic_ids2017/TrafficLabelling /Wednesday-workingHours.pcap_ISCX.csv"
    
    # Read CSV
    df = pd.read_csv(file_path, encoding='latin1', low_memory=False)
    df.columns = df.columns.str.strip()
    
    # Ensure chronological order
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    df = df.dropna(subset=['Timestamp']).sort_values('Timestamp')
    
    # Extract only what we need for the temporal graph to save memory
    graph_df = df[['Source IP', 'Destination IP', 'Timestamp', 'Label', 'Protocol', 'Destination Port']].copy()
    
    # Window size: lets divide into 5 chunks chronologically
    num_snapshots = 5
    chunk_size = len(graph_df) // num_snapshots
    
    stats = []
    
    for i in range(num_snapshots):
        start_idx = i * chunk_size
        end_idx = start_idx + chunk_size if i < num_snapshots - 1 else len(graph_df)
        snapshot = graph_df.iloc[start_idx:end_idx]
        
        G = nx.DiGraph()
        benign = 0
        attack = 0
        attack_types = set()
        
        for _, row in snapshot.iterrows():
            src = row['Source IP']
            dst = row['Destination IP']
            lbl = row['Label']
            
            if lbl == 'BENIGN':
                benign += 1
            else:
                attack += 1
                attack_types.add(lbl)
                
            if G.has_edge(src, dst):
                G[src][dst]['weight'] += 1
            else:
                G.add_edge(src, dst, weight=1, first_seen=row['Timestamp'])
                
        stats.append({
            'Snapshot': i + 1,
            'Total Nodes': G.number_of_nodes(),
            'Total Edges': G.number_of_edges(),
            'Unique Source IPs': len(snapshot['Source IP'].unique()),
            'Unique Dest IPs': len(snapshot['Destination IP'].unique()),
            'Benign Flows': benign,
            'Attack Flows': attack,
            'Attack Types': "|".join(attack_types) if attack_types else "None",
            'Graph Density': nx.density(G)
        })
        
    stats_df = pd.DataFrame(stats)
    os.makedirs('results/metrics', exist_ok=True)
    stats_df.to_csv('results/metrics/cic_ids2017_graph_statistics.csv', index=False)
    print("Saved results/metrics/cic_ids2017_graph_statistics.csv")

if __name__ == "__main__":
    main()
