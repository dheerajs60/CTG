import pandas as pd

def generate_tables():
    output_lines = ["# Final Publication Tables\n"]
    
    # Table 1: Dataset Capability Comparison
    output_lines.append("## Table 1: Dataset Capability Comparison\n")
    output_lines.append("| Capability | CIC-IDS2017 | UNSW-NB15 | Scientific use |")
    output_lines.append("|---|---|---|---|")
    output_lines.append("| Real data | YES | YES | YES |")
    output_lines.append("| Source endpoint | YES | NO | Required for temporal topology |")
    output_lines.append("| Destination endpoint | YES | NO | Required for temporal topology |")
    output_lines.append("| Timestamp | YES | NO | Required for chronological ordering |")
    output_lines.append("| Chronological topology | YES | NO | CIC-IDS2017 uniquely supports this |")
    output_lines.append("| Attack labels | YES | YES | YES (Both datasets) |")
    output_lines.append("| Temporal topology prediction | YES | NO | CIC-IDS2017 specific |")
    output_lines.append("| Flow-level Baseline | YES | YES | Independent baseline evaluation |")
    output_lines.append("| CGB/RGAR | NO | NO | UNVALIDATED |\n")
    
    # Table 2: CIC-IDS2017 temporal topology statistics
    df_temporal = pd.read_csv('results/metrics/cic_ids_temporal_changes.csv')
    mean_nodes = df_temporal['Node_Count'].mean()
    mean_edges = df_temporal['Added_Edges'].mean()
    output_lines.append("## Table 2: CIC-IDS2017 temporal topology statistics (Averages per snapshot)\n")
    output_lines.append("| Metric | Value |")
    output_lines.append("|---|---|")
    output_lines.append(f"| Average Node Count | {mean_nodes:.1f} |")
    output_lines.append(f"| Average Added Edges | {mean_edges:.1f} |\n")
    
    # Table 3: EvolveGCN-H vs persistence
    df_evolve = pd.read_csv('results/final_real/topology_prediction_benchmark.csv')
    evolve = df_evolve[df_evolve['Model'] == 'EvolveGCN-H'].iloc[0]
    pers = df_evolve[df_evolve['Model'] == 'Persistence Baseline'].iloc[0]
    output_lines.append("## Table 3: EvolveGCN-H vs persistence (CIC-IDS2017)\n")
    output_lines.append("| Model | F1 (Mean ± Std) | ROC-AUC (Mean ± Std) | PR-AUC (Mean ± Std) |")
    output_lines.append("|---|---|---|---|")
    output_lines.append(f"| EvolveGCN-H | {evolve['F1_mean']:.4f} ± {evolve['F1_std']:.4f} | {evolve['ROC-AUC_mean']:.4f} ± {evolve['ROC-AUC_std']:.4f} | {evolve['PR-AUC_mean']:.4f} ± {evolve['PR-AUC_std']:.4f} |")
    output_lines.append(f"| Persistence Baseline | {pers['F1_mean']:.4f} ± {pers['F1_std']:.4f} | {pers['ROC-AUC_mean']:.4f} ± {pers['ROC-AUC_std']:.4f} | {pers['PR-AUC_mean']:.4f} ± {pers['PR-AUC_std']:.4f} |\n")
    
    # Table 4: Topology anomaly results
    output_lines.append("## Table 4: Topology anomaly results\n")
    output_lines.append("*(See Figure 5 for temporal mapping of anomaly threshold bounding)*\n")
    
    # Table 5: Grammar results
    df_grammar = pd.read_csv('results/final_real/grammar_metrics.csv')
    output_lines.append("## Table 5: Grammar results (CIC-IDS2017)\n")
    output_lines.append("| Legit Accepted | Legit Rejected | Malicious Accepted | Malicious Rejected |")
    output_lines.append("|---|---|---|---|")
    output_lines.append(f"| {df_grammar['Legit_Accepted'].iloc[0]} | {df_grammar['Legit_Rejected'].iloc[0]} | {df_grammar['Malicious_Accepted'].iloc[0]} | {df_grammar['Malicious_Rejected'].iloc[0]} |\n")
    
    # Table 6: UNSW-NB15 flow-level baseline results
    df_base = pd.read_csv('results/metrics/baseline_comparison.csv')
    output_lines.append("## Table 6: UNSW-NB15 flow-level baseline results\n")
    output_lines.append("| Model | F1 Score | Accuracy |")
    output_lines.append("|---|---|---|")
    for _, row in df_base.iterrows():
        output_lines.append(f"| {row['Model']} | {row['F1']:.4f} | {row['Accuracy']:.4f} |")
    output_lines.append("\n")
    
    # Table 7: Engine validation status
    output_lines.append("## Table 7: Engine validation status\n")
    output_lines.append("| Engine | Real-data execution | Empirical validation |")
    output_lines.append("|---|---|---|")
    output_lines.append("| Temporal Graph | ✓ | Validated |")
    output_lines.append("| EvolveGCN-H | ✓ | Validated |")
    output_lines.append("| Topology Anomaly | ✓ | Validated |")
    output_lines.append("| Grammar Evolution | ✓ | Validated |")
    output_lines.append("| Genesis Violation | Limited | Unvalidated |")
    output_lines.append("| RGAR | Interface only | Unvalidated |")
    output_lines.append("| CGB | Interface only | Unvalidated |")
    output_lines.append("| Adaptive Defense | Interface only | Unvalidated |")
    
    with open('paper/PUBLICATION_TABLES.md', 'w') as f:
        f.write('\n'.join(output_lines))
        
    print("Tables generated from artifacts.")

if __name__ == "__main__":
    generate_tables()
