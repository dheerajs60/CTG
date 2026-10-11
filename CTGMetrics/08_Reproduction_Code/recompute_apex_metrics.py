import pandas as pd
from pathlib import Path
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score, average_precision_score

PRED_DIR = Path("results/apex_ids2026/predictions")

def recompute_metrics():
    seeds = [42, 100, 1234]
    
    print("Recomputing metrics from raw prediction files...")
    for seed in seeds:
        f = PRED_DIR / f"test_predictions_seed{seed}.parquet"
        if not f.exists():
            print(f"Missing {f}")
            continue
            
        df = pd.read_parquet(f)
        
        y_true = df['y_true']
        gcn_prob = df['gcn_prob']
        gcn_pred = df['gcn_pred']
        
        pers_prob = df['pers_prob']
        pers_pred = df['pers_pred']
        
        print(f"\n--- Seed {seed} ---")
        print("EvolveGCN-H:")
        print(f"  F1: {f1_score(y_true, gcn_pred):.4f}")
        print(f"  Precision: {precision_score(y_true, gcn_pred):.4f}")
        print(f"  Recall: {recall_score(y_true, gcn_pred):.4f}")
        print(f"  ROC-AUC: {roc_auc_score(y_true, gcn_prob):.4f}")
        print(f"  PR-AUC: {average_precision_score(y_true, gcn_prob):.4f}")
        
        print("Persistence:")
        print(f"  F1: {f1_score(y_true, pers_pred):.4f}")
        print(f"  Precision: {precision_score(y_true, pers_pred):.4f}")
        print(f"  Recall: {recall_score(y_true, pers_pred):.4f}")
        print(f"  ROC-AUC: {roc_auc_score(y_true, pers_prob):.4f}")
        print(f"  PR-AUC: {average_precision_score(y_true, pers_prob):.4f}")

if __name__ == "__main__":
    recompute_metrics()
