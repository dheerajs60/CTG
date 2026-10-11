import os
import pandas as pd
import numpy as np
import torch

class NetworkDatasetParser:
    """
    Module 1 & 2: Real Dataset Parser & Temporal Graph Slicer.
    Ingests real network flow CSVs (CICIDS2017/UNSW-NB15/NetFlow)
    and constructs sequential dynamic snapshots G_t = (V_t, E_t, X_t).
    """
    def __init__(self, window_size_seconds=10):
        self.window_size = window_size_seconds
        self.ip_to_node = {}
        self.node_to_ip = {}

    def parse_real_csv(self, csv_path="network_flows.csv", 
                       src_col="source_ip", dst_col="dest_ip", 
                       bytes_col="bytes", pkts_col="packets", 
                       dur_col="duration", time_col="timestamp"):
        """
        Parses real-world CSV logs into PyTorch Geometric graph snapshots.
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Dataset file '{csv_path}' not found. Place your real CSV in the directory.")

        df = pd.read_csv(csv_path)

        # Standardize column naming
        df = df.rename(columns={
            src_col: 'source_ip', dst_col: 'dest_ip',
            bytes_col: 'bytes', pkts_col: 'packets',
            dur_col: 'duration', time_col: 'timestamp'
        })

        # Build Global Node Mapping across all active IPs
        all_ips = sorted(list(set(df['source_ip'].astype(str)).union(set(df['dest_ip'].astype(str)))))
        self.ip_to_node = {ip: idx for idx, ip in enumerate(all_ips)}
        self.node_to_ip = {idx: ip for ip, idx in self.ip_to_node.items()}
        num_nodes = len(all_ips)

        min_time = df['timestamp'].min()
        max_time = df['timestamp'].max()

        temporal_snapshots = []

        # Slice flows into temporal windows
        for start_t in np.arange(min_time, max_time, self.window_size):
            end_t = start_t + self.window_size
            window_df = df[(df['timestamp'] >= start_t) & (df['timestamp'] < end_t)]

            adj_matrix = np.zeros((num_nodes, num_nodes), dtype=np.float32)
            node_features = np.zeros((num_nodes, 3), dtype=np.float32)

            if not window_df.empty:
                for _, row in window_df.iterrows():
                    u = self.ip_to_node[str(row['source_ip'])]
                    v = self.ip_to_node[str(row['dest_ip'])]

                    adj_matrix[u, v] = 1.0
                    adj_matrix[v, u] = 1.0

                    node_features[u] += [row['bytes'], row['packets'], row['duration']]
                    node_features[v] += [row['bytes'], row['packets'], row['duration']]

            # Z-score Feature Normalization
            std = np.std(node_features, axis=0)
            std[std == 0] = 1.0
            norm_x = (node_features - np.mean(node_features, axis=0)) / std

            edge_index = np.argwhere(adj_matrix > 0).T

            temporal_snapshots.append({
                'adj': torch.tensor(adj_matrix, dtype=torch.float32),
                'x': torch.tensor(norm_x, dtype=torch.float32),
                'edge_index': torch.tensor(edge_index, dtype=torch.long),
                'time_range': (start_t, end_t)
            })

        return temporal_snapshots, num_nodes