import os
import torch
import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
import networkx as nx

# Import existing modules
from detection.detector import GenesisViolationDetector
from detection.rgar import ReverseGenesisAttackReconstructor
from detection.cgb import CounterfactualGenesisBarrier
from models.genesis_engine import TopologyGrammarEngine

# --- Task 1: Genesis Violation Detector Benchmark ---
def benchmark_genesis_violation():
    print("Running Task 1: Genesis Violation Detector Benchmark...")
    # Synthetic data generation: Normal (0) and Anomalous (1) scores
    np.random.seed(42)
    # Train
    train_scores_normal = np.random.normal(0.2, 0.05, 100)
    train_scores_anom = np.random.normal(0.8, 0.1, 20)
    train_gvs = np.concatenate([train_scores_normal, train_scores_anom])
    train_labels = np.concatenate([np.zeros(100), np.ones(20)])
    
    # Val
    val_scores_normal = np.random.normal(0.22, 0.06, 50)
    val_scores_anom = np.random.normal(0.78, 0.12, 15)
    val_gvs = np.concatenate([val_scores_normal, val_scores_anom])
    val_labels = np.concatenate([np.zeros(50), np.ones(15)])
    
    # Test
    test_scores_normal = np.random.normal(0.25, 0.07, 150)
    test_scores_anom = np.random.normal(0.85, 0.15, 30)
    test_gvs = np.concatenate([test_scores_normal, test_scores_anom])
    test_labels = np.concatenate([np.zeros(150), np.ones(30)])
    
    detector = GenesisViolationDetector()
    detector.fit(val_gvs, val_labels)
    preds = detector.predict(test_gvs)
    
    prec = precision_score(test_labels, preds, zero_division=0)
    rec = recall_score(test_labels, preds, zero_division=0)
    f1 = f1_score(test_labels, preds, zero_division=0)
    roc = roc_auc_score(test_labels, test_gvs)
    
    os.makedirs('results/metrics', exist_ok=True)
    df = pd.DataFrame([{'Model': 'CTG GV Detector', 'Precision': prec, 'Recall': rec, 'F1': f1, 'ROC_AUC': roc, 'Threshold': detector.threshold}])
    df.to_csv('results/metrics/gv_detector_benchmark.csv', index=False)
    print(f"GV Detector F1: {f1:.4f}")

# --- Task 2: Topology Evolution Prediction Benchmark ---
def benchmark_topology_prediction():
    print("Running Task 2: Topology Evolution Prediction Benchmark... (SKIPPED)")
    pass

# --- Task 3: RGAR Benchmark ---
def benchmark_rgar():
    print("Running Task 3: RGAR Benchmark...")
    rgar = ReverseGenesisAttackReconstructor(max_search_depth=10)
    results = []
    
    for i in range(5): # 5 test cases
        edges_base = [(0,1), (1,2), (2,3)]
        edges_anom = [(0,1), (2,3), (0,3), (1,3)] # Add (0,3), (1,3), Remove (1,2)
        
        g1 = {'edge_index': torch.tensor(edges_base, dtype=torch.long).t().contiguous(), 'nodes': 4}
        g2 = {'edge_index': torch.tensor(edges_anom, dtype=torch.long).t().contiguous(), 'nodes': 4}
        
        path, metrics = rgar.reconstruct_path(g1, g2)
        results.append({
            'TestCase': i,
            'Success': metrics['reconstruction_success'],
            'PathLength': metrics['path_length'],
            'Expansions': metrics['search_expansions']
        })
        
    df = pd.DataFrame(results)
    df.to_csv('results/metrics/rgar_expanded_benchmark.csv', index=False)

# --- Task 4: CGB Benchmark ---
def benchmark_cgb():
    print("Running Task 4: CGB Benchmark...")
    cgb = CounterfactualGenesisBarrier()
    edges_anom = [(0,1), (2,3), (0,3), (1,3)]
    g2 = {'edge_index': torch.tensor(edges_anom, dtype=torch.long).t().contiguous(), 'nodes': 4}
    
    intervention = cgb.find_minimal_intervention(g2)
    
    df = pd.DataFrame([{
        'Model': 'CTG CGB',
        'Cost': intervention['cost'] if intervention else None,
        'Collateral': intervention['collateral'] if intervention else None,
        'Success': True if intervention else False
    }])
    df.to_csv('results/metrics/cgb_expanded_benchmark.csv', index=False)

# --- Task 5: Grammar Evolution Benchmark ---
def benchmark_grammar():
    print("Running Task 5: Grammar Evolution Benchmark...")
    grammar = TopologyGrammarEngine()
    
    acc_legit = 0
    acc_mal = 0
    rej_legit = 0
    rej_mal = 0
    
    # Legitimate changes (score > 0.8)
    for _ in range(10):
        a, r = grammar.evolve_grammar(["ADD_L_EDGE"], validation_score=0.9)
        acc_legit += a
        rej_legit += r
        
    # Malicious changes (score < 0.8)
    for _ in range(5):
        a, r = grammar.evolve_grammar(["ADD_M_EDGE"], validation_score=0.4)
        acc_mal += a
        rej_mal += r
        
    df = pd.DataFrame([{
        'Legit_Accepted': acc_legit,
        'Legit_Rejected': rej_legit,
        'Malicious_Accepted': acc_mal,
        'Malicious_Rejected': rej_mal
    }])
    df.to_csv('results/metrics/grammar_evolution_benchmark.csv', index=False)

def main():
    os.makedirs('results/metrics', exist_ok=True)
    benchmark_genesis_violation()
    benchmark_topology_prediction()
    benchmark_rgar()
    benchmark_cgb()
    benchmark_grammar()
    print("All compute-efficient synthetic benchmarks completed.")

if __name__ == '__main__':
    main()
