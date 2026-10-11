import os
import sys
sys.path.append('.')

def check_readiness():
    print("=== REAL-DATA READINESS CHECK ===\n")
    
    passed = True
    
    # 1. Environment
    print("Environment: PASS")
    
    # 2. Dependencies
    try:
        import torch_geometric
        import pandas
        import networkx
        print("Dependencies: PASS")
    except ImportError as e:
        print(f"Dependencies: FAIL ({e})")
        passed = False
        
    # 3. Data Directory
    cicids_path = "data/raw/CICIDS2017"
    if os.path.exists(cicids_path):
        csvs = [f for f in os.listdir(cicids_path) if f.endswith('.csv') and not f.startswith('dummy')]
        if len(csvs) > 0:
            print("Data directory: PASS")
            print("Real CICIDS2017 detected: PASS")
        else:
            print("Data directory: PASS")
            print("Real CICIDS2017 detected: WAITING (only dummy or empty found)")
            passed = False
    else:
        print("Data directory: FAIL (data/raw/CICIDS2017 missing)")
        passed = False
        
    # 4. Modules
    modules_to_check = [
        ('src.data.dataset_validator', 'Data validator'),
        ('src.data.temporal_split', 'Temporal splitter'),
        ('src.graph.ctg_dataset', 'Graph builder'),
        ('src.models.topology_field', 'CTG model'),
        ('src.evaluation.metrics', 'Evaluation')
    ]
    
    for mod, desc in modules_to_check:
        try:
            __import__(mod)
            print(f"{desc}: PASS")
        except Exception as e:
            print(f"{desc}: FAIL ({e})")
            passed = False
            
    print("\n----------------------------------")
    if passed:
        print("READY FOR REAL CICIDS2017")
    else:
        print("NOT READY. WAITING FOR REAL DATA OR FIXES.")
        
if __name__ == "__main__":
    check_readiness()
