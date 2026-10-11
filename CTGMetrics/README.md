# CTG Research Submission Package

This `CTGMetrics` directory is a focused research-paper evidence bundle containing the validated metrics, publication figures, methodology documentation, and reproducibility scripts required for the Counterfactual Topology Genesis (CTG) manuscript submission.

**Note:** This package is NOT a standalone reproduction environment. Large raw datasets, intermediate graphs, and massive model checkpoints (`.parquet`, `.pt`, `.csv` logs) are maintained securely in the primary project repository or explicit artifact storage systems.

## Package Contents
- **01_Manuscript:** The canonical, journal-neutral `CTG_Manuscript.md`. (Word document pending).
- **02_Figures:** The final SVGs/PNGs/PDFs with `FIGURE_PROVENANCE.md` providing generation traceability.
- **03_Metrics_and_Tables / 04_Experimental_Evidence:** Lightweight summaries of empirically validated metrics across datasets.
- **05_Datasets_and_Protocol:** Documentation regarding dataset acquisition, preprocessing rules, and chronological boundaries.
- **06_Methodology:** The capability map (`CLAIM_EVIDENCE_MAP.md`) strictly gating empirical evidence from unvalidated causal theories (`ENGINE_VALIDATION_STATUS.md`).
- **07_Limitations_and_Review:** Scientific integrity boundary definitions (`LIMITATIONS.md`) handling the base-rate fallacy and the reported LightGBM environment test crash.
- **08_Reproduction_Code:** Core metric recomputation scripts and repository-forensic validation routines.
- **09_Submission_Materials:** Target journal requirement tracking.

## Manifest
A strictly hashed `MANIFEST.csv` is provided in this root directory, detailing the SHA-256 fingerprint, byte size, and origin of every copied artifact.
