import matplotlib.pyplot as plt
import pandas as pd
import os

def main():
    print("Generating CIC-IDS2017 real anomaly plots...")
    os.makedirs('results/figures', exist_ok=True)
    
    # Temporal changes
    if os.path.exists('results/metrics/cic_ids_temporal_changes.csv'):
        df = pd.read_csv('results/metrics/cic_ids_temporal_changes.csv')
        df.plot(x='Snapshot', y=['Added_Edges', 'Removed_Edges'], kind='bar')
        plt.title('Topology Structural Changes over Time')
        plt.ylabel('Edge Count')
        plt.tight_layout()
        plt.savefig('results/figures/fig_cic_ids_structural_changes.png')
        plt.close()
        
    # Anomaly Detection (GV Real)
    if os.path.exists('results/metrics/cic_ids_gv_real.csv'):
        df = pd.read_csv('results/metrics/cic_ids_gv_real.csv')
        df.plot(x='Model', y=['F1', 'Precision', 'Recall'], kind='bar')
        plt.title('Attack-Associated Topology Anomaly Detection')
        plt.ylim(0, 1.0)
        plt.tight_layout()
        plt.savefig('results/figures/fig_cic_ids_anomaly.png')
        plt.close()
        
    # Grammar Evolution
    if os.path.exists('results/metrics/cic_ids_grammar_real.csv'):
        df = pd.read_csv('results/metrics/cic_ids_grammar_real.csv')
        df.iloc[0].plot(kind='bar')
        plt.title('Real Grammar Evolution Acceptance')
        plt.ylabel('Edge Count')
        plt.tight_layout()
        plt.savefig('results/figures/fig_cic_ids_grammar_real.png')
        plt.close()
        
    print("Generated real experimental figures.")

if __name__ == "__main__":
    main()
