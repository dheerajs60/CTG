# Engine Validation Status

## Empirically Validated
*   **Temporal Graph Construction:** Real-data executed (CIC-IDS2017 & APEX-IDS2026). Produces true chronological graphs matching endpoints.
*   **Topology Genesis:** Real-data executed (CIC-IDS2017). Transition generation ($\Delta_t$) verified against graph structure.
*   **EvolveGCN-H Prediction:** Real-data executed (CIC-IDS2017 & APEX-IDS2026). Strictly leakage-controlled metric boundaries generated. For APEX-IDS2026, it is specifically validated for next-snapshot edge existence on a 1:1 sampled candidate distribution, strongly outperforming persistence.
*   **Topology Anomaly Detection:** Real-data executed (CIC-IDS2017). Flow anomalies detected via transition shifts.
*   **Topology Grammar Evolution:** Real-data executed (CIC-IDS2017). Whitelist evolution recorded securely.

## Unvalidated / Theoretical Only
*   **Genesis Violation Detection (Causal):** True genesis validation implies an ordered process. Real passive telemetry fails to supply this underlying process intent.
*   **RGAR:** Requires true ordered causal attack-event ground truth which does not exist in standard packet captures.
*   **CGB:** Requires an authorized testbed capable of dynamically routing and actively simulating edge interventions.
*   **Adaptive Defense:** Implementation strictly theoretical, interface-only pending active-response environment construction.
