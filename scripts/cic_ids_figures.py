import matplotlib.pyplot as plt
import pandas as pd
import os

def main():
    print("Generating CIC-IDS2017 plots...")
    os.makedirs('results/figures', exist_ok=True)
    
    if os.path.exists('results/metrics/cic_ids_graph_statistics.csv'):
        # Fix file name if I misnamed it in the previous script. Let's assume 'cic_ids2017_graph_statistics.csv'
        pass

    if os.path.exists('results/metrics/cic_ids2017_graph_statistics.csv'):
        df = pd.read_csv('results/metrics/cic_ids2017_graph_statistics.csv')
        
        # Plot 1: Nodes and Edges over time
        df.plot(x='Snapshot', y=['Total Nodes', 'Total Edges'], kind='line', marker='o')
        plt.title('CIC-IDS2017 Topology Growth Over Time')
        plt.ylabel('Count')
        plt.tight_layout()
        plt.savefig('results/figures/fig_cic_ids_topology_growth.png')
        plt.close()
        
        # Plot 2: Attack vs Benign flows
        df.plot(x='Snapshot', y=['Benign Flows', 'Attack Flows'], kind='bar', stacked=True)
        plt.title('CIC-IDS2017 Flow Label Distribution per Snapshot')
        plt.ylabel('Flow Count')
        plt.tight_layout()
        plt.savefig('results/figures/fig_cic_ids_label_dist.png')
        plt.close()
        
        print("Generated figures successfully.")

if __name__ == "__main__":
    main()
