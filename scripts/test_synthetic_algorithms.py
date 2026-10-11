import torch
import pandas as pd
import os
import networkx as nx
from detection.rgar import ReverseGenesisAttackReconstructor
from detection.cgb import CounterfactualGenesisBarrier
from models.genesis_engine import TopologyGrammarEngine

def create_synthetic_graphs():
    # G1: Base graph
    edges1 = [(0,1), (1,2), (2,3)]
    edge_idx1 = torch.tensor(edges1, dtype=torch.long).t().contiguous()
    g1 = {'edge_index': edge_idx1, 'nodes': 4}
    
    # G2: Attack trajectory (add edges 0->3, remove 1->2)
    edges2 = [(0,1), (2,3), (0,3)]
    edge_idx2 = torch.tensor(edges2, dtype=torch.long).t().contiguous()
    g2 = {'edge_index': edge_idx2, 'nodes': 4}
    
    return g1, g2

def run_tests():
    os.makedirs('results/metrics', exist_ok=True)
    g1, g2 = create_synthetic_graphs()
    
    # 1. Test RGAR
    print("Testing RGAR...")
    rgar = ReverseGenesisAttackReconstructor(max_search_depth=10)
    path, metrics = rgar.reconstruct_path(g1, g2)
    
    # True edits: Add (0,3) or (3,0), Remove (1,2) or (2,1)
    print("RGAR Path Found:", path)
    
    rgar_df = pd.DataFrame([{
        'reconstruction_success': metrics['reconstruction_success'],
        'path_length': metrics['path_length'],
        'search_expansions': metrics['search_expansions']
    }])
    rgar_df.to_csv('results/metrics/rgar_synthetic_benchmark.csv', index=False)
    
    # 2. Test CGB
    print("Testing CGB...")
    cgb = CounterfactualGenesisBarrier(lambda_collateral=1.0, mu_residual=1.0)
    intervention = cgb.find_minimal_intervention(g2)
    
    print("CGB Intervention Recommended:", intervention)
    
    cgb_df = pd.DataFrame([{
        'intervention_found': intervention is not None,
        'cost': intervention['cost'] if intervention else None,
        'collateral': intervention['collateral'] if intervention else None
    }])
    cgb_df.to_csv('results/metrics/cgb_synthetic_benchmark.csv', index=False)
    
    # 3. Test Grammar Evolution
    print("Testing Grammar Evolution & Rollback...")
    grammar = TopologyGrammarEngine()
    grammar.learn_from_training([g1, g2]) # Learn initial rules
    initial_grammar = set(grammar.grammar)
    
    # Accept valid rule
    acc, rej = grammar.evolve_grammar(["ADD_NEW_EDGE"], validation_score=0.9, threshold=0.8)
    assert acc == 1
    assert "ADD_NEW_EDGE" in grammar.grammar
    
    # Reject invalid rule
    acc2, rej2 = grammar.evolve_grammar(["MALICIOUS_EDGE"], validation_score=0.4, threshold=0.8)
    assert rej2 == 1
    assert "MALICIOUS_EDGE" not in grammar.grammar
    
    # Rollback
    rollback_success = grammar.rollback()
    assert rollback_success
    assert grammar.grammar == initial_grammar
    print("Grammar Rollback logic verified.")
    
    print("Saved all synthetic benchmarks and verified logic.")

if __name__ == '__main__':
    run_tests()
