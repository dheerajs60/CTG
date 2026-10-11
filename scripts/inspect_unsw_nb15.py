import os
import json
import pandas as pd
from data.loader import DataLoader

def main():
    loader = DataLoader(data_dir=".")
    df_train, df_test = loader.load_unsw_nb15()
    df = pd.concat([df_train, df_test])
    
    # Check for fields
    columns = list(df.columns)
    
    has_source_ip = 'srcip' in columns
    has_dest_ip = 'dstip' in columns
    has_timestamp = 'stime' in columns or 'ltime' in columns
    has_labels = 'label' in columns or 'attack_cat' in columns
    
    # Check chronological
    is_chronological = False
    if has_timestamp:
        # Check if naturally sorted
        time_col = 'stime' if 'stime' in columns else 'ltime'
        is_chronological = df[time_col].is_monotonic_increasing
    
    capability = {
        "dataset": "UNSW-NB15",
        "has_source_endpoint": has_source_ip,
        "has_destination_endpoint": has_dest_ip,
        "has_timestamp": has_timestamp,
        "is_chronologically_ordered": bool(is_chronological),
        "has_attack_labels": has_labels,
        "supports_temporal_topology": has_source_ip and has_dest_ip and has_timestamp,
        "supports_flow_classification": has_labels
    }
    
    os.makedirs("results/final_real", exist_ok=True)
    with open("results/final_real/unsw_nb15_capability_report.json", "w") as f:
        json.dump(capability, f, indent=4)
        
    print("UNSW-NB15 Capability Report Generated.")

if __name__ == "__main__":
    main()
