# Final Two-Dataset Evidence Map

| Claim | Dataset | Raw Evidence | Execution Script | Metric | Result | Ground Truth | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Temporal Graph Construction | CIC-IDS2017 | `cic_ids_temporal_changes.csv` | `cic_ids_real_experiments.py` | Chronological sort | Success | Timestamps | **PASS** |
| Topology Grammar Evolution | CIC-IDS2017 | `cic_ids_grammar_real.csv` | `cic_ids_real_experiments.py` | Legitimate edge extraction | Success | Benign traffic | **PASS** |
| Genesis Violation Detection | CIC-IDS2017 | `cic_ids_gv_real.csv` | `cic_ids_real_experiments.py` | Anomaly precision/recall | Validated | Flow-labels | **PASS** |
| EvolveGCN-H vs Persistence | CIC-IDS2017 | `topology_prediction_benchmark_raw.csv` | `run_evolvegcn_experiment.py`| F1, ROC-AUC, PR-AUC | Competitive | Future edges | **PASS** |
| EvolveGCN-H vs Persistence (1:1 balanced distribution) | APEX-IDS2026 | `test_predictions_seed*.parquet` | `run_evolvegcn_apex.py` | F1, Prec, Rec, ROC-AUC, PR-AUC | GCN Superior Recall | Next-snapshot edges | **PASS WITH LIMITATIONS** |
| Flow-level Baseline Evaluation | UNSW-NB15 | `baseline_comparison.csv` | `run_all_experiments.py` | F1, Accuracy | Validated | Attack labels | **PASS** |
| Dataset Class Distribution | UNSW-NB15 | `dataset_distribution.csv` | `run_all_experiments.py` | Class counts | Extracted | File metadata | **PASS** |
| RGAR Reconstruction | None | None | None | Sequence reconstruction | None | Causal events | **UNVALIDATED** |
| CGB Intervention | None | None | None | Containment rate | None | Active replay | **UNVALIDATED** |
