import os
import hashlib
import csv
from pathlib import Path
from datetime import datetime

ROOT = Path('.')
MAINTENANCE = ROOT / 'maintenance'

def get_hash(filepath):
    try:
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return ""

def is_ignored(p):
    parts = p.parts
    return '.git' in parts or 'maintenance' in parts or 'venv' in parts or '.pytest_cache' in parts or '__pycache__' in parts

def main():
    inventory = []
    
    for root, dirs, files in os.walk(ROOT):
        root_path = Path(root)
        if '.git' in root_path.parts or 'maintenance' in root_path.parts:
            continue
            
        for f in files:
            p = root_path / f
            if p.is_symlink():
                continue
                
            stat = p.stat()
            size = stat.st_size
            mtime = datetime.fromtimestamp(stat.st_mtime).isoformat()
            ext = p.suffix
            h = get_hash(p) if size > 0 else "EMPTY"
            
            inventory.append({
                'Path': str(p),
                'Size': size,
                'Ext': ext,
                'Modified': mtime,
                'Hash': h,
            })
            
    with open(MAINTENANCE / 'WORKSPACE_INVENTORY.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Path', 'Size', 'Ext', 'Modified', 'Hash'])
        writer.writeheader()
        writer.writerows(inventory)
        
if __name__ == '__main__':
    main()
