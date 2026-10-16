# Phase 1 Evaluation Protocol and Baseline Specification

**Date:** October 15, 2026  
**Document Version:** 1.0  
**Phase:** Phase 1 (Baselines & Corrected Negative Evaluation Pipeline)

---

## 1. Problem Formulation & Prediction Task

### 1.1 Formal Task Definition
Given a sequence of discrete, chronological temporal graph snapshots:
$$\mathcal{G} = \{G_0, G_1, \dots, G_t, G_{t+1}, \dots, G_T\}$$
where each snapshot $G_t = (V_t, E_t)$ represents network communication observed during a disjoint time window $[t \cdot \Delta t, (t+1) \cdot \Delta t)$.

The **temporal link prediction task** at time step $t$ is to predict the existence of directed edges in the subsequent snapshot $G_{t+1}$ using strictly historical observations $\{G_\tau\}_{\tau \le t}$.

### 1.2 Graph Representation & Directionality
*   **Nodes ($V_t$):** Network endpoints represented by IP addresses (e.g., IPv4 strings `192.168.10.50`).
*   **Edges ($E_t$):** Directed communication links $(u, v)$ where $u$ is the source endpoint (`src_ip`) initiating or transmitting traffic and $v$ is the destination endpoint (`dst_ip`). Directionality is strictly preserved ($u \to v \neq v \to u$) because network perimeter scanning, DoS, and client-server traffic are asymmetric.
*   **Duplicate-Edge Aggregation:** Network flow records frequently record multiple distinct flows between identical endpoints $(u, v)$ within a single window $[t, t+1)$. Within each snapshot $G_t$:
    *   Duplicate flows are collapsed into a single directed edge $e = (u, v)$.
    *   Edge attributes store aggregated metadata: `flow_count` (integer occurrences) and `total_bytes` (sum of bytes transferred).
    *   For topology prediction benchmarking, the target label $y_{(u,v)}^{(t+1)} \in \{0, 1\}$ is binary, denoting whether at least one communication flow occurred from $u$ to $v$ in snapshot $t+1$.

---

## 2. Snapshot Construction & Temporal Partitions

### 2.1 Non-Overlapping Windows
Snapshots are partitioned chronologically without temporal overlap:
*   **APEX-IDS2026:** Daily non-overlapping windows ($\Delta t = 24\text{ hours}$), producing 44 discrete snapshots from 2026-06-21 to 2026-08-03.
    *   *Train Partition:* Snapshots $0$ to $24$ (2026-06-21 to 2026-07-15, 25 days)
    *   *Validation Partition:* Snapshots $25$ to $31$ (2026-07-16 to 2026-07-22, 7 days)
    *   *Test Partition:* Snapshots $32$ to $43$ (2026-07-23 to 2026-08-03, 12 days)
    *   *Note on Boundary Snapshots:* Snapshot $0$ (June 21) and Snapshot $43$ (August 3) are recorded as partial days in telemetry metadata.
*   **CIC-IDS2017:** Chronological full-day or hour-scale non-overlapping windows spanning July 3 to July 7, 2017.

---

## 3. Candidate Universe and Stratification Protocol

To prevent evaluation bias and address Reviewer Comment C3, candidate edges at test step $t \to t+1$ are partitioned into three mutually exclusive categories:

### 3.1 Edge Category Stratification

1.  **Category 1: Recurring Edges ($E_{\text{rec}}$)**
    *   *Definition:* Positive edges present in both $G_t$ and $G_{t+1}$:
        $$E_{\text{rec}} = E_{t+1} \cap E_t$$
    *   *Model Eligibility:* Fully transductive. Both memory models (Persistence, EdgeBank) and structural models (GNNs) are eligible.
2.  **Category 2: New Edges Between Known Nodes ($E_{\text{known}}$)**
    *   *Definition:* Positive edges in $G_{t+1}$ where both endpoints $u, v \in V_t$, but $(u, v) \notin E_t$:
        $$E_{\text{known}} = \{(u, v) \in E_{t+1} \setminus E_t \mid u \in V_t \land v \in V_t\}$$
    *   *Model Eligibility:* Transductive on nodes, dynamic on edges. GNNs and topological heuristics (Common Neighbors, Jaccard) attempt to predict these. Standard Persistence cannot predict these ($\hat{y} = 0$).
3.  **Category 3: Edges Involving Unseen Nodes ($E_{\text{unseen}}$)**
    *   *Definition:* Positive edges in $G_{t+1}$ where at least one endpoint was not observed in $G_t$:
        $$E_{\text{unseen}} = \{(u, v) \in E_{t+1} \mid u \notin V_t \lor v \notin V_t\}$$
    *   *Model Eligibility:* Inductive. Pure transductive models (static GCN with fixed embedding tables, standard Persistence) cannot natively embed or evaluate unseen nodes without an explicit inductive fallback (e.g., global mean pooling or zero embedding).
    *   *Rule:* Models must not claim inductive performance without documenting their fallback mechanism. Performance on $E_{\text{unseen}}$ must be reported separately.

---

## 4. Corrected Negative Sampling Protocols

Candidate evaluations will test two distinct, strictly separated settings:

### Setting A: Historical Hard Negatives
*   **Candidate Pool:** Directed node pairs $(u, v)$ that were actively observed in historical telemetry prior to snapshot $t+1$, but do NOT occur in $G_{t+1}$:
    $$\mathcal{N}_{\text{hard}}^{(t+1)} = \left(\bigcup_{\tau \le t} E_\tau\right) \setminus E_{t+1}$$
*   **Significance:** Tests whether a model can distinguish inactive former links from active ones, directly testing memory decay. In this setting, Persistence precision drops significantly from $0.9998$ because edges that disappeared generate true false positives.
*   **Sampling Protocol:** Sample $K = |E_{t+1}^{\text{eligible}}|$ unique pairs from $\mathcal{N}_{\text{hard}}^{(t+1)}$ without replacement using seed $S$.

### Setting B: Mixed / Uniform Random Negatives
*   **Candidate Pool:** Directed node pairs $(u, v) \in V_t \times V_t$ sampled uniformly without replacement such that $(u, v) \notin E_{t+1}$.
*   **Significance:** Standard temporal benchmark setting representing the full candidate graph universe.
*   **Anti-Leakage Constraints (Mandatory):**
    1.  *Disjointness:* $E_{\text{neg}} \cap E_{t+1} = \emptyset$.
    2.  *No Future Leakage:* Nodes in negative pairs must be members of $\bigcup_{\tau \le t} V_\tau$.
    3.  *No Padding or Duplication:* If the negative pool contains fewer unique pairs than required, the sampler **must raise an explicit error**. It must NEVER duplicate or pad negative examples.
    4.  *Seed Reproducibility:* The sampling PRNG is initialized with an explicit, fixed seed per transition ($S_{\text{base}} + t$).

---

## 5. Model Specifications and Scoring Mechanisms

Every baseline must be evaluated on the exact same candidate sets. Scoring mechanisms are explicitly distinguished between continuous ranking models and discrete binary classifiers:

| Model | Class Type | Output Score $s(u, v)$ | Binary Decision $\hat{y}$ | Ranking Metrics Eligible? (MRR, Hits@K) |
| :--- | :--- | :--- | :--- | :--- |
| **Persistence** | Memory Baseline | $s \in \{0.0, 1.0\}$ | $\mathbb{I}\{(u, v) \in E_t\}$ | **NO** (Binary step; degenerate rank) |
| **EdgeBank-∞** | Memory Baseline | $s \in \{0.0, 1.0\}$ (binary) or frequency | $\mathbb{I}\{(u, v) \in \bigcup_{\tau \le t} E_\tau\}$ | **NO** (when binary); **YES** (frequency) |
| **EdgeBank-tw** | Memory Baseline | $s \in \{0.0, 1.0\}$ | $\mathbb{I}\{(u, v) \in \bigcup_{\tau = t-W+1}^{t} E_\tau\}$ | **NO** (Binary step) |
| **Common Neighbors** | Topological Heuristic | $s = |\mathcal{N}_{\text{out}}(u) \cap \mathcal{N}_{\text{in}}(v)|$ | $s \ge \theta$ | **YES** (Continuous non-negative integer) |
| **Jaccard Coefficient** | Topological Heuristic | $s = \frac{|\mathcal{N}(u) \cap \mathcal{N}(v)|}{|\mathcal{N}(u) \cup \mathcal{N}(v)|}$ | $s \ge \theta$ | **YES** (Continuous $\in [0, 1]$) |
| **Adamic-Adar** | Topological Heuristic | $s = \sum_{z \in \mathcal{N}(u) \cap \mathcal{N}(v)} \frac{1}{\log |\mathcal{N}(z)|}$ | $s \ge \theta$ | **YES** (Continuous $\ge 0$) |
| **EvolveGCN-H** | Dynamic GNN | $s = \sigma(\text{MLP}(h_u^{(t)} \,\|\, h_v^{(t)})) \in (0, 1)$ | $s \ge 0.5$ | **YES** (Continuous probability score) |

### 5.1 Metric Reporting Rules
*   **Classification Metrics (Threshold-Based):** F1-Score, Precision, Recall, Accuracy.
*   **Continuous Ranking Metrics:** Mean Reciprocal Rank (MRR), Hits@10, Hits@50, Average Precision (AP), ROC-AUC.
*   **Strict Rule:** Discrete binary models (Persistence, binary EdgeBank) are evaluated on Classification Metrics only. They must not be assigned interpolated ROC-AUC or ranking scores.
