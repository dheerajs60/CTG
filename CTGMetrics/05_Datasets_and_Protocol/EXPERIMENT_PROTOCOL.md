# Experiment Protocol

## 1. Research Questions
*   How accurately can EvolveGCN-H predict network topology versus a Persistence baseline?
*   Can temporal topology anomalies map to attack phases?
*   Can grammar evolution effectively whitelist benign structure?

## 2. Dataset Splitting
*   **CIC-IDS2017:** 20,000 continuous samples chronologically sorted by `Timestamp`. Chunked into 10 snapshots (2,000 flows each). 
    *   Train/Val bounds for Anomaly/Grammar: Snapshots 1-4 (Train), Snapshots 6-10 (Test).
*   **UNSW-NB15:** Train set limit 5000, Test set limit 2500 (sampled with `random_state=42`).

## 3. Leakage Control
*   Candidate sampling for temporal link prediction in $G_t \rightarrow G_{t+1}$ restricts negative samples STRICTLY to historical endpoints observed in or before $G_t$ (`nodes_seen = list(set(G_curr.nodes()))`).
*   Grammar rules are extracted solely from benign subsets prior to malicious intervention.

## 4. Evaluation Metrics
*   **Topology Prediction:** F1 (0.5 threshold), ROC-AUC, PR-AUC.
*   **Anomaly/Classification:** F1, Accuracy, Precision, Recall.

## 5. Configuration
*   **Random Seeds:** 42, 123, 999.
*   **Models:** Logistic Regression for Flow Baseline. DummyClassifier (majority class) for absolute baseline. EvolveGCN-H (100 epochs, 0.001 lr).
