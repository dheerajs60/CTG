import pandas as pd
import json
import os

def main():
    print("Generating Data Quality Report for UNSW-NB15...")
    
    train_file = "UNSW_NB15_training-set.csv"
    test_file = "UNSW_NB15_testing-set(in).csv"
    
    if not os.path.exists(train_file) or not os.path.exists(test_file):
        print("UNSW-NB15 datasets not found. Skipping report.")
        return
        
    df_train = pd.read_csv(train_file)
    df_test = pd.read_csv(test_file)
    
    report = {
        "dataset_name": "UNSW-NB15",
        "provenance": "Local CSV files",
        "train_set": {
            "row_count": len(df_train),
            "normal_count": int((df_train['label'] == 0).sum()),
            "attack_count": int((df_train['label'] == 1).sum()),
            "missing_values": int(df_train.isnull().sum().sum()),
            "endpoint_coverage": "Proxy only (derived signatures, no explicit IP)"
        },
        "test_set": {
            "row_count": len(df_test),
            "normal_count": int((df_test['label'] == 0).sum()),
            "attack_count": int((df_test['label'] == 1).sum()),
            "missing_values": int(df_test.isnull().sum().sum()),
            "endpoint_coverage": "Proxy only (derived signatures, no explicit IP)"
        },
        "limitations": [
            "Lacks true temporal chronological causality (records are pre-shuffled in public release).",
            "Lacks host-level IP addresses; network nodes are simulated via flow signatures.",
            "Lacks ground-truth topological attack sequences for RGAR evaluation."
        ]
    }
    
    os.makedirs('results/manifests', exist_ok=True)
    with open("results/manifests/unsw_nb15_quality_report.json", "w") as f:
        json.dump(report, f, indent=4)
        
    print("Data quality report generated at results/manifests/unsw_nb15_quality_report.json")

if __name__ == "__main__":
    main()
