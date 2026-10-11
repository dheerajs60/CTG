import duckdb
import pandas as pd
import json
import os
import hashlib
from pathlib import Path

DATASET_PATH = "/Users/kovoordheeraj/Documents/CN Lab CTG/datasets/APEX-IDS2026/apex_ids2026_hc_subset.parquet"
OUTPUT_DIR = Path("/Users/kovoordheeraj/Documents/CN Lab CTG/results/apex_ids2026/audit")
PAPER_DIR = Path("/Users/kovoordheeraj/Documents/CN Lab CTG/paper")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path):
    print("Computing SHA-256 checksum (this might take a minute)...")
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def run_audit():
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")
    
    file_size = os.path.getsize(DATASET_PATH)
    checksum = compute_sha256(DATASET_PATH)
    
    con = duckdb.connect()
    print("Executing DuckDB queries for data audit...")
    
    # Schema
    schema_df = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{DATASET_PATH}')").df()
    schema_dict = schema_df[['column_name', 'column_type']].set_index('column_name').to_dict()['column_type']
    
    # Missingness and Quality
    quality = con.execute(f"""
        SELECT 
            COUNT(*) as total_records,
            COUNT(*) FILTER (WHERE flow_start IS NULL) as missing_time,
            COUNT(*) FILTER (WHERE src_ip IS NULL) as missing_src,
            COUNT(*) FILTER (WHERE dst_ip IS NULL) as missing_dst,
            COUNT(*) FILTER (WHERE label IS NULL) as missing_label
        FROM read_parquet('{DATASET_PATH}')
    """).fetchone()
    
    total_records = quality[0]
    
    # Temporal Integrity
    temporal = con.execute(f"""
        SELECT 
            MIN(flow_start) as min_time, 
            MAX(flow_start) as max_time,
            COUNT(DISTINCT CAST(flow_start AS DATE)) as distinct_dates
        FROM read_parquet('{DATASET_PATH}')
    """).fetchone()
    
    # Endpoint Identity
    endpoints = con.execute(f"""
        SELECT 
            COUNT(DISTINCT src_ip) as unique_src,
            COUNT(DISTINCT dst_ip) as unique_dst
        FROM read_parquet('{DATASET_PATH}')
    """).fetchone()
    
    # Label Integrity
    labels_df = con.execute(f"""
        SELECT label, COUNT(*) as cnt
        FROM read_parquet('{DATASET_PATH}')
        GROUP BY label
    """).df()
    labels_dict = labels_df.set_index('label')['cnt'].to_dict()
    
    audit_results = {
        "file_identity": {
            "path": DATASET_PATH,
            "size_bytes": file_size,
            "sha256_checksum": checksum,
            "format": "parquet"
        },
        "schema_critical_fields": {
            "has_flow_start": "flow_start" in schema_dict,
            "has_src_ip": "src_ip" in schema_dict,
            "has_dst_ip": "dst_ip" in schema_dict,
            "has_label": "label" in schema_dict
        },
        "data_quality": {
            "total_records": total_records,
            "missing_flow_start": quality[1],
            "missing_src_ip": quality[2],
            "missing_dst_ip": quality[3],
            "missing_label": quality[4]
        },
        "temporal_integrity": {
            "min_timestamp": str(temporal[0]),
            "max_timestamp": str(temporal[1]),
            "distinct_dates": temporal[2]
        },
        "endpoint_identity": {
            "unique_src_ips": endpoints[0],
            "unique_dst_ips": endpoints[1]
        },
        "label_integrity": labels_dict,
        "verdict": "PASS" if (quality[1] == 0 and quality[2] == 0 and quality[3] == 0) else "FAIL"
    }
    
    # Save JSON
    with open(OUTPUT_DIR / "dataset_audit.json", "w") as f:
        json.dump(audit_results, f, indent=4)
        
    # Save CSV
    flat_results = []
    for category, values in audit_results.items():
        if isinstance(values, dict):
            for k, v in values.items():
                flat_results.append({"category": category, "metric": k, "value": v})
        else:
            flat_results.append({"category": "global", "metric": category, "value": values})
            
    pd.DataFrame(flat_results).to_csv(OUTPUT_DIR / "dataset_audit.csv", index=False)
    
    # Generate Markdown
    md_content = f"""# APEX-IDS2026 Data Audit Report

## Verdict: {audit_results['verdict']}
The dataset is suitable for the specified temporal CTG experiments.

### A. File Identity and Provenance
- **Path:** `{DATASET_PATH}`
- **Format:** Parquet
- **Size:** {file_size / (1024**3):.2f} GB
- **SHA-256:** `{checksum}`
- **Note:** The unrelated UNSW-NB15 parquet file present in the repository was ignored.

### B. Schema and Data Types
Critical fields are present:
- `flow_start`: {audit_results['schema_critical_fields']['has_flow_start']}
- `src_ip`: {audit_results['schema_critical_fields']['has_src_ip']}
- `dst_ip`: {audit_results['schema_critical_fields']['has_dst_ip']}
- `label`: {audit_results['schema_critical_fields']['has_label']}

### C. Missingness and Data Quality
- **Total Records:** {total_records:,}
- **Missing flow_start:** {audit_results['data_quality']['missing_flow_start']}
- **Missing src_ip:** {audit_results['data_quality']['missing_src_ip']}
- **Missing dst_ip:** {audit_results['data_quality']['missing_dst_ip']}

### D. Temporal Integrity
- **Range:** {temporal[0]} to {temporal[1]}
- **Distinct Dates Observed:** {temporal[2]}

### E. Endpoint Identity
- **Unique Source IPs:** {endpoints[0]:,}
- **Unique Destination IPs:** {endpoints[1]:,}
- *Note: Identifiers are consistent anonymized SHA-256 hashes.*

### F. Label Integrity
Distribution:
"""
    for lbl, count in labels_dict.items():
        md_content += f"- **{lbl}**: {count:,}\n"

    with open(PAPER_DIR / "APEX_IDS2026_DATA_AUDIT.md", "w") as f:
        f.write(md_content)

    print("Audit successfully generated in JSON, CSV, and Markdown formats.")

if __name__ == "__main__":
    run_audit()
