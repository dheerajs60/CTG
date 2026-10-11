import pandas as pd
from pathlib import Path
import json

GRAPHS_DIR = Path("/Users/kovoordheeraj/Documents/CN Lab CTG/results/apex_ids2026/graphs")
OUTPUT_DIR = Path("/Users/kovoordheeraj/Documents/CN Lab CTG/results/apex_ids2026/baselines")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def run_persistence_baseline():
    print("Running Persistence Baseline (Predicting Edge at T = Edge at T-1)...")
    diagnostics = pd.read_csv(GRAPHS_DIR / "graph_diagnostics.csv")
    
    # We load edge lists iteratively to compare T and T-1
    edge_lists_dir = GRAPHS_DIR / "edge_lists"
    windows = sorted([d.name for d in edge_lists_dir.iterdir() if d.is_dir()])
    
    results = []
    
    # Validation period: 2026-07-16 to 2026-07-22
    # Test period: 2026-07-23 to 2026-08-03
    
    for i in range(1, len(windows)):
        prev_window = windows[i-1]
        curr_window = windows[i]
        
        # Parse date to check partition
        curr_date = curr_window.split('=')[1]
        partition = "train"
        if "2026-07-16" <= curr_date <= "2026-07-22":
            partition = "validation"
        elif "2026-07-23" <= curr_date <= "2026-08-03":
            partition = "test"
            
        if partition == "train":
            continue
            
        # Load prev edges
        df_prev = pd.read_parquet(edge_lists_dir / prev_window)
        edges_prev = set(zip(df_prev['src_ip'], df_prev['dst_ip']))
        
        # Load curr edges
        df_curr = pd.read_parquet(edge_lists_dir / curr_window)
        edges_curr = set(zip(df_curr['src_ip'], df_curr['dst_ip']))
        
        # Persistence predicts prev_edges for curr_edges
        true_positives = len(edges_curr.intersection(edges_prev))
        false_positives = len(edges_prev - edges_curr)
        false_negatives = len(edges_curr - edges_prev)
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        results.append({
            "window": curr_date,
            "partition": partition,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "precision": precision,
            "recall": recall,
            "f1": f1
        })
        
    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_DIR / "persistence_baseline_results.csv", index=False)
    
    val_f1 = results_df[results_df['partition'] == 'validation']['f1'].mean()
    test_f1 = results_df[results_df['partition'] == 'test']['f1'].mean()
    
    print(f"Validation F1 (Mean): {val_f1:.4f}")
    print(f"Test F1 (Mean): {test_f1:.4f}")
    
    with open(OUTPUT_DIR / "persistence_baseline_summary.json", "w") as f:
        json.dump({
            "model": "persistence",
            "task": "edge_prediction",
            "validation_f1_mean": val_f1,
            "test_f1_mean": test_f1
        }, f, indent=4)

if __name__ == "__main__":
    run_persistence_baseline()
