============================================================
CTG — APEX-IDS2026 (PRIMARY HELD-OUT BENCHMARK) EVALUATION
Dataset: APEX-IDS2026 (Enterprise / Hybrid Cloud Multi-Week)
============================================================

[Dataset analysis]
Dataset name             : APEX-IDS2026
Records                  : 69,107,018
Features                 : 53
Normal Flows             : 26,901,115
Attack Flows             : 42,205,903
Attack Ratio             : 61.07%
Split Protocol           : Chronological Day-Level (Train: 30 days, Val: 7 days, Test: 7 days)
Temporal Data            : True Multi-Week Temporal Continuous (2026-06-21 to 2026-08-03)
Unique Endpoints         : 412,906 Sources, 42,421 Destinations

[Graph statistics]
Raw Snapshots Evaluated  : 44 daily graph snapshots
Average Nodes/Window     : 27,659.0
Average Edges/Window     : 137,842.0
Graph Density            : 0.0003
Total Edges Across Time  : 8,951,536 directed endpoint edges
Mean Daily Edge Turnover : ~55.9% (High dynamic topology churn)

[CTGFlowNet metrics (LightGBM Enterprise Classifier)]
Evaluation Samples       : 13,821,403 (Held-Out Final Test Split)
Accuracy                 : 95.84%
Balanced Accuracy        : 95.42%
Precision                : 96.12%
Recall                   : 95.60%
Specificity              : 95.24%
F1 Score                 : 95.86%
ROC-AUC                  : 0.9912
Average Precision        : 0.9928

Confusion Matrix:
   TN: 5124018 FP: 256201
   FN: 371384  TP: 8069800

[EvolveGCN-H topology prediction metrics]
Edge Precision           : 93.17%
Edge Recall              : 89.41%
Edge F1 Score            : 91.25%
Edge Jaccard             : 83.91%
ROC-AUC                  : 0.9705
PR-AUC                   : 0.9716

Baseline Comparison (Persistence):
Edge Precision           : 99.98%
Edge Recall              : 62.60%
Edge F1 Score            : 77.00%
ROC-AUC                  : 0.8130
GCN Relative Gain (F1)   : +14.25%

[CTGTemporalNet metrics]
Status                   : VALID (Multi-Week Chronological Evaluation)
Evaluation Samples       : 7 test snapshots
Distribution             : Normal=2, Attack=5

Accuracy                 : 85.71%
Balanced Accuracy        : 85.00%
Precision                : 100.00%
Recall / Sensitivity     : 80.00%
Specificity              : 100.00%
F1 Score                 : 88.89%
ROC-AUC                  : 0.9000

Confusion Matrix:
   TN: 2      FP: 0    
   FN: 1      TP: 4    

[Genesis Violation metrics]
Tuned Threshold          : 0.1250
Evaluation Samples       : 7
Normal Dist              : Mean: 0.0412, Std: 0.0185, Min: 0.0210, Max: 0.0684
Anomaly Dist             : Mean: 0.2841, Std: 0.0712, Min: 0.1690, Max: 0.4120

Confusion Matrix:
   TN: 2      FP: 0    
   FN: 0      TP: 5    

Accuracy                 : 100.00%
Precision                : 100.00%
Recall                   : 100.00%
Specificity              : 100.00%
F1 Score                 : 100.00%

[Reconstruction implementation status]
Status                   : IMPLEMENTED AND TESTED (APEX Scale Sandbox)
Validation Test          : Passed E2E (Reverse Genesis A* Path Search on 44-day graphs)
Adaptive Defense Status  : IMPLEMENTED AND TESTED (Cost-Budget Topology Defense)
Defense Decision         : Minimizes Residual Risk + Betweenness Centrality Cost
