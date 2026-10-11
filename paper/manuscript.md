# Counterfactual Topology Genesis for Detecting and Reconstructing Attack-Generating Processes in Dynamic Networks

## 1. Abstract
We present Counterfactual Topology Genesis (CTG), a framework focusing on the temporal topology of dynamic networks. Moving beyond traditional flow tracking, CTG features chronological graph construction and attack-associated topology analysis derived from empirical network endpoints. We natively implement EvolveGCN-H under a strict, leakage-controlled evaluation protocol for temporal topology prediction. Our empirical findings demonstrate that while persistence is an exceptionally strong baseline on static short-term topologies (CIC-IDS2017), EvolveGCN-H significantly outperforms persistence in highly dynamic, active-defense network environments (APEX-IDS2026). To complete the framework, we introduce topology grammar extraction and controlled algorithmic counterfactual reconstruction components (RGAR and CGB), explicitly noting these are theoretically implemented software components that remain scientifically unvalidated due to the limitations of passive datasets for causal evaluation.

## 2. Keywords
Network Anomaly Detection, Temporal Graphs, Graph Neural Networks, Counterfactual Reasoning, EvolveGCN, Intrusion Detection

## 3. Introduction
Network anomaly detection traditionally relies on tracking malicious flows. We propose shifting to structural analysis of temporal graphs, establishing a counterfactual topology reasoning framework.

Our methodological contributions include:
1.  **Temporal Topology Representation**: Constructing strict chronological sequences without future leakage.
2.  **Counterfactual Topology Reasoning Framework**: Introducing RGAR and CGB algorithms as implemented software modules.
3.  **Topology Grammar**: Extracting structural bounds from benign network snapshots.
4.  **Leakage-Controlled Empirical Evaluation**: Explicitly distinguishing between passive-data evidence and causal testbed evidence in our findings across both stable and highly-dynamic topologies.

## 4. Related Work
*Recent advancements in Graph Neural Networks (GNNs) have shown promise in dynamic network analysis [Placeholder: Citation]. However, existing approaches often suffer from temporal leakage during evaluation and fail to compare against strong topological persistence baselines [Placeholder: Citation]. Furthermore, causal reconstruction of attack paths remains an open challenge lacking proper empirical datasets [Placeholder: Citation].*

## 5. Problem Formulation
Given a continuous stream of network flows, the objective is to construct a chronological sequence of temporal graphs $G_t$ and accurately predict the structural transition $\Delta_t$ to $G_{t+1}$ using only historical topology. Furthermore, we define the theoretical problem of causal reverse genesis, attempting to isolate the specific structural operations responsible for anomalous graph states.

## 6. CTG Framework and Methodology

### 6.1 Temporal Graph Construction
**Mathematical Definition:** Given a set of network flow observations $F$, we construct a sequence of directed graphs $G_t = (V_t, E_t)$ where $V_t$ represents active endpoints (IPs) and $E_t$ represents observed flows within the time interval $[t, t+\Delta t]$. Flows are ordered by timestamp and partitioned into fixed-size chunks.

### 6.2 Topology Genesis Engine
Computes the structural transition $\Delta_t = (E^+_t, E^-_t, V^+_t, V^-_t)$ where $E^+_t = E_{t+1} \setminus E_t$ and $E^-_t = E_t \setminus E_{t+1}$. 

### 6.3 EvolveGCN-H
Uses a Gated Recurrent Unit (GRU) to evolve the weight matrix $W_t$ of a Graph Convolutional Network. $W_{t+1} = \text{GRU}(Z_t, W_t)$ where $Z_t$ is the mean-pooled representation of $G_t$. Evaluated with strict historical-node negative sampling to prevent leakage.

### 6.4 Attack-Associated Temporal Topology Anomaly Detection
Calculates statistical deviations of transition sizes against a legitimate training period to flag anomalous transitions.

### 6.5 Topology Grammar
A set of permissible edges $R = \bigcup_{t \in \text{Benign}} E_t$. Future edges are rejected if $e \notin R$.

### 6.6 Counterfactual Reconstruction (RGAR / CGB / Adaptive Defense)
Inferences ordered sequences of structural operations $A$ that causally link $G_t$ to $G_{t+1}$, and identifies minimal subsets of edges $C$ to block. These components are implemented structurally but remain **UNVALIDATED** due to the lack of authorized active routing testbeds.

## 7. Datasets and Experimental Protocol
CTG is evaluated using three real cybersecurity datasets:
*   **APEX-IDS2026:** High-confidence telemetry evaluated specifically for temporal topology edge prediction and graph dynamics under heavy churn (55% daily graph turnover). Target prediction is next-snapshot edge existence evaluated under a 1:1 sampled candidate distribution.
*   **CIC-IDS2017:** Chronological, endpoint-aware (IP/Port), labeled temporal flow data used to evaluate short-term topological persistence.
*   **UNSW-NB15:** Independent baseline dataset evaluated specifically on flow-level characteristics natively available in the processed records.

## 8. Results

### 8.1 EvolveGCN-H vs. Persistence (APEX-IDS2026)
Evaluated on APEX-IDS2026 under strict chronological candidate generation (1:1 candidate ratio, next-snapshot prediction). Results represent the arithmetic mean and sample standard deviation across 3 seeds (42, 100, 1234) computed independently over 3,256,518 predictions per seed:

| Model | F1 | Precision | Recall | ROC-AUC | PR-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **EvolveGCN-H** | 0.9125 ± 0.0088 | 0.9317 ± 0.0044 | 0.8941 ± 0.0165 | 0.9705 ± 0.0034 | 0.9717 ± 0.0028 |
| **Persistence** | 0.7700 ± 0.0000 | 0.9998 ± 0.0000 | 0.6260 ± 0.0000 | 0.8130 ± 0.0000 | 0.8129 ± 0.0000 |

EvolveGCN-H significantly outperforms persistence in highly dynamic topologies.

### 8.2 EvolveGCN-H vs. Persistence (CIC-IDS2017)
Evaluated on CIC-IDS2017, where structural turnover is extremely low:

| Model | F1 | ROC-AUC | PR-AUC |
| :--- | :--- | :--- | :--- |
| **EvolveGCN-H** | 0.4187 ± 0.1357 | 0.6372 ± 0.0526 | 0.6472 ± 0.0831 |
| **Persistence** | 0.4605 ± 0.0005 | 0.6481 ± 0.0007 | 0.6461 ± 0.0013 |

Here, persistence serves as a competitively dominant baseline.

### 8.3 Topology Grammar and Anomaly Detection
Topology grammar evolution successfully extracted mathematical structural bounds from benign network snapshots. Attack-associated temporal topology anomaly detection effectively mapped statistical deviations in $\Delta_t$ directly to underlying CIC-IDS2017 flow attack densities.

## 9. Discussion
The results highlight a fundamental topological dichotomy: in short-term static topologies (CIC-IDS2017), the complexity of temporal GNNs does not automatically yield superior prediction due to the strength of the persistence baseline. Conversely, in highly dynamic active-defense environments (APEX-IDS2026), EvolveGCN-H critically captures edge flux, overcoming the recall collapse experienced by the persistence model.

## 10. Limitations and Threats to Validity
1. **Base-Rate Fallacy:** The APEX-IDS2026 evaluation utilizes a 1:1 sampled candidate distribution. The 0.9317 precision metric is conditional on this protocol and must not be represented as a real-world deployment metric, as severe graph sparsity would heavily degrade operational precision.
2. **Passive Telemetry:** Passive telemetry strictly prevents validating counterfactual intervention algorithms.
3. **Causal Ground Truth:** CIC-IDS2017 flow attack labels are not independently verified ground truth for topology-level Genesis Violations or ordered causal attack sequences.
4. **Statistical Significance:** Three random seeds do not definitively establish broad generalization.

## 11. Conclusion
Counterfactual Topology Genesis establishes a rigorous foundation for chronological graph reasoning in cybersecurity. While complex temporal algorithms like EvolveGCN-H thrive in highly dynamic environments, our strict leakage-controlled validation emphasizes that baseline persistence remains a dominant heuristic in stable networks. Finally, we establish clear empirical boundaries by strictly withholding validation claims from theoretical causal reconstruction algorithms until active testbed evaluation becomes possible.

## 12. References
[1] Author, A. et al. (2026). Temporal Graph Networks. *Journal of Cybersecurity*. (Placeholder)
[2] Author, B. et al. (2025). The Base-Rate Fallacy in Intrusion Detection. *Security Proceedings*. (Placeholder)

## 13. Declarations
*   **Funding:** [Placeholder: No external funding / Funding agency details to be inserted].
*   **Conflicts of Interest:** The authors declare no conflicts of interest.
*   **Data Availability:** The CIC-IDS2017 and UNSW-NB15 datasets are publicly available from their original distributors. The APEX-IDS2026 High-Confidence subset must be obtained securely according to the provider's licensing constraints. Test artifacts and evaluation splits for reproducibility are available within the repository bounds.
