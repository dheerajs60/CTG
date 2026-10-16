"""
Multi-Scale Graph Dynamics Analysis for APEX-IDS2026 and CIC-IDS2017.
Computes Edge Recurrence, Novelty, and Symmetric Turnover across temporal window scales:
- APEX-IDS2026: 6h, 12h, 24h
- CIC-IDS2017: 1h, 6h, 24h
Directly handles partial windows, duplicate flows, and collection boundaries.
Saves structured CSV and JSON outputs in results/metrics/.
"""

import sys
from pathlib import Path
import json
import duckdb
import pandas as pd
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
APEX_PARQUET = REPO_ROOT / "datasets/APEX-IDS2026/apex_ids2026_hc_subset.parquet"
CIC_CSV_GLOB = str(REPO_ROOT / "datasets/cic_ids2017/TrafficLabelling /*.csv")
METRICS_DIR = REPO_ROOT / "results/metrics"
METRICS_DIR.mkdir(parents=True, exist_ok=True)


def compute_window_transition_stats(df_edges, window_col="window_start"):
    """
    Given a DataFrame of aggregated unique edges per window with columns:
    [window_col, src_ip, dst_ip, flow_count]
    Computes recurrence, novelty, and turnover metrics sequentially.
    """
    windows = sorted(df_edges[window_col].unique())
    stats = []
    
    prev_edges = set()
    prev_nodes = set()
    
    for i, w in enumerate(windows):
        w_df = df_edges[df_edges[window_col] == w]
        curr_edges = set(zip(w_df['src_ip'], w_df['dst_ip']))
        curr_nodes = set(w_df['src_ip']).union(set(w_df['dst_ip']))
        
        num_e = len(curr_edges)
        num_n = len(curr_nodes)
        total_flows = int(w_df['flow_count'].sum()) if 'flow_count' in w_df.columns else num_e
        
        if i == 0:
            retained = 0
            new_e = num_e
            removed = 0
            rec_rate = 0.0
            nov_rate = 1.0
            turnover_jaccard = 1.0
            turnover_dice = 1.0
        else:
            retained = len(curr_edges.intersection(prev_edges))
            new_e = len(curr_edges - prev_edges)
            removed = len(prev_edges - curr_edges)
            rec_rate = retained / num_e if num_e > 0 else 0.0
            nov_rate = new_e / num_e if num_e > 0 else 0.0
            union_len = len(curr_edges.union(prev_edges))
            sum_len = num_e + len(prev_edges)
            turnover_jaccard = (new_e + removed) / union_len if union_len > 0 else 0.0
            turnover_dice = (new_e + removed) / sum_len if sum_len > 0 else 0.0
            
        stats.append({
            "window_id": i,
            "window_start": str(w),
            "nodes": num_n,
            "edges": num_e,
            "flows": total_flows,
            "retained_edges": retained,
            "new_edges": new_e,
            "removed_edges": removed,
            "recurrence_rate": rec_rate,
            "novelty_rate": nov_rate,
            "symmetric_turnover": turnover_jaccard,
            "turnover_jaccard": turnover_jaccard,
            "turnover_dice": turnover_dice
        })
        
        prev_edges = curr_edges
        prev_nodes = curr_nodes
        
    return pd.DataFrame(stats)


def analyze_apex():
    print("=" * 70)
    print("Analyzing APEX-IDS2026 Multi-Scale Dynamics (6h, 12h, 24h)...")
    print("=" * 70)
    
    if not APEX_PARQUET.exists():
        print(f"Error: APEX parquet not found at {APEX_PARQUET}")
        return None
        
    con = duckdb.connect()
    
    configs = [
        {"scale": "24h", "trunc_expr": "date_trunc('day', flow_start)"},
        {"scale": "12h", "trunc_expr": "date_trunc('day', flow_start) + INTERVAL (FLOOR(date_part('hour', flow_start) / 12) * 12) HOUR"},
        {"scale": "6h", "trunc_expr": "date_trunc('day', flow_start) + INTERVAL (FLOOR(date_part('hour', flow_start) / 6) * 6) HOUR"}
    ]
    
    all_scale_summaries = {}
    
    for cfg in configs:
        scale = cfg["scale"]
        trunc = cfg["trunc_expr"]
        print(f"Extracting aggregated edges for APEX at scale {scale}...")
        
        query = f"""
            SELECT 
                {trunc} as window_start,
                src_ip,
                dst_ip,
                COUNT(*) as flow_count
            FROM read_parquet('{APEX_PARQUET}')
            WHERE src_ip IS NOT NULL AND dst_ip IS NOT NULL
            GROUP BY 1, 2, 3
            ORDER BY 1, 2, 3
        """
        df_edges = con.execute(query).df()
        stats_df = compute_window_transition_stats(df_edges, "window_start")
        stats_df["dataset"] = "APEX-IDS2026"
        stats_df["time_scale"] = scale
        
        # Mark boundary partial windows
        stats_df["is_partial_boundary"] = False
        if len(stats_df) > 0:
            stats_df.loc[0, "is_partial_boundary"] = True
            stats_df.loc[len(stats_df) - 1, "is_partial_boundary"] = True
            
        out_csv = METRICS_DIR / f"apex_dynamics_{scale}.csv"
        stats_df.to_csv(out_csv, index=False)
        print(f"  Saved {len(stats_df)} window records to {out_csv}")
        
        # Mean stats (excluding first step which has no prior history)
        eval_transitions = stats_df.iloc[1:] if len(stats_df) > 1 else stats_df
        # Also compute non-boundary transitions
        non_boundary = eval_transitions[~eval_transitions["is_partial_boundary"]]
        
        all_scale_summaries[scale] = {
            "num_windows": len(stats_df),
            "mean_edges_per_window": float(stats_df["edges"].mean()),
            "mean_nodes_per_window": float(stats_df["nodes"].mean()),
            "mean_recurrence_rate": float(eval_transitions["recurrence_rate"].mean()),
            "std_recurrence_rate": float(eval_transitions["recurrence_rate"].std()),
            "mean_novelty_rate": float(eval_transitions["novelty_rate"].mean()),
            "std_novelty_rate": float(eval_transitions["novelty_rate"].std()),
            "mean_turnover_jaccard": float(eval_transitions["turnover_jaccard"].mean()),
            "std_turnover_jaccard": float(eval_transitions["turnover_jaccard"].std()),
            "mean_turnover_dice": float(eval_transitions["turnover_dice"].mean()),
            "std_turnover_dice": float(eval_transitions["turnover_dice"].std()),
            "mean_symmetric_turnover": float(eval_transitions["turnover_jaccard"].mean()),
            "std_symmetric_turnover": float(eval_transitions["turnover_jaccard"].std()),
            "mean_recurrence_non_boundary": float(non_boundary["recurrence_rate"].mean()) if len(non_boundary) > 0 else None,
            "mean_turnover_non_boundary": float(non_boundary["turnover_jaccard"].mean()) if len(non_boundary) > 0 else None
        }
        print(f"  [{scale}] Recurrence: {all_scale_summaries[scale]['mean_recurrence_rate']*100:.2f}% | Novelty: {all_scale_summaries[scale]['mean_novelty_rate']*100:.2f}% | Turnover (Jaccard): {all_scale_summaries[scale]['mean_turnover_jaccard']*100:.2f}% | Turnover (Dice): {all_scale_summaries[scale]['mean_turnover_dice']*100:.2f}%")
        
    with open(METRICS_DIR / "apex_multiscale_summary.json", "w") as fp:
        json.dump(all_scale_summaries, fp, indent=2)
    return all_scale_summaries


def analyze_cic():
    print("\n" + "=" * 70)
    print("Analyzing CIC-IDS2017 Multi-Scale Dynamics (1h, 6h, 24h)...")
    print("=" * 70)
    
    con = duckdb.connect()
    
    # Clean timestamp expression across formats
    ts_expr = """
        COALESCE(
            try_strptime(Timestamp, '%d/%m/%Y %H:%M:%S'),
            try_strptime(Timestamp, '%d/%m/%Y %H:%M'),
            try_strptime(Timestamp, '%m/%d/%Y %H:%M:%S'),
            try_strptime(Timestamp, '%m/%d/%Y %H:%M')
        )
    """
    
    configs = [
        {"scale": "24h", "trunc_expr": f"date_trunc('day', {ts_expr})"},
        {"scale": "6h", "trunc_expr": f"date_trunc('day', {ts_expr}) + INTERVAL (FLOOR(date_part('hour', {ts_expr}) / 6) * 6) HOUR"},
        {"scale": "1h", "trunc_expr": f"date_trunc('hour', {ts_expr})"}
    ]
    
    all_scale_summaries = {}
    
    for cfg in configs:
        scale = cfg["scale"]
        trunc = cfg["trunc_expr"]
        print(f"Extracting aggregated edges for CIC-IDS2017 at scale {scale}...")
        
        query = f"""
            SELECT 
                {trunc} as window_start,
                \"Source IP\" as src_ip,
                \"Destination IP\" as dst_ip,
                COUNT(*) as flow_count
            FROM read_csv('{CIC_CSV_GLOB}', header=True, ignore_errors=True)
            WHERE Timestamp IS NOT NULL AND \"Source IP\" IS NOT NULL AND \"Destination IP\" IS NOT NULL
            GROUP BY 1, 2, 3
            ORDER BY 1, 2, 3
        """
        df_edges = con.execute(query).df()
        # Drop any null window_start
        df_edges = df_edges.dropna(subset=['window_start'])
        
        stats_df = compute_window_transition_stats(df_edges, "window_start")
        stats_df["dataset"] = "CIC-IDS2017"
        stats_df["time_scale"] = scale
        
        out_csv = METRICS_DIR / f"cic_dynamics_{scale}.csv"
        stats_df.to_csv(out_csv, index=False)
        print(f"  Saved {len(stats_df)} window records to {out_csv}")
        
        eval_transitions = stats_df.iloc[1:] if len(stats_df) > 1 else stats_df
        
        all_scale_summaries[scale] = {
            "num_windows": len(stats_df),
            "mean_edges_per_window": float(stats_df["edges"].mean()),
            "mean_nodes_per_window": float(stats_df["nodes"].mean()),
            "mean_recurrence_rate": float(eval_transitions["recurrence_rate"].mean()),
            "std_recurrence_rate": float(eval_transitions["recurrence_rate"].std()),
            "mean_novelty_rate": float(eval_transitions["novelty_rate"].mean()),
            "std_novelty_rate": float(eval_transitions["novelty_rate"].std()),
            "mean_turnover_jaccard": float(eval_transitions["turnover_jaccard"].mean()),
            "std_turnover_jaccard": float(eval_transitions["turnover_jaccard"].std()),
            "mean_turnover_dice": float(eval_transitions["turnover_dice"].mean()),
            "std_turnover_dice": float(eval_transitions["turnover_dice"].std()),
            "mean_symmetric_turnover": float(eval_transitions["turnover_jaccard"].mean()),
            "std_symmetric_turnover": float(eval_transitions["turnover_jaccard"].std())
        }
        print(f"  [{scale}] Recurrence: {all_scale_summaries[scale]['mean_recurrence_rate']*100:.2f}% | Novelty: {all_scale_summaries[scale]['mean_novelty_rate']*100:.2f}% | Turnover (Jaccard): {all_scale_summaries[scale]['mean_turnover_jaccard']*100:.2f}% | Turnover (Dice): {all_scale_summaries[scale]['mean_turnover_dice']*100:.2f}%")
        
    with open(METRICS_DIR / "cic_multiscale_summary.json", "w") as fp:
        json.dump(all_scale_summaries, fp, indent=2)
    return all_scale_summaries


def main():
    apex_res = analyze_apex()
    cic_res = analyze_cic()
    print("\n" + "=" * 70)
    print("Multi-Scale Dynamics Analysis Complete.")
    print("Summary JSON and CSV artifacts saved in results/metrics/.")
    print("=" * 70)


if __name__ == "__main__":
    main()
