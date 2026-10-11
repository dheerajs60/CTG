import matplotlib.pyplot as plt
import pandas as pd
import os

def main():
    print("Generating EvolveGCN-H vs Persistence plots...")
    os.makedirs('results/figures', exist_ok=True)
    
    if os.path.exists('results/metrics/topology_prediction_benchmark.csv'):
        df = pd.read_csv('results/metrics/topology_prediction_benchmark.csv')
        
        # Plot just the means if std is problematic
        cols = [c for c in df.columns if 'ROC-AUC' in c or 'PR-AUC' in c or 'F1' in c]
        means = [c for c in cols if 'mean' in c] or ['ROC-AUC', 'PR-AUC', 'F1']
        
        ax = df.plot(x='Model', y=means, kind='bar')
        plt.title('EvolveGCN-H vs Persistence Baseline')
        plt.ylabel('Score')
        plt.ylim(0, 1.0)
        plt.xticks(rotation=0)
        plt.tight_layout()
        plt.savefig('results/figures/fig_evolvegcn_persistence.png')
        plt.close()
        print("Saved results/figures/fig_evolvegcn_persistence.png")

if __name__ == "__main__":
    main()
