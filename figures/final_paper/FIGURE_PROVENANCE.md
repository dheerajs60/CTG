# Final Figure Provenance

| Figure | Dataset | Input Artifact | Generating Script | Calculation | Configuration |
|---|---|---|---|---|---|
| `fig01_ctg_architecture` | N/A | N/A | `generate_final_figures.py` | Architecture Diagram | Matplotlib diagram |
| `fig02_temporal_topology` | CIC-IDS2017 | `cic_ids_temporal_changes.csv` | `generate_final_figures.py` | Node and Edge chronological plot | 20k rows, 10 chunks |
| `fig03_genesis_transitions` | CIC-IDS2017 | `genesis_transitions.csv` | `generate_final_figures.py` | Count of transition set operations | N/A |
| `fig04_evolvegcn_vs_persistence` | CIC-IDS2017 | `topology_prediction_benchmark.csv` | `generate_final_figures.py` | Mean and Std Dev parsing | 3 seeds (42, 123, 999), 0.5 threshold |
| `fig05_topology_anomaly` | CIC-IDS2017 | `cic_ids_temporal_changes.csv` | `generate_final_figures.py` | Train mean + train std threshold | Train interval 0-4 |
| `fig06_grammar_evolution` | CIC-IDS2017 | `grammar_metrics.csv` | `generate_final_figures.py` | Bar chart of whitelist evaluation | Train interval 0-4 |
| `fig07_two_dataset_evaluation` | CIC-IDS2017 & UNSW-NB15 | `topology_prediction_benchmark.csv` & `baseline_comparison.csv` | `generate_final_figures.py` | Separate metric comparison | Dual task representation |
| `fig02_temporal_topology_apex` | APEX-IDS2026 | `graph_transition_statistics.csv` | `generate_apex_figures.py` | Node count & total topology changes | 45 daily snapshots |
| `fig03_genesis_transitions_apex` | APEX-IDS2026 | `graph_transition_statistics.csv` | `generate_apex_figures.py` | Added/removed edges and nodes count | 44 transition intervals |
| `fig04_evolvegcn_vs_persistence_apex` | APEX-IDS2026 | `test_predictions_seed{42,100,1234}.parquet` | `generate_apex_figures.py` | Recomputed metrics across seeds (F1, Prec, Rec, ROC, PR) | 3 seeds (42, 100, 1234), 0.5 threshold |
| `fig08_dataset_scale_temporal_scope` | Multi-dataset (9 datasets) | `dataset_scope_comparison.csv` | `generate_dataset_scope_figures.py` | Comparative log scale record count and duration | Documented dataset scale & time |
| `fig09_dataset_topology_ctg_suitability` | Multi-dataset (9 datasets) | `dataset_scope_comparison.csv` | `generate_dataset_scope_figures.py` | Categorical suitability matrix | 11 criteria evaluated |
| `fig10_dataset_scope_comparison_unified` | Multi-dataset (9 datasets) | `dataset_scope_comparison.csv` | `generate_dataset_scope_figures.py` | Unified 4-panel scope & suitability comparison | Comprehensive benchmark scope |
