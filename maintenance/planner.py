import csv
from collections import defaultdict
import os

def main():
    inventory = []
    with open('maintenance/WORKSPACE_INVENTORY.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            inventory.append(row)
            
    hashes = defaultdict(list)
    empty_files = []
    caches_and_pyc = []
    duplicates = []
    
    for row in inventory:
        p = row['Path']
        h = row['Hash']
        size = int(row['Size'])
        
        if '__pycache__' in p or p.endswith('.pyc') or '.pytest_cache' in p:
            caches_and_pyc.append(p)
            continue
            
        if size == 0:
            empty_files.append(p)
            continue
            
        hashes[h].append(p)
        
    for h, paths in hashes.items():
        if len(paths) > 1:
            duplicates.append(paths)
            
    with open('maintenance/CLEANUP_PLAN.md', 'w') as f:
        f.write("# Cleanup Plan\n\n")
        
        f.write("## 1. Caches & Temporary Files (To Delete)\n")
        for p in caches_and_pyc:
            f.write(f"- {p}\n")
            
        f.write("\n## 2. Empty Files (To Review/Delete)\n")
        for p in empty_files:
            f.write(f"- {p}\n")
            
        f.write("\n## 3. Duplicates (To Review/Deduplicate)\n")
        for group in duplicates:
            f.write("- Duplicate Group:\n")
            for p in group:
                f.write(f"  - {p}\n")

if __name__ == '__main__':
    main()
