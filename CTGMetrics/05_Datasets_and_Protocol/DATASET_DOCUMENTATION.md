# Dataset Documentation

## 1. CIC-IDS2017
*   **Purpose:** Primary temporal topology evaluation.
*   **Provenance:** Downloaded from the Canadian Institute for Cybersecurity.
*   **File Structure:** `data/cic_ids2017/TrafficLabelling/`
*   **Fields Used:** `Source IP`, `Destination IP`, `Timestamp`, `Label`
*   **Temporal Properties:** Sorted chronologically by `Timestamp`. Provides endpoint-aware topological transitions spanning 10 temporal graph chunks.
*   **Supported CTG Components:** Temporal Graph Construction, Topology Genesis Engine, EvolveGCN-H Prediction, Topology Anomaly Detection, Topology Grammar Evolution.
*   **Unsupported CTG Components:** CGB, RGAR (lacks causal attack replay logs).

## 2. UNSW-NB15
*   **Purpose:** Independent flow-level baseline evaluation.
*   **Provenance:** Cyber Range Lab of UNSW Canberra.
*   **File Structure:** `data/unsw_nb15/`
*   **Fields Used:** Conventional continuous and categorical flow variables, `label`, `attack_cat`.
*   **Fields Not Available:** Source IP, Destination IP, Timestamp (in the processed subset utilized).
*   **Temporal Properties:** No chronological ordering or endpoint tracking natively supported.
*   **Supported CTG Components:** Flow-level baseline modeling, dataset complexity analysis.
*   **Unsupported CTG Components:** Temporal Graph Construction, Topology Genesis Engine, EvolveGCN-H Prediction, Topology Anomaly Detection, Topology Grammar Evolution, CGB, RGAR.
