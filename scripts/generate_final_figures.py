import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def save_fig(fig, path):
    fig.savefig(path + '.png', dpi=300, bbox_inches='tight')
    fig.savefig(path + '.pdf', bbox_inches='tight')
    fig.savefig(path + '.svg', bbox_inches='tight')
    plt.close(fig)

def main():
    print("Generating Final Publication Figures...")
    os.makedirs('figures/final_paper', exist_ok=True)
    
    # FIG 1: CTG Architecture
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis('off')
    
    # Draw architecture blocks
    # Validated
    boxes = [
        ("Real Datasets", 0.1, 0.8),
        ("Temporal Graph Construction", 0.4, 0.8),
        ("Genesis Transitions", 0.7, 0.8),
        ("EvolveGCN-H\n(Temporal Prediction)", 0.4, 0.5),
        ("Topology Anomaly Detection", 0.7, 0.5),
        ("Grammar Evolution", 0.1, 0.5)
    ]
    
    for text, x, y in boxes:
        ax.add_patch(plt.Rectangle((x-0.1, y-0.05), 0.25, 0.1, fill=True, color='lightblue', lw=1, ec='black'))
        ax.text(x+0.025, y, text, ha='center', va='center', fontsize=9, wrap=True)
        
    # Unvalidated
    unval_boxes = [
        ("Genesis Violation\n[UNVALIDATED]", 0.1, 0.2),
        ("RGAR\n[UNVALIDATED]", 0.4, 0.2),
        ("CGB\n[UNVALIDATED]", 0.7, 0.2),
        ("Adaptive Defense\n[UNVALIDATED]", 0.4, 0.0)
    ]
    
    for text, x, y in unval_boxes:
        ax.add_patch(plt.Rectangle((x-0.1, y-0.05), 0.25, 0.1, fill=True, color='lightgray', lw=1, ec='red', ls='--'))
        ax.text(x+0.025, y, text, ha='center', va='center', fontsize=9, wrap=True)
        
    # Arrows
    arrows = [
        (0.25, 0.8, 0.35, 0.8), # data -> graph
        (0.55, 0.8, 0.65, 0.8), # graph -> genesis
        (0.5, 0.75, 0.5, 0.55), # graph -> evolve
        (0.8, 0.75, 0.8, 0.55), # genesis -> anomaly
    ]
    for x1, y1, x2, y2 in arrows:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", lw=1.5))
        
    ax.set_title("Counterfactual Topology Genesis (CTG) Architecture", pad=20)
    save_fig(fig, 'figures/final_paper/fig01_ctg_architecture')
    
    # FIG 2: Temporal Topology
    df_temporal = pd.read_csv('results/metrics/cic_ids_temporal_changes.csv')
    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(df_temporal['Snapshot'], df_temporal['Node_Count'], 'b-', label='Node Count')
    ax1.set_xlabel('Chronological Snapshot (Time)')
    ax1.set_ylabel('Node Count', color='b')
    ax1.tick_params('y', colors='b')
    
    ax2 = ax1.twinx()
    ax2.plot(df_temporal['Snapshot'], df_temporal['Added_Edges'] + df_temporal['Removed_Edges'], 'r--', label='Total Topology Changes')
    ax2.set_ylabel('Total Topology Changes', color='r')
    ax2.tick_params('y', colors='r')
    
    fig.suptitle('CIC-IDS2017 Chronological Temporal Topology Evolution')
    save_fig(fig, 'figures/final_paper/fig02_temporal_topology')
    
    # FIG 3: Genesis Transitions
    df_trans = pd.read_csv('results/final_real/genesis_transitions.csv')
    # parse the lists lengths
    def list_len(s):
        import ast
        try:
            return len(ast.literal_eval(s))
        except:
            return 0
            
    df_trans['added_edges_count'] = df_trans['added_edges'].apply(list_len)
    df_trans['removed_edges_count'] = df_trans['removed_edges'].apply(list_len)
    df_trans['added_nodes_count'] = df_trans['added_nodes'].apply(list_len)
    df_trans['removed_nodes_count'] = df_trans['removed_nodes'].apply(list_len)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    x = df_trans['t_next']
    ax.plot(x, df_trans['added_edges_count'], label='Added Edges', marker='o')
    ax.plot(x, df_trans['removed_edges_count'], label='Removed Edges', marker='x')
    ax.plot(x, df_trans['added_nodes_count'], label='Added Nodes', marker='s')
    ax.plot(x, df_trans['removed_nodes_count'], label='Removed Nodes', marker='^')
    ax.set_xlabel('Transition Interval (t -> t+1)')
    ax.set_ylabel('Transition Count')
    ax.set_title('CIC-IDS2017 Genesis Transition Dynamics')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)
    save_fig(fig, 'figures/final_paper/fig03_genesis_transitions')
    
    # FIG 4: EvolveGCN vs Persistence
    df_evolve = pd.read_csv('results/final_real/topology_prediction_benchmark.csv')
    # Because the CSV is already aggregated (contains F1_mean, F1_std, etc)
    # We just need to read the specific row.
    evolve_row = df_evolve[df_evolve['Model'] == 'EvolveGCN-H'].iloc[0]
    pers_row = df_evolve[df_evolve['Model'] == 'Persistence Baseline'].iloc[0]
    
    metrics = ['F1', 'ROC-AUC', 'PR-AUC']
    evolve_means = [evolve_row[f'{m}_mean'] for m in metrics]
    evolve_stds = [evolve_row[f'{m}_std'] for m in metrics]
    pers_means = [pers_row[f'{m}_mean'] for m in metrics]
    pers_stds = [pers_row[f'{m}_std'] for m in metrics]
    
    x = np.arange(len(metrics))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(x - width/2, evolve_means, width, yerr=evolve_stds, label='EvolveGCN-H (CIC-IDS2017)', capsize=5)
    ax.bar(x + width/2, pers_means, width, yerr=pers_stds, label='Persistence Baseline (CIC-IDS2017)', capsize=5)
    
    ax.set_ylabel('Score')
    ax.set_title('Chronological Endpoint-level Topology Prediction Performance')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.legend(loc='lower right')
    ax.set_ylim([0, 1.0])
    save_fig(fig, 'figures/final_paper/fig04_evolvegcn_vs_persistence')
    
    # FIG 5: Topology Anomaly
    train_end = 4
    train_features = df_temporal['Added_Edges'].iloc[:train_end].values
    threshold = np.mean(train_features) + np.std(train_features)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df_temporal['Snapshot'], df_temporal['Added_Edges'], color=['red' if l == 1 else 'blue' for l in df_temporal['Is_Attack_Associated']])
    ax.axhline(y=threshold, color='black', linestyle='--', label=f'Learned Threshold ({threshold:.1f})')
    ax.set_xlabel('Chronological Snapshot')
    ax.set_ylabel('Added Edges Magnitude')
    ax.set_title('Attack-associated temporal topology anomaly detection (CIC-IDS2017)')
    ax.legend()
    # fake legends for color
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='blue', label='Benign Period'), Patch(facecolor='red', label='Attack-Associated Period')]
    ax.legend(handles=legend_elements + [ax.get_legend_handles_labels()[0][0]])
    save_fig(fig, 'figures/final_paper/fig05_topology_anomaly')
    
    # FIG 6: Grammar Evolution
    df_gram = pd.read_csv('results/final_real/grammar_metrics.csv')
    fig, ax = plt.subplots(figsize=(7, 5))
    categories = ['Legit Accepted', 'Legit Rejected', 'Malicious Accepted', 'Malicious Rejected']
    values = [df_gram['Legit_Accepted'].iloc[0], df_gram['Legit_Rejected'].iloc[0], 
              df_gram['Malicious_Accepted'].iloc[0], df_gram['Malicious_Rejected'].iloc[0]]
    colors = ['green', 'red', 'orange', 'purple']
    ax.bar(categories, values, color=colors)
    ax.set_ylabel('Count')
    ax.set_title('Topology Grammar Evolution Performance (CIC-IDS2017)')
    plt.xticks(rotation=45)
    save_fig(fig, 'figures/final_paper/fig06_grammar_evolution')
    
    # FIG 7: Two-Dataset Evaluation
    df_base = pd.read_csv('results/metrics/baseline_comparison.csv')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Panel 1: CIC Topology Prediction
    evolve_f1_mean = evolve_row['F1_mean']
    pers_f1_mean = pers_row['F1_mean']
    ax1.bar(['EvolveGCN-H', 'Persistence'], [evolve_f1_mean, pers_f1_mean], color=['skyblue', 'steelblue'])
    ax1.set_ylabel('Temporal Topology F1 Score')
    ax1.set_title('Task 1: Temporal Topology Prediction\nDataset: CIC-IDS2017')
    ax1.set_ylim([0, 1])
    
    # Panel 2: UNSW Flow Baseline
    ax2.bar(df_base['Model'], df_base['F1'], color=['lightcoral', 'indianred'])
    ax2.set_ylabel('Flow Classification F1 Score')
    ax2.set_title('Task 2: Flow-Level Classification Baseline\nDataset: UNSW-NB15')
    ax2.set_ylim([0, 1])
    
    plt.suptitle('Two-Dataset Scientific Boundaries (Incompatible Metrics Handled Independently)', fontsize=14)
    save_fig(fig, 'figures/final_paper/fig07_two_dataset_evaluation')
    
    # Generate APEX-IDS2026 figures
    try:
        import generate_apex_figures
        generate_apex_figures.main()
    except Exception as e:
        print(f"Note: APEX figure generation encountered: {e}")

    print("All figures successfully generated.")

if __name__ == "__main__":
    main()
