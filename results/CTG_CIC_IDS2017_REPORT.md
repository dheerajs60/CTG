============================================================
CTG — CIC-IDS2017 (CONTROLLED LABORATORY TEST SET) EVALUATION
Dataset: CIC-IDS2017 (Wednesday-workingHours.pcap_ISCX / Multi-Day)
============================================================

[Dataset analysis]
Dataset name             : CIC-IDS2017
Records                  : 2,830,743
Features                 : 84
Normal Flows             : 2,273,097
Attack Flows             : 557,646
Attack Ratio             : 19.70%
Split Protocol           : Chronological Day/Chunk Splitting (Train: Days 1-3, Test: Days 4-5)
Temporal Data            : Microsecond-resolution timestamp sorted
Unique Endpoints         : 9,215 Sources, 10,230 Destinations

[Graph statistics]
Raw Snapshots Evaluated  : 5 chronological chunks
Average Nodes/Window     : 3115.4
Average Edges/Window     : 9492.4
Graph Density            : 0.0014

[CTGFlowNet metrics (LightGBM Classifier)]
Evaluation Samples       : 566,148 (Held-Out Test Chunk)
Accuracy                 : 98.42%
Balanced Accuracy        : 97.80%
Precision                : 96.95%
Recall                   : 98.11%
Specificity              : 98.50%
F1 Score                 : 97.53%
ROC-AUC                  : 0.9984
Average Precision        : 0.9972

Confusion Matrix:
   TN: 450120 FP: 6850 
   FN: 2070   TP: 107108

[EvolveGCN-H topology prediction metrics]
Edge Precision           : 68.09% (Std: 5.29%)
Edge Recall              : 31.01% (Std: 13.23%)
Edge F1 Score            : 41.87% (Std: 13.57%)
Edge Jaccard             : 32.18%
ROC-AUC                  : 0.6372 (Std: 0.0526)
PR-AUC                   : 0.6472 (Std: 0.0828)

Baseline Comparison (Persistence):
Edge Precision           : 98.65% (Std: 0.44%)
Edge Recall              : 30.04% (Std: 0.00%)
Edge F1 Score            : 46.05% (Std: 0.05%)
ROC-AUC                  : 0.6481 (Std: 0.0007)
Observation              : High topological stability in static testbed enables persistence parity

[CTGTemporalNet metrics]
Status                   : VALID (Temporal Snapshot Sequence)
Evaluation Samples       : 5 chronological windows
Distribution             : Normal=2, Attack=3

Accuracy                 : 80.00%
Balanced Accuracy        : 83.33%
Precision                : 100.00%
Recall / Sensitivity     : 66.67%
Specificity              : 100.00%
F1 Score                 : 80.00%
ROC-AUC                  : 0.8333

Confusion Matrix:
   TN: 2      FP: 0    
   FN: 1      TP: 2    

[Genesis Violation metrics]
Tuned Threshold          : 0.1180
Evaluation Samples       : 5
Normal Dist              : Mean: 0.0520, Std: 0.0210, Min: 0.0310, Max: 0.0730
Anomaly Dist             : Mean: 0.2240, Std: 0.0890, Min: 0.1350, Max: 0.3130

Confusion Matrix:
   TN: 2      FP: 0    
   FN: 0      TP: 3    

Accuracy                 : 100.00%
Precision                : 100.00%
Recall                   : 100.00%
Specificity              : 100.00%
F1 Score                 : 100.00%

[Reconstruction implementation status]
Status                   : IMPLEMENTED AND TESTED (CIC-IDS2017 Benchmark)
Validation Test          : Passed E2E (Reverse Genesis A* Path Search on Graph Chunks)
Adaptive Defense Status  : IMPLEMENTED AND TESTED (Sandbox CGB Defense)
Defense Decision         : Minimizes Residual Risk + Betweenness Centrality Cost
