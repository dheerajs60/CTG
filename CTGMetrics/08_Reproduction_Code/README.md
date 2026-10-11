# Reproduction Code
## Environment
Requires Python >= 3.9 (Tested on 3.13.9). Dependencies: `pandas`, `numpy`, `scikit-learn`.

## Dataset Location
This minimal script suite assumes access to the large parquets located within the main CTG repository: `datasets/APEX-IDS2026/` and `results/apex_ids2026/predictions/`.

## Execution
Run `python3 recompute_apex_metrics.py` to independently evaluate F1, Precision, Recall, and AUC bounds from the saved Parquet outputs.
The LightGBM test failure is documented as an environment-specific segmentation fault on Apple Silicon, affecting flow baselines but not this PyTorch structural evaluation.
