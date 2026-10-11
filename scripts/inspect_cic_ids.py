import os
import pandas as pd
import hashlib
import json
import glob
import sys

def get_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath,"rb") as f:
        for byte_block in iter(lambda: f.read(4096),b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    print("Inspecting CIC-IDS2017 dataset...")
    base_dir = "datasets/cic_ids2017/TrafficLabelling "
    files = glob.glob(f"{base_dir}/*.csv")
    
    manifest = {
        "source_archive": "GeneratedLabelledFlows.zip",
        "files": [],
        "time_range": {"min": None, "max": None},
        "label_distribution": {},
        "missing_value_statistics": 0,
        "total_row_count": 0,
        "unique_timestamps": 0,
        "unique_source_ips": 0,
        "unique_dest_ips": 0,
        "columns": []
    }
    
    all_timestamps = set()
    all_src_ips = set()
    all_dst_ips = set()
    global_min_ts = None
    global_max_ts = None
    
    for f in files:
        print(f"Processing {os.path.basename(f)}...")
        size = os.path.getsize(f)
        sha = get_sha256(f)
        
        df = pd.read_csv(f, encoding='latin1', low_memory=False)
        df.columns = df.columns.str.strip()
        
        rows = len(df)
        if not manifest["columns"]:
            manifest["columns"] = list(df.columns)
            
        manifest["total_row_count"] += rows
        manifest["missing_value_statistics"] += int(df.isnull().sum().sum())
        
        labels = df['Label'].value_counts().to_dict()
        for k, v in labels.items():
            if k in manifest["label_distribution"]:
                manifest["label_distribution"][k] += int(v)
            else:
                manifest["label_distribution"][k] = int(v)
                
        if 'Timestamp' in df.columns:
            ts = pd.to_datetime(df['Timestamp'], errors='coerce')
            ts_dropped = ts.dropna()
            
            all_timestamps.update(ts_dropped.unique())
            
            if len(ts_dropped) > 0:
                local_min = ts_dropped.min()
                local_max = ts_dropped.max()
                if global_min_ts is None or local_min < global_min_ts:
                    global_min_ts = local_min
                if global_max_ts is None or local_max > global_max_ts:
                    global_max_ts = local_max

        if 'Source IP' in df.columns:
            all_src_ips.update(df['Source IP'].dropna().unique())
        if 'Destination IP' in df.columns:
            all_dst_ips.update(df['Destination IP'].dropna().unique())
            
        manifest["files"].append({
            "filename": os.path.basename(f),
            "size": size,
            "sha256": sha,
            "row_count": rows,
            "columns": list(df.columns)
        })
        
    manifest["time_range"]["min"] = str(global_min_ts) if global_min_ts is not None else None
    manifest["time_range"]["max"] = str(global_max_ts) if global_max_ts is not None else None
    manifest["unique_timestamps"] = len(all_timestamps)
    manifest["unique_source_ips"] = len(all_src_ips)
    manifest["unique_dest_ips"] = len(all_dst_ips)
    
    os.makedirs('results/manifests', exist_ok=True)
    with open("results/manifests/cic_ids2017_manifest.json", "w") as out:
        json.dump(manifest, out, indent=4)
        
    print("Generated manifest at results/manifests/cic_ids2017_manifest.json")
    
    # Validation tests
    if manifest["time_range"]["min"] is None or manifest["time_range"]["max"] is None:
        print("TEST FAILED: Timestamp column exists but min/max are null.")
        sys.exit(1)
        
    expected_rows = sum([f["row_count"] for f in manifest["files"]])
    if manifest["total_row_count"] != expected_rows:
        print("TEST FAILED: Row count mismatch.")
        sys.exit(1)
        
    if "Source IP" not in manifest["columns"] or "Destination IP" not in manifest["columns"]:
        print("TEST FAILED: Required endpoint columns are missing.")
        sys.exit(1)

    print("ALL VALIDATION TESTS PASSED.")

if __name__ == "__main__":
    main()
