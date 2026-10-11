import os
import shutil
import csv
from pathlib import Path

ROOT = Path('.')
ARCHIVE = ROOT / 'archive' / 'cleanup_backup'
LOG_FILE = ROOT / 'maintenance' / 'CLEANUP_LOG.md'
CSV_FILE = ROOT / 'maintenance' / 'CLEANUP_MANIFEST.csv'

def setup():
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'w') as f:
        f.write("# Cleanup Log\n\n")
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Action', 'Original Path', 'Destination', 'Reason'])

def log_action(action, orig, dest, reason):
    with open(LOG_FILE, 'a') as f:
        f.write(f"- **{action}**: `{orig}` -> `{dest}` ({reason})\n")
    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([action, orig, dest, reason])

def safe_remove(p, reason):
    if not os.path.exists(p): return
    dest = ARCHIVE / str(p).replace('/', '_')
    if os.path.isdir(p):
        shutil.move(str(p), str(dest))
    else:
        shutil.move(str(p), str(dest))
    log_action('ARCHIVE_REMOVE', str(p), str(dest), reason)

def execute_plan():
    setup()
    
    inventory = []
    with open('maintenance/WORKSPACE_INVENTORY.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            inventory.append(row)
            
    # 1. Caches
    for row in inventory:
        p = row['Path']
        if '__pycache__' in p or '.pytest_cache' in p or p.endswith('.pyc'):
            safe_remove(p, "Disposable cache or bytecode")
            
    # 2. Empty files
    for row in inventory:
        p = row['Path']
        if int(row['Size']) == 0:
            if not p.endswith('__init__.py') and not p.endswith('.gitkeep'):
                safe_remove(p, "Empty file without recognized purpose")
                
    # 3. Duplicates
    from collections import defaultdict
    hashes = defaultdict(list)
    for row in inventory:
        p = row['Path']
        if not os.path.exists(p): continue # Already removed
        if row['Size'] == '0': continue
        hashes[row['Hash']].append(p)
        
    for h, paths in hashes.items():
        if len(paths) > 1:
            # We want to keep one canonical path.
            # Priority:
            # 1. Not in CTG_FINAL_AUDIT
            # 2. Not in CTGpaper
            # 3. Not in root TrafficLabelling
            
            def score(p):
                s = 0
                if 'CTG_FINAL_AUDIT' in p: s -= 100
                if 'CTGpaper' in p: s -= 50
                if p.startswith('TrafficLabelling'): s -= 50
                if 'archive' in p: s -= 10
                return s
                
            paths_sorted = sorted(paths, key=score, reverse=True)
            canonical = paths_sorted[0]
            
            for dup in paths_sorted[1:]:
                safe_remove(dup, f"Exact duplicate of {canonical}")

    # Remove empty dirs
    for root_dir, dirs, files in os.walk(ROOT, topdown=False):
        if '.git' in root_dir or 'maintenance' in root_dir or 'archive' in root_dir:
            continue
        try:
            if not os.listdir(root_dir):
                os.rmdir(root_dir)
                log_action('REMOVE_DIR', root_dir, 'None', 'Empty directory')
        except:
            pass

if __name__ == '__main__':
    execute_plan()
