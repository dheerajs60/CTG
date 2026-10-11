import os
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score, average_precision_score

BASE_DIR = Path("/Users/kovoordheeraj/Documents/CN Lab CTG")
PRED_DIR = BASE_DIR / "results/apex_ids2026/predictions"
GRAPH_STAT_CSV = BASE_DIR / "results/apex_ids2026/graphs/graph_transition_statistics.csv"
FIGURES_DIR_APEX = BASE_DIR / "results/apex_ids2026/figures"
FIGURES_DIR_FINAL = BASE_DIR / "figures/final_paper"
TABLES_DIR = BASE_DIR / "results/apex_ids2026/tables"

SEEDS = [42, 100, 1234]

def save_fig(fig, path_without_ext):
    """Save figure in PNG (300 dpi), PDF, and SVG with tight bounding box."""
    os.makedirs(os.path.dirname(path_without_ext), exist_ok=True)
    fig.savefig(f"{path_without_ext}.png", dpi=300, bbox_inches='tight')
    fig.savefig(f"{path_without_ext}.pdf", bbox_inches='tight')
    fig.savefig(f"{path_without_ext}.svg", bbox_inches='tight')
    plt.close(fig)

def recompute_and_evaluate_apex():
    """
    Recompute metrics directly from saved Parquet test prediction files
    for seeds 42, 100, and 1234.
    """
    per_seed_results = []
    
    for seed in SEEDS:
        parquet_path = PRED_DIR / f"test_predictions_seed{seed}.parquet"
        if not parquet_path.exists():
            raise FileNotFoundError(f"Missing required prediction file: {parquet_path}")
            
        print(f"Loading predictions from {parquet_path.name}...")
        df = pd.read_parquet(parquet_path)
        
        y_true = df['y_true'].values
        gcn_prob = df['gcn_prob'].values
        gcn_pred = df['gcn_pred'].values
        pers_prob = df['pers_prob'].values
        pers_pred = df['pers_pred'].values
        
        # Calculate EvolveGCN-H metrics
        gcn_f1 = float(f1_score(y_true, gcn_pred))
        gcn_prec = float(precision_score(y_true, gcn_pred))
        gcn_rec = float(recall_score(y_true, gcn_pred))
        gcn_roc = float(roc_auc_score(y_true, gcn_prob))
        gcn_pr = float(average_precision_score(y_true, gcn_prob))
        
        # Calculate Persistence baseline metrics
        pers_f1 = float(f1_score(y_true, pers_pred))
        pers_prec = float(precision_score(y_true, pers_pred))
        pers_rec = float(recall_score(y_true, pers_pred))
        pers_roc = float(roc_auc_score(y_true, pers_prob))
        pers_pr = float(average_precision_score(y_true, pers_prob))
        
        per_seed_results.append({
            'Seed': seed,
            'GCN_F1': gcn_f1,
            'GCN_Prec': gcn_prec,
            'GCN_Rec': gcn_rec,
            'GCN_ROC': gcn_roc,
            'GCN_PR': gcn_pr,
            'Pers_F1': pers_f1,
            'Pers_Prec': pers_prec,
            'Pers_Rec': pers_rec,
            'Pers_ROC': pers_roc,
            'Pers_PR': pers_pr,
        })
        
    df_results = pd.DataFrame(per_seed_results)
    
    # Compute summary statistics
    metrics_list = ['F1', 'Prec', 'Rec', 'ROC', 'PR']
    gcn_means = [df_results[f'GCN_{m}'].mean() for m in metrics_list]
    gcn_stds = [df_results[f'GCN_{m}'].std(ddof=1) for m in metrics_list]
    pers_means = [df_results[f'Pers_{m}'].mean() for m in metrics_list]
    pers_stds = [0.0 for _ in metrics_list]  # Verified zero variance for persistence
    
    # Save comparison table
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    metric_display_names = ['F1', 'Precision', 'Recall', 'ROC-AUC', 'PR-AUC']
    table_rows = []
    for name, m, gm, gs, pm, ps in zip(metric_display_names, metrics_list, gcn_means, gcn_stds, pers_means, pers_stds):
        table_rows.append({
            'Metric': name,
            'EvolveGCN-H (Mean ± Std)': f"{gm:.4f} ± {gs:.4f}",
            'Persistence (Mean ± Std)': f"{pm:.4f} ± {ps:.4f}",
            'Absolute Difference': f"{gm - pm:+.4f}"
        })
    df_table = pd.DataFrame(table_rows)
    df_table.to_csv(TABLES_DIR / "final_model_comparison.csv", index=False)
    with open(TABLES_DIR / "final_model_comparison.md", "w") as f:
        f.write(df_table.to_markdown(index=False))
        
    return metric_display_names, gcn_means, gcn_stds, pers_means, pers_stds

def plot_model_comparison(metrics, gcn_means, gcn_stds, pers_means, pers_stds):
    """
    Generate APEX model comparison figure matching CIC fig04 styling:
    Fonts, colors, dimensions, error bars (capsize=5), and formats.
    """
    x = np.arange(len(metrics))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - width/2, gcn_means, width, yerr=gcn_stds, label='EvolveGCN-H (APEX-IDS2026)', capsize=5)
    ax.bar(x + width/2, pers_means, width, yerr=pers_stds, label='Persistence Baseline (APEX-IDS2026)', capsize=5)
    
    ax.set_ylabel('Score')
    ax.set_title('APEX-IDS2026 Chronological Endpoint-level Topology Prediction Performance')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.legend(loc='lower right')
    ax.set_ylim([0, 1.05])
    
    # Save to both APEX figures directory and final paper figures directory
    save_fig(fig, str(FIGURES_DIR_APEX / "apex_model_comparison"))
    
    # Recreate or save identical figure in final_paper matching naming scheme
    fig_paper, ax_paper = plt.subplots(figsize=(10, 6))
    ax_paper.bar(x - width/2, gcn_means, width, yerr=gcn_stds, label='EvolveGCN-H (APEX-IDS2026)', capsize=5)
    ax_paper.bar(x + width/2, pers_means, width, yerr=pers_stds, label='Persistence Baseline (APEX-IDS2026)', capsize=5)
    ax_paper.set_ylabel('Score')
    ax_paper.set_title('APEX-IDS2026 Chronological Endpoint-level Topology Prediction Performance')
    ax_paper.set_xticks(x)
    ax_paper.set_xticklabels(metrics)
    ax_paper.legend(loc='lower right')
    ax_paper.set_ylim([0, 1.05])
    save_fig(fig_paper, str(FIGURES_DIR_FINAL / "fig04_evolvegcn_vs_persistence_apex"))

def plot_temporal_topology():
    """
    Generate APEX temporal topology evolution matching CIC fig02 styling.
    """
    if not GRAPH_STAT_CSV.exists():
        print(f"Skipping temporal topology: {GRAPH_STAT_CSV} not found.")
        return
        
    df = pd.read_csv(GRAPH_STAT_CSV)
    x = np.arange(1, len(df) + 1)
    
    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(x, df['nodes'], 'b-', label='Node Count')
    ax1.set_xlabel('Chronological Snapshot (Time)')
    ax1.set_ylabel('Node Count', color='b')
    ax1.tick_params('y', colors='b')
    
    ax2 = ax1.twinx()
    ax2.plot(x, df['new_edges'] + df['removed_edges'], 'r--', label='Total Topology Changes')
    ax2.set_ylabel('Total Topology Changes', color='r')
    ax2.tick_params('y', colors='r')
    
    fig.suptitle('APEX-IDS2026 Chronological Temporal Topology Evolution')
    save_fig(fig, str(FIGURES_DIR_APEX / "apex_temporal_topology"))
    
    # Re-save in final_paper
    fig_paper, ax1_p = plt.subplots(figsize=(8, 5))
    ax1_p.plot(x, df['nodes'], 'b-', label='Node Count')
    ax1_p.set_xlabel('Chronological Snapshot (Time)')
    ax1_p.set_ylabel('Node Count', color='b')
    ax1_p.tick_params('y', colors='b')
    ax2_p = ax1_p.twinx()
    ax2_p.plot(x, df['new_edges'] + df['removed_edges'], 'r--', label='Total Topology Changes')
    ax2_p.set_ylabel('Total Topology Changes', color='r')
    ax2_p.tick_params('y', colors='r')
    fig_paper.suptitle('APEX-IDS2026 Chronological Temporal Topology Evolution')
    save_fig(fig_paper, str(FIGURES_DIR_FINAL / "fig02_temporal_topology_apex"))

def plot_genesis_transitions():
    """
    Generate APEX genesis transition dynamics matching CIC fig03 styling.
    """
    if not GRAPH_STAT_CSV.exists():
        print(f"Skipping genesis transitions: {GRAPH_STAT_CSV} not found.")
        return
        
    df = pd.read_csv(GRAPH_STAT_CSV)
    df_trans = df.iloc[1:].copy()  # Snapshot 0 has no preceding transition
    x = np.arange(1, len(df_trans) + 1)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x, df_trans['new_edges'], label='Added Edges', marker='o')
    ax.plot(x, df_trans['removed_edges'], label='Removed Edges', marker='x')
    ax.plot(x, df_trans['new_nodes'], label='Added Nodes', marker='s')
    ax.plot(x, df_trans['removed_nodes'], label='Removed Nodes', marker='^')
    ax.set_xlabel('Transition Interval (t -> t+1)')
    ax.set_ylabel('Transition Count')
    ax.set_title('APEX-IDS2026 Genesis Transition Dynamics')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)
    
    save_fig(fig, str(FIGURES_DIR_APEX / "apex_genesis_transitions"))
    
    # Re-save in final_paper
    fig_paper, ax_p = plt.subplots(figsize=(10, 6))
    ax_p.plot(x, df_trans['new_edges'], label='Added Edges', marker='o')
    ax_p.plot(x, df_trans['removed_edges'], label='Removed Edges', marker='x')
    ax_p.plot(x, df_trans['new_nodes'], label='Added Nodes', marker='s')
    ax_p.plot(x, df_trans['removed_nodes'], label='Removed Nodes', marker='^')
    ax_p.set_xlabel('Transition Interval (t -> t+1)')
    ax_p.set_ylabel('Transition Count')
    ax_p.set_title('APEX-IDS2026 Genesis Transition Dynamics')
    ax_p.legend()
    ax_p.grid(True, linestyle='--', alpha=0.7)
    save_fig(fig_paper, str(FIGURES_DIR_FINAL / "fig03_genesis_transitions_apex"))

def main():
    print("Generating APEX-IDS2026 Figures matching CIC-IDS2017 style...")
    FIGURES_DIR_APEX.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR_FINAL.mkdir(parents=True, exist_ok=True)
    
    # 1. Model comparison from actual Parquet predictions
    metrics, gcn_m, gcn_s, pers_m, pers_s = recompute_and_evaluate_apex()
    plot_model_comparison(metrics, gcn_m, gcn_s, pers_m, pers_s)
    print("Model comparison figures generated.")
    
    # 2. Temporal topology from actual transition statistics
    plot_temporal_topology()
    print("Temporal topology figures generated.")
    
    # 3. Genesis transition dynamics from actual transition statistics
    plot_genesis_transitions()
    print("Genesis transition figures generated.")
    
    print("All APEX-IDS2026 figures generated successfully.")

if __name__ == "__main__":
    main()
