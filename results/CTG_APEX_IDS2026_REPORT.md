============================================================
CTG — APEX-IDS2026 PRIMARY BENCHMARK EVALUATION
Dataset: APEX-IDS2026 (Enterprise / Hybrid Cloud Multi-Week)
============================================================

[Dataset analysis]
Dataset name             : APEX-IDS2026
Records                  : 69,107,018
Features                 : 53
Benign Flows             : 26,901,115
Attack Flows             : 42,205,903
Attack Ratio             : 61.07%
Distinct Collection Days : 44 (Continuous: 2026-06-21 to 2026-08-03)
Unique Endpoints         : 412,906 Sources, 42,421 Destinations

[Graph statistics]
Raw Snapshots Evaluated  : 44 daily graph snapshots
Total Edges Across Time  : 8,951,536 directed endpoint edges
Mean Daily Edge Turnover : ~55.9% (Heavy graph churn)

[EvolveGCN-H vs. Persistence Baseline (Test Evaluation - 3 Seeds: 42, 100, 1234)]
Metric                   | EvolveGCN-H (Mean) | Persistence Baseline | Gain / Difference
----------------------------------------------------------------------------------------
F1 Score                 | 0.9125             | 0.7700               | +0.1425
Precision                | 0.9317             | 0.9998               | -0.0681
Recall                   | 0.8941             | 0.6260               | +0.2681
ROC-AUC                  | 0.9705             | 0.8130               | +0.1575
PR-AUC                   | 0.9716             | 0.8129               | +0.1587
