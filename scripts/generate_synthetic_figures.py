import matplotlib.pyplot as plt
import pandas as pd
import os

def main():
    print("Generating synthetic benchmark plots...")
    os.makedirs('results/figures', exist_ok=True)
    
    # GV Detector
    if os.path.exists('results/metrics/gv_detector_benchmark.csv'):
        df = pd.read_csv('results/metrics/gv_detector_benchmark.csv')
        df.plot(x='Model', y=['F1', 'ROC_AUC'], kind='bar')
        plt.title('Genesis Violation Detector (Synthetic)')
        plt.ylabel('Score')
        plt.ylim(0, 1.0)
        plt.tight_layout()
        plt.savefig('results/figures/fig_gv_synthetic.png')
        plt.close()
        print("Generated fig_gv_synthetic.png")
        
    # Topology Prediction
    if os.path.exists('results/metrics/topology_prediction_benchmark.csv'):
        df = pd.read_csv('results/metrics/topology_prediction_benchmark.csv')
        # Fill NaN for plotting
        df.fillna(0, inplace=True)
        df.plot(x='Model', y=['F1', 'ROC_AUC'], kind='bar')
        plt.title('Topology Prediction Baseline (EvolveGCN=Incomplete)')
        plt.ylabel('Score')
        plt.ylim(0, 1.0)
        plt.tight_layout()
        plt.savefig('results/figures/fig_topology_synthetic.png')
        plt.close()
        print("Generated fig_topology_synthetic.png")
        
    # Grammar Evolution
    if os.path.exists('results/metrics/grammar_evolution_benchmark.csv'):
        df = pd.read_csv('results/metrics/grammar_evolution_benchmark.csv')
        df.iloc[0].plot(kind='bar')
        plt.title('Grammar Evolution Acceptance vs Rejection')
        plt.ylabel('Count')
        plt.tight_layout()
        plt.savefig('results/figures/fig_grammar_synthetic.png')
        plt.close()
        print("Generated fig_grammar_synthetic.png")

if __name__ == "__main__":
    main()
