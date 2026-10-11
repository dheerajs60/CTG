# Reproducibility Guide

## 1. Environment
*   **Operating System:** macOS Darwin arm64 (Apple Silicon) or standard Linux environments.
*   **Python Version:** >= 3.9 (Tested on 3.13.9)
*   **Dependencies:** `pandas`, `numpy`, `networkx`, `scikit-learn`, `matplotlib`, `torch`, `torch_geometric`, `lightgbm`

## 2. Directory Structure
*   `datasets/APEX-IDS2026/` (Requires `apex_ids2026_hc_subset.parquet`)
*   `datasets/cic_ids2017/` (Requires `TrafficLabelling/`)
*   `datasets/raw/UNSW_NB15/`
*   `scripts/`
*   `src/`
*   `tests/`

## 3. Execution Commands
To recreate all empirical artifacts from a clean state without hardcoded metrics:

1.  **Extract real datasets:**
    `PYTHONPATH=. python scripts/cic_ids_real_experiments.py`
    `PYTHONPATH=. python scripts/run_all_experiments.py`
2.  **Evaluate APEX-IDS2026 (Skip Training, Run Evaluation Directly on Frozen Checkpoints):**
    `PYTHONPATH=. python scripts/run_evolvegcn_apex.py`
    `PYTHONPATH=. python scripts/recompute_apex_metrics.py`
3.  **Evaluate CIC-IDS2017 Baseline Predictions:**
    `PYTHONPATH=. python scripts/run_evolvegcn_experiment.py`
4.  **Generate Final Figures:**
    `PYTHONPATH=. python scripts/generate_final_figures.py`
5.  **Validate Final Scientific Provenance and Code:**
    `PYTHONPATH=. python scripts/validate_no_hardcoded_results.py`
    `PYTHONPATH=. python scripts/final_submission_audit.py`
    `pytest tests/`

## 4. Expected Artifacts
All generated metrics will appear in `results/metrics/`, `results/final_real/`, and `results/apex_ids2026/predictions/`. Figures will output to `figures/final_paper/`.

## 5. Known Environmental Limitations (LightGBM)
**Issue:** When running `pytest tests/test_pipeline.py`, the flow-level classification test encounters a `Fatal Python error: Segmentation fault`. 
**Diagnosis:** This is an isolated, environment-specific dependency issue occurring in LightGBM 4.6.0 on Apple Silicon (`arm64`) during pointer deserialization (`__setstate__` in `lightgbm/basic.py`). 
**Impact:** This failure strictly affects the baseline flow-level test and does **not** impact the execution, reliability, or reproducibility of the core mathematical PyTorch EvolveGCN-H algorithm, graph construction, or temporal anomaly evaluations. The remaining core algorithms explicitly pass unit testing (`pytest tests/test_evolvegcn_h.py tests/test_gv_math.py`).
