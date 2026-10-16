import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import numpy as np
import pandas as pd
import joblib
import torch
import networkx as nx

from main import compute_metrics, count_classes
from detection.genesis_violation import compute_topology_metrics, calculate_gv_score
from sklearn.metrics import accuracy_score, confusion_matrix

def test_compute_metrics():
    # Test correct calculation from confusion matrices
    y_true = [0, 0, 1, 1, 1, 1, 0, 0]
    y_pred = [0, 1, 1, 1, 0, 1, 0, 0]
    # TN: 3, FP: 1 (0 predicted as 1)
    # FN: 1 (1 predicted as 0), TP: 3
    # Acc: 6/8 = 75%
    metrics = compute_metrics(y_true, y_pred)
    assert metrics['acc'] == 75.0
    assert metrics['cm'][0, 0] == 3
    assert metrics['cm'][0, 1] == 1
    assert metrics['cm'][1, 0] == 1
    assert metrics['cm'][1, 1] == 3
    
    # Test one class partition handling
    y_true_one_class = [1, 1, 1]
    y_pred_one_class = [1, 0, 1]
    m_one = compute_metrics(y_true_one_class, y_pred_one_class)
    assert m_one['spec'] == "NOT EVALUABLE"
    assert m_one['bacc'] == "NOT EVALUABLE"

def test_gv_score_calculations():
    # Test GV calculation
    preds = np.array([1, 0, 1, 0])
    targets = np.array([1, 1, 0, 0])
    # pos_edge_index length is 2 (targets == 1 is index 0 and 1)
    pos_edge_index = torch.tensor([[0, 1], [1, 2]])
    neg_edge_index = torch.tensor([[2, 3], [3, 0]])
    
    ev, deg_d, den_d, u_rt, m_rt = compute_topology_metrics(preds, targets, pos_edge_index, neg_edge_index, 4)
    # preds: 1, 0, 1, 0
    # targets: 1, 1, 0, 0
    # intersection: 1 (index 0)
    # union: 2 + 2 - 1 = 3
    # Jaccard = 1/3, EV = 2/3
    assert np.isclose(ev, 2/3)
    
    gv = calculate_gv_score(ev, deg_d, den_d, u_rt, m_rt)
    assert gv > 0

def test_checkpoints_loaded():
    assert os.path.exists('results/checkpoints/lgbm_flownet.joblib')
    assert os.path.exists('results/checkpoints/scaler.joblib')
    assert os.path.exists('results/checkpoints/label_encoders.joblib')
    assert os.path.exists('results/checkpoints/features_schema.joblib')
    assert os.path.exists('results/checkpoints/thresholds.joblib')
    
    scaler = joblib.load('results/checkpoints/scaler.joblib')
    features = joblib.load('results/checkpoints/features_schema.joblib')
    # Preprocessing is fit on train data
    assert len(features) == 42
    
def test_reproducible_predictions():
    # Load dataset 2 and verify identical predictions to baseline in isolated subprocess
    # (avoiding macOS Python 3.13 OpenMP segfault under pytest harness)
    import subprocess, sys
    code = """
import joblib, pandas as pd, numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix
df_test = pd.read_csv('UNSW_NB15_testing-set(in).csv')
clf = joblib.load('results/checkpoints/lgbm_flownet.joblib')
clf.set_params(n_jobs=1)
scaler = joblib.load('results/checkpoints/scaler.joblib')
features = joblib.load('results/checkpoints/features_schema.joblib')
label_encoders = joblib.load('results/checkpoints/label_encoders.joblib')
X_test_df = df_test[features].copy()
for c in ['proto', 'service', 'state']:
    le = label_encoders[c]
    test_vals = X_test_df[c].astype(str).map(lambda s: s if s in le.classes_ else '<unknown>')
    X_test_df[c] = le.transform(test_vals)
X_test_scaled = pd.DataFrame(scaler.transform(X_test_df), columns=X_test_df.columns)
preds = clf.predict(X_test_scaled)
acc = accuracy_score(df_test['label'].values, preds) * 100
assert np.isclose(acc, 91.3156, atol=1e-2)
cm = confusion_matrix(df_test['label'].values, preds)
assert cm[0,0] == 31290
assert cm[0,1] == 5710
assert cm[1,0] == 1440
assert cm[1,1] == 43892
print('PASS')
"""
    r = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True)
    assert r.returncode == 0, f"Subprocess failed with stderr:\n{r.stderr}"
    assert "PASS" in r.stdout

