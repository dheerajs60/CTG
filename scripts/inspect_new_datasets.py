import os
import glob
import pandas as pd
import zipfile
import json

DATASET_ROOT = "/Users/kovoordheeraj/Documents/CN Lab CTG/datasets"

def safe_read_csv(filepath, nrows=5):
    try:
        return pd.read_csv(filepath, nrows=nrows)
    except Exception as e:
        return None

def inspect_datasets():
    datasets = os.listdir(DATASET_ROOT)
    
    report = []
    
    for d in datasets:
        if d.startswith('.'):
            continue
        d_path = os.path.join(DATASET_ROOT, d)
        if not os.path.isdir(d_path):
            continue
            
        print(f"Inspecting {d}...")
        
        # Recursively list all files
        all_files = []
        for root, _, files in os.walk(d_path):
            for f in files:
                if not f.startswith('.'):
                    all_files.append(os.path.join(root, f))
                    
        total_size = sum(os.path.getsize(f) for f in all_files)
        
        info = {
            "name": d,
            "total_files": len(all_files),
            "total_size_mb": total_size / (1024 * 1024),
            "csv_files": [f for f in all_files if f.endswith('.csv')],
            "pcap_files": [f for f in all_files if f.endswith('.pcap') or f.endswith('.pcapng')],
            "zip_files": [f for f in all_files if f.endswith('.zip')],
            "readme": [f for f in all_files if 'readme' in f.lower()],
            "columns": set(),
            "has_timestamp": False,
            "has_src": False,
            "has_dst": False,
            "has_label": False
        }
        
        # Check first CSV if available
        if info["csv_files"]:
            df = safe_read_csv(info["csv_files"][0])
            if df is not None:
                cols = [c.lower() for c in df.columns]
                info["columns"] = cols
                if any('time' in c for c in cols): info["has_timestamp"] = True
                if any('src' in c for c in cols): info["has_src"] = True
                if any('dst' in c for c in cols): info["has_dst"] = True
                if any('label' in c or 'attack' in c for c in cols): info["has_label"] = True
                
        # For CTU specifically inspect inside zips
        if 'CTU' in d:
            for zf in info['zip_files']:
                if 'CTU-IDSEVAL-6-summary.csv' in zf:
                    # just noting it exists
                    pass
                    
        report.append(info)
        
    with open('dataset_inspection_report.json', 'w') as f:
        # Convert sets to lists
        for r in report:
            r['columns'] = list(r['columns'])
        json.dump(report, f, indent=4)

if __name__ == "__main__":
    inspect_datasets()
