# CTG Workspace Status

**Status:** CLEAN
**Date:** October 10, 2026

## Active Scientific Artifacts
- **Manuscript:** `paper/manuscript.md`
- **Results:** `paper/RESULTS_AND_METRICS.md`
- **Limitations:** `paper/LIMITATIONS.md`
- **Reproducibility Guide:** `paper/REPRODUCIBILITY_GUIDE.md`
- **Experiment Protocol:** `paper/EXPERIMENT_PROTOCOL.md`
- **Data Documentation:** `paper/DATASET_DOCUMENTATION.md`
- **Evidence Map:** `paper/CLAIM_EVIDENCE_MAP.md`
- **Validation Status:** `paper/ENGINE_VALIDATION_STATUS.md`

## Repositiory Constraints
- Generated pipeline audits, temporary datasets, duplicated figures, and minor stage updates have been archived to `archive/markdown_reports/` to enforce workspace minimalism.
- Python caches (`__pycache__`, `.pytest_cache`) are excluded in `.gitignore` and removed from the active tree. 
- Results and checkpoints exist under `results/`.
- `lightgbm` segmentation fault is an isolated environment issue on Apple Silicon and does not impact reproducibility of the core results.
