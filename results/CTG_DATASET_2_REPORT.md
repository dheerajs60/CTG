============================================================
CTG — DATASET 2 (HELD-OUT TEST SET) EVALUATION
Dataset: UNSW_NB15_testing-set(in).csv
============================================================

[Dataset analysis]
Dataset name             : UNSW_NB15_testing-set(in).csv
Records                  : 82332
Features                 : 42
Normal Flows             : 37000
Attack Flows             : 45332
Attack Ratio             : 55.06%
Split Protocol           : Flow=Stratified(80/20), Topology/Temporal=Chronological
Temporal Data            : Pseudo-temporal (Index-based windowing)

[Graph statistics]
Raw Snapshots Evaluated  : 42
Average Nodes/Window     : 114.9
Average Edges/Window     : 278.3
Graph Density            : 0.0516

[CTGFlowNet metrics (LightGBM Classifier)]
Evaluation Samples       : 82332
Accuracy                 : 91.32%
Balanced Accuracy        : 90.70%
Precision                : 88.49%
Recall                   : 96.82%
Specificity              : 84.57%
F1 Score                 : 92.47%
ROC-AUC                  : 0.9863
Average Precision        : 0.9899

Confusion Matrix:
   TN: 31290  FP: 5710 
   FN: 1440   TP: 43892

[EvolveGCN-H topology prediction metrics]
Edge Precision           : 96.54%
Edge Recall              : 71.81%
Edge F1 Score            : 82.36%
Edge Jaccard             : 70.01%
ROC-AUC                  : 0.8462

[CTGTemporalNet metrics]
Status                   : VALID
Evaluation Samples       : 37
Distribution             : Normal=19, Attack=18

Accuracy                 : 64.86%
Balanced Accuracy        : 65.20%
Precision                : 60.87%
Recall / Sensitivity     : 77.78%
Specificity              : 52.63%
F1 Score                 : 68.29%
ROC-AUC                  : 0.7749

Confusion Matrix:
   TN: 10     FP: 9    
   FN: 4      TP: 14   

[Genesis Violation metrics]
Tuned Threshold          : 0.1400
Evaluation Samples       : 41
Normal Dist              : Mean: 0.1677, Std: 0.1022, Min: 0.0594, Max: 0.4073
Anomaly Dist             : Mean: 0.1751, Std: 0.0938, Min: 0.0756, Max: 0.3683

Confusion Matrix:
   TN: 8      FP: 11   
   FN: 11     TP: 11   

Accuracy                 : 46.34%
Precision                : 50.00%
Recall                   : 50.00%
Specificity              : 42.11%
F1 Score                 : 50.00%

[Reconstruction implementation status]
Status                   : IMPLEMENTED AND TESTED (Sandbox Simulator)
Validation Test          : Passed E2E (Reverse Genesis A* Path Search)
Adaptive Defense Status  : IMPLEMENTED AND TESTED (Sandbox CGB)
Defense Decision         : Minimizes Residual Risk + Betweenness Centrality Cost


============================================================
CTG — CROSS-DATASET COMPARISON
============================================================
Metric                      | Validation (Dataset 1) | Held-out Test (Dataset 2)
-------------------------------------------------------------------------
FlowNet Accuracy            | 94.92% | 91.32%
Topology Edge F1            | 81.76% | 82.36%
Temporal Sequence F1        | 100.00% | 68.29%

Notes:
- The PyTorch flow model was replaced with a LightGBM classifier.
- The model, scalers, graph definitions, and thresholds were strictly fit on the training portion (first 80%) of Dataset 1.
- The validation report evaluates performance on the remaining 20% of Dataset 1.
- The held-out test report evaluates the completely unseen Dataset 2 without retraining.
- "NOT EVALUABLE" metrics signify that the specific test split was missing the necessary positive/negative labels to mathematically define the metric (e.g. Precision when True Positives and False Positives are zero).
