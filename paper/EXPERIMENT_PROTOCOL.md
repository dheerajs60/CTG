# Definitive Experiment Protocol: Temporal Link Prediction & Graph Dynamics

## 1. Scope & Research Questions
This document defines the formal experiment protocol for evaluating temporal link prediction and multi-scale graph dynamics in dynamic network security environments.

* **RQ1 (Baseline Robustness under Hard Negatives):** Does the empirical superiority of memory/persistence baselines over dynamic GNNs hold when evaluated against historically active but currently inactive edges (Setting A: Hard Historical Negatives), or is it an artifact of random non-edge sampling (Setting B)?
* **RQ2 (Multi-Scale Topological Churn):** Does temporal window granularity (1h, 6h, 12h, 24h) explain baseline link prediction performance across datasets with disparate collection durations?
* **RQ3 (Topological Signal vs. Memory):** Can graph heuristic proximity metrics (Common Neighbors, Adamic-Adar, Jaccard) provide predictive signal when edge novelty is high and memory decay fails?

---

## 2. Dataset Splitting & Snapshot Construction

### 2.1 APEX-IDS2026 (Enterprise Real-World Deployment)
* **Duration:** 44 continuous days (2026-06-21 to 2026-08-03).
* **Flow Volume:** 69,107,018 verified flows.
* **Snapshots (Daily, $\Delta t = 24\text{h}$):** 44 temporal snapshots.
  * **Train Split:** Snapshots 0–24 (Days 1–25).
  * **Validation Split:** Snapshots 25–31 (Days 26–32).
  * **Test Split:** Snapshots 32–43 (Days 33–44, 12 evaluation transitions).
* **Sub-Daily Multi-Scale Analysis:** 12-hour windows (86 snapshots) and 6-hour windows (170 snapshots).

### 2.2 CIC-IDS2017 (Laboratory Cyber Range)
* **Duration:** 5 active days (2017-07-03 to 2017-07-07).
* **Flow Volume:** 2,830,743 flows.
* **Snapshots (Daily, $\Delta t = 24\text{h}$):** 5 temporal snapshots (Monday to Friday).
  * **Train Split:** Days 0–2 (Monday–Wednesday).
  * **Validation Split:** Day 3 (Thursday).
  * **Test Split:** Day 4 (Friday, 1 evaluation transition).
* **Sub-Daily Multi-Scale Analysis:** 6-hour windows (15 snapshots, 14 transitions) and 1-hour windows (50 snapshots, 49 transitions) across the continuous timeline, capturing diurnal variation and overnight collection pauses.

---

## 3. Formal Metrics Definitions

### 3.1 Temporal Graph Dynamics
For consecutive graph snapshots $G_{t-1} = (V_{t-1}, E_{t-1})$ and $G_t = (V_t, E_t)$:

* **Edge Recurrence Rate ($R_t$):**
  $$R_t = \frac{|E_t \cap E_{t-1}|}{|E_t|}$$
* **Edge Novelty Rate ($N_t$):**
  $$N_t = \frac{|E_t \setminus E_{t-1}|}{|E_t|} = 1 - R_t$$
* **Symmetric Edge Turnover (Jaccard Distance, $T_{\text{Jaccard}}$):**
  $$T_{\text{Jaccard}} = \frac{|E_t \triangle E_{t-1}|}{|E_t \cup E_{t-1}|} = \frac{|E_t \setminus E_{t-1}| + |E_{t-1} \setminus E_t|}{|E_t \cup E_{t-1}|}$$
* **Normalized Symmetric Difference (Dice Dissimilarity, $T_{\text{Dice}}$):**
  $$T_{\text{Dice}} = \frac{|E_t \triangle E_{t-1}|}{|E_t| + |E_{t-1}|} = \frac{|E_t \setminus E_{t-1}| + |E_{t-1} \setminus E_t|}{|E_t| + |E_{t-1}|}$$

*Note:* Edge recurrence $R_t$ and novelty $N_t$ are directional rates normalized strictly by target snapshot size $|E_t|$. In contrast, $T_{\text{Jaccard}}$ and $T_{\text{Dice}}$ are symmetric set-theoretic distance metrics capturing total bilateral edge flux across both snapshots. In this work, the primary metric is $T_{\text{Jaccard}}$ (canonical Jaccard distance on sets); $T_{\text{Dice}}$ is also reported for comparability with prior literature.

### 3.2 Temporal Link Prediction Metrics
* **Classification Metrics (at decision threshold $\tau = 0.5$ or $\tau = 1.0$ for discrete counts):**
  $$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}, \quad \text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}, \quad \text{F1} = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$
* **Continuous Area Metrics (Gated by Ranking Eligibility):**
  * ROC-AUC and Average Precision (PR-AUC) are computed strictly for models producing continuous real-valued confidence scores.
  * Models with binary step outputs (Persistence, EdgeBank binary) are flagged as `NOT EVALUABLE (Discrete Binary Predictor)` for ranking metrics to avoid degenerate step-function artifacts.
  * *Note on Mean Reciprocal Rank (MRR):* In standard link prediction benchmarks (e.g. DyGLib, TGB), MRR evaluates 1-vs-$Q$ candidate ranking where each query edge is ranked among $Q$ negative candidates. In contrast, evaluating MRR on a globally pooled candidate set ($N_{\text{pos}}$ positives and $N_{\text{neg}}$ negatives) mathematically constrains the maximum possible MRR to $\frac{1}{N_{\text{pos}}} \sum_{r=1}^{N_{\text{pos}}} \frac{1}{r} = \frac{H_{N_{\text{pos}}}}{N_{\text{pos}}} \approx 0.0041$ (for $N_{\text{pos}} = 2000$) even for a theoretically perfect classifier. To prevent misinterpreting this pooled ranking artifact, paper benchmark tables report standardized area metrics (ROC-AUC and Average Precision) instead.

---

## 4. Candidate Generation & Anti-Leakage Safeguards

### 4.1 Positive Candidate Stratification
Positive edges in $G_{t+1}$ are partitioned into three mutually disjoint subsets:
1. **Recurring edges:** $E_{t+1} \cap E_t$.
2. **New edges between known nodes:** $(u, v) \in E_{t+1} \setminus E_t$ where $u, v \in V_{\text{hist}} \cup V_t$.
3. **Unseen node edges:** $(u, v) \in E_{t+1}$ where $u \notin V_{\text{hist}} \cup V_t$ or $v \notin V_{\text{hist}} \cup V_t$.

Link prediction evaluation is restricted to eligible edges (`recurring` $\cup$ `new_between_known`). Edges involving previously unobserved nodes are tracked separately.

### 4.2 Negative Sampling Regimes
* **Setting A (Hard Historical Negatives):**
  Negative edges are sampled uniformly without replacement strictly from:
  $$E_{\text{neg}}^{\text{hard}} \subseteq E_{\text{hist}} \setminus E_{t+1}$$
  These represent historically active communication channels that went dark at $t+1$. Silent padding or duplicate negative injection is strictly prohibited; if $|E_{\text{hist}} \setminus E_{t+1}| < K$, an explicit error is raised.
* **Setting B (Mixed Random Negatives):**
  Negative edges are sampled uniformly without replacement from $(u, v) \in V_t \times V_t$ such that $(u, v) \notin E_{t+1}$ and $u \neq v$.

Both settings maintain a balanced $1:1$ positive-to-negative candidate ratio ($K = \min(|E_{\text{pos}}|, 2000)$ per step). Within each seed run, positive and negative candidate sets are strictly identical across all evaluated models. Across seeds, negative non-edge samples vary deterministically with the PRNG seed (`seed + t` for Setting A, `seed + 200 + t` for Setting B).

---

## 5. Model Configurations & Training

1. **Persistence:** Predicts $\hat{y}(u, v) = 1$ if $(u, v) \in E_t$, else $0$.
2. **EdgeBank-∞ (Binary & Frequency):** Unbounded memory of all historical edges $E_{\text{hist}}$.
3. **EdgeBank-tw ($W=2$, Binary):** Sliding window memory across the last $W$ snapshots: $M_t = \bigcup_{\tau = t - W + 1}^t E_\tau$.
4. **Common Neighbors (Directed):** Score $s(u, v) = |N_{\text{out}}(u) \cap N_{\text{in}}(v)|$ computed on $G_t$.
5. **Jaccard Coefficient (Undirected):** Score $s(u, v) = \frac{|N(u) \cap N(v)|}{|N(u) \cup N(v)|}$ computed on $G_t$.
6. **Adamic-Adar (Undirected):** Score $s(u, v) = \sum_{z \in N(u) \cap N(v)} \frac{1}{\log |N(z)|}$ computed on $G_t$.
7. **EvolveGCN-H:**
   * **Node Features:** Deterministic topological features computed on $G_t$ (in-degree, out-degree, total degree, $\log(1 + d_{\text{in}})$, $\log(1 + d_{\text{out}})$, degree ratio $\frac{d_{\text{in}}}{d_{\text{total}}}$).
   * **Hidden Dimension:** 16 channels.
   * **Weight Evolution:** Flattened GCN weights evolved via GRU: $W_t = \text{GRU}(\text{Pool}(X_t), W_{t-1})$.
   * **Training Split:** Optimized with Adam ($\text{lr}=0.005$) strictly on the training partition. Hidden state is evolved sequentially through validation into the test partition without gradient updates or future leakage.
   * **Decision Threshold:** Fixed canonical $\tau = 0.5$; no test-set threshold tuning.

---

## 6. Statistical Significance & Seeds
* **Random Seeds:** 5 fixed seeds: `[42, 100, 123, 456, 999]`.
* **Statistical Estimators:**
  * Sample mean $\bar{x} = \frac{1}{5} \sum_{i=1}^5 x_i$.
  * Sample standard deviation $s = \sqrt{\frac{1}{4} \sum_{i=1}^5 (x_i - \bar{x})^2}$.
  * 95% Confidence Interval: $\bar{x} \pm t_{0.025, 4} \cdot \frac{s}{\sqrt{5}}$ with critical value $t_{0.025, 4} = 2.776$.
* **Scope Limitation:** 5 seeds quantify candidate sampling and parameter initialization variance within fixed splits; they do not represent independent temporal test periods, nor do they establish general temporal shift invariance across unobserved timeframes. Candidate pools are stably sorted in lexicographical order prior to sampling or shuffling, ensuring 100% deterministic, process-independent candidate generation across separate Python environments regardless of `PYTHONHASHSEED`.
