============================================================
CTG — CIC-IDS2017 SECONDARY BENCHMARK EVALUATION
Dataset: CIC-IDS2017 (Controlled Laboratory Testbed)
============================================================

[Dataset analysis]
Dataset name             : CIC-IDS2017
Records                  : 2,830,743 flows
Features                 : 84 columns
Capture Period           : 5 consecutive days (2017-07-03 to 2017-07-07)
Temporal Data            : Microsecond-resolution timestamp sorted

[Graph statistics]
Raw Snapshots Evaluated  : 5 chronological chunks
Average Nodes/Window     : 3115.4
Average Edges/Window     : 9492.4
Graph Density            : 0.0014

[EvolveGCN-H vs. Persistence Baseline (Chronological Link Prediction)]
Metric                   | EvolveGCN-H (Mean ± Std) | Persistence Baseline   | Difference
----------------------------------------------------------------------------------------
F1 Score                 | 0.4187 ± 0.1357     | 0.4605 ± 0.0005 | -0.0418
Precision                | 0.6809 ± 0.0529     | 0.9865 ± 0.0044 | -0.3056
Recall                   | 0.3101 ± 0.1323     | 0.3004 ± 0.0000 | +0.0098
ROC-AUC                  | 0.6372 ± 0.0526     | 0.6481 ± 0.0007 | -0.0109
PR-AUC                   | 0.6472 ± 0.0828     | 0.6461 ± 0.0013 | +0.0011
