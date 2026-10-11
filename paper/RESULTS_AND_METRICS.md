# Results and Metrics Reference

All metrics are extracted dynamically from `results/final_real/`.

## 1. Temporal Topology Prediction (CIC-IDS2017)
*   **EvolveGCN-H:**
    *   F1 Mean: 0.4187 (Std: 0.1357)
    *   ROC-AUC Mean: 0.6372 (Std: 0.0526)
    *   PR-AUC Mean: 0.6472 (Std: 0.0831)
*   **Persistence Baseline:**
    *   F1 Mean: 0.4605 (Std: 0.0005)
    *   ROC-AUC Mean: 0.6481 (Std: 0.0007)
    *   PR-AUC Mean: 0.6461 (Std: 0.0013)
*   **Interpretation:** Persistence demonstrates extreme strength in short-term static topologies. EvolveGCN does not uniformly outperform it.

## 2. Temporal Topology Prediction (APEX-IDS2026)
*   **Dataset Note:** 1:1 sampled negative candidate universe.
*   **EvolveGCN-H (3 seeds):**
    *   F1 Mean: 0.9125 (Std: 0.0086)
    *   Precision Mean: 0.9317 (Std: 0.0044)
    *   Recall Mean: 0.8941 (Std: 0.0165)
    *   ROC-AUC Mean: 0.9705 (Std: 0.0034)
    *   PR-AUC Mean: 0.9717 (Std: 0.0028)
*   **Persistence Baseline (3 seeds):**
    *   F1 Mean: 0.7700 (Std: 0.0000)
    *   Precision Mean: 0.9998 (Std: 0.0000)
    *   Recall Mean: 0.6260 (Std: 0.0000)
    *   ROC-AUC Mean: 0.8130 (Std: 0.0000)
    *   PR-AUC Mean: 0.8129 (Std: 0.0000)
*   **Interpretation:** APEX-IDS2026 features intense daily graph churn. The persistence baseline achieves near-perfect precision (edges from $T-1$ that continue are almost always true), but its recall is low (0.62) because it misses all newly formed edges. EvolveGCN-H successfully learns dynamic graph evolution patterns, drastically improving recall to 0.89 and raising overall F1 from 0.77 to 0.91, demonstrating definitive superiority over persistence for dynamic topologies.

## 3. Flow Baseline (UNSW-NB15)
*   Anomaly successfully flags test snapshots matching `Is_Attack_Associated == 1`.
*   Grammar reliably logs `Legit_Accepted` bounds.

## 4. Counterfactual Operations
*   RGAR Sequence Accuracy: NOT VALIDATED
*   CGB Prevention Rate: NOT VALIDATED
*   Adaptive Defense: NOT VALIDATED
