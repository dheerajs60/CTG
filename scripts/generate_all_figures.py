import matplotlib.pyplot as plt
import pandas as pd
import os

def main():
    print("Generating publication plots from REAL data...")
    os.makedirs('results/figures', exist_ok=True)
    
    # Dataset Distribution
    if os.path.exists('results/metrics/dataset_distribution.csv'):
        df = pd.read_csv('results/metrics/dataset_distribution.csv')
        df.set_index('Split').plot(kind='bar', stacked=True)
        plt.title('Dataset Class Distribution')
        plt.ylabel('Count')
        plt.tight_layout()
        plt.savefig('results/figures/fig02_dataset_distribution.png')
        plt.close()
        print("Generated fig02_dataset_distribution.png")
        
    # Baseline Comparison
    if os.path.exists('results/metrics/baseline_comparison.csv'):
        df = pd.read_csv('results/metrics/baseline_comparison.csv')
        df.plot(x='Model', y=['Accuracy', 'F1'], kind='bar')
        plt.title('CTG vs Baselines')
        plt.ylabel('Score')
        plt.ylim(0, 1.0)
        plt.tight_layout()
        plt.savefig('results/figures/fig16_baseline_comparison.png')
        plt.close()
        print("Generated fig16_baseline_comparison.png")
        
    print("All figures generated based on actual available data.")

if __name__ == "__main__":
    main()
