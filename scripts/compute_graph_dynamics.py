import pandas as pd
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EDGE_LISTS_DIR = REPO_ROOT / "results/apex_ids2026/graphs/edge_lists"
OUTPUT_DIR = REPO_ROOT / "results/apex_ids2026/graphs"

def compute_graph_dynamics():
    windows = sorted([d.name for d in EDGE_LISTS_DIR.iterdir() if d.is_dir()])
    
    stats = []
    
    prev_edges = set()
    prev_nodes = set()
    
    for i, w in enumerate(windows):
        date_str = w.split('=')[1]
        df = pd.read_parquet(EDGE_LISTS_DIR / w)
        
        curr_edges = set(zip(df['src_ip'], df['dst_ip']))
        curr_nodes = set(df['src_ip']).union(set(df['dst_ip']))
        
        num_edges = len(curr_edges)
        num_nodes = len(curr_nodes)
        density = num_edges / (num_nodes * (num_nodes - 1)) if num_nodes > 1 else 0
        event_volume = df['weight'].sum()
        
        if i == 0:
            new_edges = num_edges
            removed_edges = 0
            retained_edges = 0
            new_nodes = num_nodes
            removed_nodes = 0
        else:
            new_edges = len(curr_edges - prev_edges)
            removed_edges = len(prev_edges - curr_edges)
            retained_edges = len(curr_edges.intersection(prev_edges))
            new_nodes = len(curr_nodes - prev_nodes)
            removed_nodes = len(prev_nodes - curr_nodes)
            
        edge_turnover = (new_edges + removed_edges) / max(1, num_edges + len(prev_edges))
        
        stats.append({
            'date': date_str,
            'nodes': num_nodes,
            'edges': num_edges,
            'density': density,
            'daily_events': event_volume,
            'new_edges': new_edges,
            'removed_edges': removed_edges,
            'retained_edges': retained_edges,
            'edge_turnover': edge_turnover,
            'new_nodes': new_nodes,
            'removed_nodes': removed_nodes
        })
        
        prev_edges = curr_edges
        prev_nodes = curr_nodes
        
    stats_df = pd.DataFrame(stats)
    stats_df.to_csv(OUTPUT_DIR / "graph_transition_statistics.csv", index=False)
    print("Computed graph dynamics and saved to graph_transition_statistics.csv")
    
if __name__ == "__main__":
    compute_graph_dynamics()
