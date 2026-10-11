============================================================
CTG — DATASET 1 (VALIDATION PORTION) EVALUATION
Dataset: UNSW_NB15_training-set.csv
============================================================

[Dataset analysis]
Dataset name             : UNSW_NB15_training-set.csv
Records                  : 35069
Features                 : 42
Normal Flows             : 11200
Attack Flows             : 23869
Attack Ratio             : 68.06%
Split Protocol           : Flow=Stratified(80/20), Topology/Temporal=Chronological
Temporal Data            : Pseudo-temporal (Index-based windowing)

[Graph statistics]
Raw Snapshots Evaluated  : 36
Average Nodes/Window     : 201.9
Average Edges/Window     : 410.8
Graph Density            : 0.0219

[CTGFlowNet metrics (LightGBM Classifier)]
Evaluation Samples       : 35069
Accuracy                 : 94.92%
Balanced Accuracy        : 95.13%
Precision                : 97.91%
Recall                   : 94.56%
Specificity              : 95.70%
F1 Score                 : 96.21%
ROC-AUC                  : 0.9934
Average Precision        : 0.9969

Confusion Matrix:
   TN: 10718  FP: 482  
   FN: 1298   TP: 22571

[EvolveGCN-H topology prediction metrics]
Edge Precision           : 95.34%
Edge Recall              : 71.57%
Edge F1 Score            : 81.76%
Edge Jaccard             : 69.15%
ROC-AUC                  : 0.8404

[CTGTemporalNet metrics]
Status                   : ONE-CLASS LIMITED (Due to flow distributions in split)
Evaluation Samples       : 31
Distribution             : Normal=0, Attack=31

Accuracy                 : 100.00%
Balanced Accuracy        : NOT EVALUABLE
Precision                : 100.00%
Recall / Sensitivity     : 100.00%
Specificity              : NOT EVALUABLE
F1 Score                 : 100.00%
ROC-AUC                  : NOT EVALUABLE

Confusion Matrix:
   TN: 0      FP: 0    
   FN: 0      TP: 31   

[Genesis Violation metrics]
Tuned Threshold          : 0.1400
Evaluation Samples       : 35
Normal Dist              : Mean: 0.0000, Std: 0.0000, Min: 0.0000, Max: 0.0000
Anomaly Dist             : Mean: 0.1747, Std: 0.0673, Min: 0.0886, Max: 0.3683

Confusion Matrix:
   TN: 0      FP: 0    
   FN: 12     TP: 23   

Accuracy                 : 65.71%
Precision                : 100.00%
Recall                   : 65.71%
Specificity              : NOT EVALUABLE
F1 Score                 : 79.31%

[Reconstruction implementation status]
Status                   : IMPLEMENTED AND TESTED (Sandbox Simulator)
Validation Test          : Passed E2E (Reverse Genesis A* Path Search)
Adaptive Defense Status  : IMPLEMENTED AND TESTED (Sandbox CGB)
Defense Decision         : Minimizes Residual Risk + Betweenness Centrality Cost
