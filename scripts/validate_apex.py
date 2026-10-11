import duckdb
import os
import pandas as pd

file_path = "/Users/kovoordheeraj/Documents/CN Lab CTG/datasets/APEX-IDS2026/apex_ids2026_hc_subset.parquet"
output_dir = "/Users/kovoordheeraj/Documents/CN Lab CTG/results/apex_ids2026"
os.makedirs(output_dir, exist_ok=True)
output_csv = os.path.join(output_dir, "dataset_statistics.csv")

try:
    con = duckdb.connect()
    
    # Check total records
    total_records = con.execute(f"SELECT COUNT(*) FROM read_parquet('{file_path}')").fetchone()[0]
    
    # Check schema
    schema = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{file_path}')").df()
    columns = schema['column_name'].tolist()
    
    # Check timestamp range
    time_stats = con.execute(f"""
        SELECT 
            MIN(flow_start) as min_time, 
            MAX(flow_start) as max_time 
        FROM read_parquet('{file_path}')
    """).fetchone()
    
    # Check missing values for critical fields
    missing_stats = con.execute(f"""
        SELECT 
            COUNT(*) FILTER (WHERE flow_start IS NULL) as missing_time,
            COUNT(*) FILTER (WHERE src_ip IS NULL) as missing_src_ip,
            COUNT(*) FILTER (WHERE dst_ip IS NULL) as missing_dst_ip,
            COUNT(*) FILTER (WHERE label IS NULL) as missing_label
        FROM read_parquet('{file_path}')
    """).fetchone()
    
    # Check unique endpoints (are hashes consistent?)
    unique_endpoints = con.execute(f"""
        SELECT 
            COUNT(DISTINCT src_ip) as unique_src,
            COUNT(DISTINCT dst_ip) as unique_dst
        FROM read_parquet('{file_path}')
    """).fetchone()
    
    # Check label distribution
    labels = con.execute(f"""
        SELECT label, COUNT(*) as cnt 
        FROM read_parquet('{file_path}') 
        GROUP BY label
    """).df()
    
    # Check temporal gaps (by grouping flows per day)
    gaps = con.execute(f"""
        SELECT CAST(flow_start AS DATE) as date, COUNT(*) as flow_count
        FROM read_parquet('{file_path}')
        GROUP BY 1
        ORDER BY 1
    """).df()
    
    # Write stats to CSV
    stats = []
    stats.append({"metric": "total_records", "value": total_records})
    stats.append({"metric": "min_timestamp", "value": str(time_stats[0])})
    stats.append({"metric": "max_timestamp", "value": str(time_stats[1])})
    stats.append({"metric": "missing_flow_start", "value": missing_stats[0]})
    stats.append({"metric": "missing_src_ip", "value": missing_stats[1]})
    stats.append({"metric": "missing_dst_ip", "value": missing_stats[2]})
    stats.append({"metric": "missing_label", "value": missing_stats[3]})
    stats.append({"metric": "unique_src_ips", "value": unique_endpoints[0]})
    stats.append({"metric": "unique_dst_ips", "value": unique_endpoints[1]})
    stats.append({"metric": "total_columns", "value": len(columns)})
    
    for _, row in labels.iterrows():
        stats.append({"metric": f"label_{row['label']}", "value": row['cnt']})
        
    stats.append({"metric": "distinct_days", "value": len(gaps)})
    
    pd.DataFrame(stats).to_csv(output_csv, index=False)
    
    print("Validation complete.")
    print(f"Total Records: {total_records}")
    print(f"Time Range: {time_stats[0]} to {time_stats[1]}")
    print(f"Columns: {len(columns)} found.")
    print("Labels:")
    print(labels)
    print("\nMissing values:", missing_stats)

except Exception as e:
    print(f"Error: {e}")
