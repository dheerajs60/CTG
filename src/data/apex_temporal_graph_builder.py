import duckdb
import os
import json
from pathlib import Path
import pandas as pd
from datetime import datetime

DATASET_PATH = "/Users/kovoordheeraj/Documents/CN Lab CTG/datasets/APEX-IDS2026/apex_ids2026_hc_subset.parquet"
OUTPUT_DIR = Path("/Users/kovoordheeraj/Documents/CN Lab CTG/results/apex_ids2026/graphs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

WINDOW_HOURS = 24  # 1-day windows to prevent disk/inode exhaustion on 69M rows

def build_temporal_graphs():
    con = duckdb.connect()
    print("Building temporal graphs from APEX-IDS2026...")
    
    # 1. Define the temporal windows
    # We will use date_trunc to group flows by day
    
    query = f"""
    WITH edges AS (
        SELECT 
            date_trunc('day', CAST(flow_start AS TIMESTAMP)) as window_id,
            src_ip, 
            dst_ip,
            COUNT(*) as flow_count,
            SUM(CASE WHEN label = 'Attack_Verified' THEN 1 ELSE 0 END) as attack_flows,
            SUM(CASE WHEN label = 'Benign_Verified' THEN 1 ELSE 0 END) as benign_flows
        FROM read_parquet('{DATASET_PATH}')
        GROUP BY 1, 2, 3
    )
    SELECT * FROM edges ORDER BY window_id, src_ip, dst_ip
    """
    
    print(f"Executing query with window size: {WINDOW_HOURS} hours...")
    
    # Export directly to partitioned CSV or parquet for memory efficiency
    edges_dir = OUTPUT_DIR / "edge_lists"
    edges_dir.mkdir(exist_ok=True)
    
    # Use DuckDB's COPY command to output partitioned by window
    export_query = f"""
    COPY (
        SELECT 
            strftime(date_trunc('day', CAST(flow_start AS TIMESTAMP)), '%Y-%m-%d') as window_id,
            src_ip, 
            dst_ip,
            COUNT(*) as weight,
            SUM(CASE WHEN label = 'Attack_Verified' THEN 1 ELSE 0 END) as attack_flows,
            SUM(CASE WHEN label = 'Benign_Verified' THEN 1 ELSE 0 END) as benign_flows
        FROM read_parquet('{DATASET_PATH}')
        GROUP BY 1, 2, 3
    ) TO '{edges_dir}' (FORMAT PARQUET, PARTITION_BY (window_id), OVERWRITE_OR_IGNORE 1);
    """
    
    con.execute(export_query)
    print(f"Edge lists successfully exported to {edges_dir}")
    
    # 2. Compute Graph Diagnostics
    print("Computing graph diagnostics...")
    diagnostics_query = f"""
    SELECT 
        strftime(date_trunc('day', CAST(flow_start AS TIMESTAMP)), '%Y-%m-%d') as window_id,
        COUNT(DISTINCT src_ip) as unique_sources,
        COUNT(DISTINCT dst_ip) as unique_destinations,
        COUNT(DISTINCT src_ip || '-' || dst_ip) as edge_count,
        COUNT(*) as total_raw_flows,
        SUM(CASE WHEN label = 'Attack_Verified' THEN 1 ELSE 0 END) as total_attack_flows,
        SUM(CASE WHEN label = 'Benign_Verified' THEN 1 ELSE 0 END) as total_benign_flows
    FROM read_parquet('{DATASET_PATH}')
    GROUP BY 1
    ORDER BY 1
    """
    
    diagnostics_df = con.execute(diagnostics_query).df()
    
    # Save diagnostics
    diagnostics_csv = OUTPUT_DIR / "graph_diagnostics.csv"
    diagnostics_df.to_csv(diagnostics_csv, index=False)
    
    # Metadata summary
    metadata = {
        "timestamp_generated": datetime.utcnow().isoformat(),
        "dataset_path": DATASET_PATH,
        "window_policy": f"{WINDOW_HOURS}_hours",
        "total_snapshots": len(diagnostics_df),
        "total_edges_across_time": int(diagnostics_df['edge_count'].sum()),
        "directed": True
    }
    
    with open(OUTPUT_DIR / "graph_metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)
        
    print(f"Graph construction complete. Generated {len(diagnostics_df)} snapshots.")
    print(f"Diagnostics saved to {diagnostics_csv}")

if __name__ == "__main__":
    build_temporal_graphs()
