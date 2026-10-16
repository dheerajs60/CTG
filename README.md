# Temporal Link Prediction in Network Security Telemetry

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://img.shields.io/badge/Dataset%20DOI-10.5281%2Fzenodo.22013914-blue.svg)](https://doi.org/10.5281/zenodo.22013914)
[![Audit](https://img.shields.io/badge/Reviewer%20Audit-100%25%20Resolved-brightgreen.svg)]()

> **Evaluating Graph Dynamics, Heuristic Baselines, and Negative Sampling Regimes in Network Security Telemetry**  
> *Author:* Dheeraj Kovoord & Research Team  
> *Paper Manuscript:* [`paper/manuscript.md`](paper/manuscript.md) | [PDF](paper/manuscript.pdf) | [DOCX](paper/manuscript.docx) | [HTML](paper/manuscript.html)

---

## 1. Overview & Research Scope

This repository hosts the official empirical benchmark, datasets, candidate samplers, and baseline implementations for studying **temporal link prediction in dynamic network telemetry graphs**. 

Rather than relying on synthetic attack generation or unverifiable counterfactual assertions, this study provides a rigorous, empirical investigation into:
1. **Multi-Scale Topological Churn:** Quantifying directional edge novelty ($N_t$), recurrence ($R_t$), and symmetric set turnover ($T_{\text{Jaccard}}$) across enterprise telemetry (**APEX-IDS2026**, 44 continuous days, 69.1M flows) and laboratory cyber-range data (**CIC-IDS2017**, 5 days, 2.83M flows).
2. **The Negative Sampling Illusion:** Demonstrating how uniform random negative sampling (Setting B) creates an illusion of near-perfect temporal understanding ($\ge 99.8\%$ precision), whereas evaluating against hard historical link extinctions (Setting A) causes precision to collapse dramatically (e.g., $34.43\%$ on CIC and $47.02\%$ on APEX for unbounded memory).
3. **Competitive Heuristic Baselines:** Establishing that simple sliding-window memory (`EdgeBank-tw`, $W=2$) and local topological proximity (`Common Neighbors`) outperform complex neural architectures on raw network topologies.
4. **Recurrent GNN Optimization Boundaries:** Evaluating an adapted EvolveGCN-H variant on deterministic structural degree features, documenting seed sensitivity, finite-precision logit saturation, and degenerate collapse modes without synthetic fabrication.

---

## 2. Telemetry Datasets & Provenance

| Property | APEX-IDS2026 (Enterprise Telemetry) | CIC-IDS2017 (Cyber-Range Testbed) |
| :--- | :--- | :--- |
| **Capture Span** | 44 continuous days (2026-06-21 to 2026-08-03) | 5 weekdays (2017-07-03 to 2017-07-07) |
| **Total Flows** | 69,107,018 curated flows (53 features) | 2,830,743 flows |
| **Unique Endpoints** | 412,906 source IPs, 42,421 destination IPs | Multi-department synthetic LAN |
| **24h Snapshots** | 44 daily graphs ($203,444 \pm 40,234$ edges/day) | 5 daily graphs ($35,224 \pm 2,745$ edges/day) |
| **Boundary Days** | Truncated start (Day 0) and end (Day 43) flagged | Discrete daytime simulation runs |
| **Splits** | Train: Days 0–24 (25d), Val: Days 25–31 (7d), Test: Days 32–43 (12 transitions) | Train: Days 0–2 (Mon–Wed), Val: Day 3 (Thu), Test: Day 4 (Fri, 1 transition) |
| **Provenance** | Zenodo DOI: [`10.5281/zenodo.22013914`](https://doi.org/10.5281/zenodo.22013914) (CC BY 4.0)<br>Archive MD5: `115ed72bb8759d3ce90fe17c52a0ee98`<br>Parquet SHA-256: `7e7855964ddc8061804fa48acfd6c2a3e1891462466654f9294cdab58744730c` | Public release: Canadian Institute for Cybersecurity (UNB) |

---

## 3. Negative Sampling Regimes

Dynamic link prediction benchmarks are critically defined by how negative non-edges are selected:

* **Setting A (Hard Historical Negatives):**  
  $$E_{\text{neg}}^{\text{hard}}(t+1) \subseteq \{(u, v) \in E_{\le t} \setminus E_{t+1} \mid u, v \in V_{\le t}\}$$  
  Negative candidate links are sampled strictly from historically active channels that ceased transmission at $t+1$. This directly evaluates the model's ability to detect **temporal link extinction**.
* **Setting B (Mixed Random Negatives):**  
  $$E_{\text{neg}}^{\text{mixed}}(t+1) \subseteq \{(u, v) \in V_t \times V_t \mid (u, v) \notin E_{t+1}, u \neq v\}$$  
  Negative candidate links are sampled uniformly from non-edges between hosts active in snapshot $t$.
* **Candidate-Universe Asymmetry Limitation:** Setting B negatives are drawn strictly from active pairs ($V_t \times V_t$), while positive evaluation candidates include $\approx 18-21\%$ dormant re-emerging historical endpoints ($V_{<t} \setminus V_t$). Expanding negatives to $V_{\le t} \times V_{\le t}$ creates extreme candidate sparsity dominated by long-dead endpoints, whereas restricting positives discards $>18\%$ of real traffic. We report this candidate-universe asymmetry as an explicit methodological limitation.

---

## 4. Evaluated Models

1. **Persistence:** Predicts that edges active in snapshot $t$ persist into $t+1$ ($\hat{y} = \mathbb{I}[(u, v) \in E_t]$).
2. **EdgeBank-∞ (Binary & Frequency):** Unbounded historical memory retaining all observed edges without decay ($\hat{y} = \mathbb{I}[(u, v) \in E_{\le t}]$).
3. **EdgeBank-tw (Time-Windowed Memory):** Sliding-window memory over the preceding $W=2$ snapshots.
4. **Common Neighbors (Directed):** Structural overlap $|N_{\text{out}}(u) \cap N_{\text{in}}(v)|$ with integer threshold $\tau = 1.0$.
5. **Jaccard Coefficient (Undirected):** Neighbor overlap normalized by union degree. Threshold-free ROC-AUC/AP reveals true continuous ranking capacity despite fixed-threshold artifacts.
6. **Adamic-Adar (Undirected):** Degree-weighted shared neighbor summation penalizing high-degree hubs.
7. **Adapted EvolveGCN-H:** Recurrent graph neural network where GCN parameters are updated across discrete snapshots via vectorized GRU states driven by mean-pooled global graph summary vectors $Z_t$. Trained on 6 deterministic structural degree features (in-degree, out-degree, total degree, $\log(1+d_{\text{in}})$, $\log(1+d_{\text{out}})$, degree ratio).

---

## 5. Key Benchmark Results

### 5.1 Multi-Scale Graph Dynamics (Table 1)
| Dataset | Window Scale | Windows | Transitions | Mean Edges/Win | Recurrence ($R_t$) | Novelty ($N_t$) | Jaccard Turnover ($T_{\text{Jaccard}}$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **APEX-IDS2026** | **24h (Daily)** | 44 | 43 | 203,444 | $43.75\% \pm 6.07\%$ | $56.25\% \pm 6.07\%$ | $72.71\% \pm 4.15\%$ |
| APEX-IDS2026 | **12h** | 86 | 85 | 132,166 | $42.74\% \pm 3.86\%$ | $57.26\% \pm 3.86\%$ | $73.12\% \pm 2.68\%$ |
| APEX-IDS2026 | **6h** | 170 | 169 | 83,912 | $40.33\% \pm 3.85\%$ | $59.67\% \pm 3.85\%$ | $74.86\% \pm 2.77\%$ |
| **CIC-IDS2017** | **24h (Daily)** | 5 | 4 | 35,224 | $31.91\% \pm 1.48\%$ | $68.09\% \pm 1.48\%$ | $81.61\% \pm 0.49\%$ |
| CIC-IDS2017 | **6h (Sub-Daily)** | 15 | 14 | 14,019 | $27.81\% \pm 16.92\%$ | $72.19\% \pm 16.92\%$ | $90.84\% \pm 4.80\%$ |
| CIC-IDS2017 | **1h (Fine)** | 50 | 49 | 5,133 | $23.29\% \pm 18.87\%$ | $76.71\% \pm 18.87\%$ | $92.11\% \pm 4.36\%$ |

### 5.2 Five-Seed Benchmark Performance (Tables 2 & 3, Setting A)
* **Enterprise Telemetry (APEX-IDS2026):** `EdgeBank-tw(W=2)` achieves the highest overall F1 (**$69.78\% \pm 0.08\%$**, Precision $85.04\%$, Recall $60.01\%$), outperforming both Persistence ($64.09\%$ F1) and unbounded EdgeBank-∞ ($61.47\%$ F1).
* **Cyber-Range Telemetry (CIC-IDS2017):** In high-churn conditions, `Common Neighbors` achieves the highest F1 (**$45.24\% \pm 0.24\%$**, Precision $62.97\%$), outperforming Persistence ($35.22\%$ F1) and EdgeBank-tw ($40.40\%$ F1).
* **The Memory Failure Mechanism:** Under Setting A, EdgeBank-∞ scores 100% of sampled hard negatives as positive ($TN=0, FP=K$), collapsing precision to **$34.43\%$ on CIC** and **$47.02\%$ on APEX**.
* **Uncapped Test Continuous Discrimination (APEX $N=3,256,518$ pairs):** EvolveGCN-H achieves a continuous ROC-AUC of **$0.9705 \pm 0.0035$** and PR-AUC of **$0.9716 \pm 0.0028$** (Persistence: ROC-AUC $0.8130$). Stratified recall shows Persistence detects $100\%$ of recurring edges but $0\%$ of new edges ($62.6\%$ overall recall), whereas EvolveGCN-H detects $94.37\%$ of recurring edges and $81.12\%$ of newly emerging edges between active endpoints.

---

## 6. Figure Suite (Figures 1–13)

All publication figures are provided in high-resolution PNG (300 dpi) and vector PDF in `figures/`:

* **`figures/fig01_pipeline_architecture.png`**: Methodological 5-stage empirical workflow pipeline.
* **`figures/fig02_dataset_scale_comparison.png`**: Flow volume, edge counts, node scale, and duration comparison.
* **`figures/fig03_chronological_topology_trajectories.png`**: Daily active node and edge trajectories across partitions.
* **`figures/fig04_transition_flux_added_removed.png`**: Chronological added, retained, and expired edge flux on APEX.
* **`figures/fig05_multiscale_dynamics_rates.png`**: Multi-scale recurrence, novelty, and turnover bar charts.
* **`figures/fig06_benchmark_performance_setting_a.png`**: 8-model performance under Hard Historical Negatives.
* **`figures/fig07_benchmark_setting_comparison_full.png`**: Negative sampling illusion (Setting A vs. Setting B).
* **`figures/fig08_per_seed_evolvegcn_diagnostics.png`**: Per-seed EvolveGCN variance and collapse modes.
* **`figures/fig09_memory_failure_confusion_matrices.png`**: EdgeBank memory failure ($TN=0$) confusion matrices.
* **`figures/fig10_topology_whitelist_failure_audit.png`**: Topology grammar whitelist failure (91.4% false alarms).
* **`figures/fig11_continuous_vs_thresholded_heuristics.png`**: Thresholded F1 vs ROC-AUC/AP continuous ranking.
* **`figures/fig12_roc_and_pr_curves_apex.png`**: Continuous ROC and PR curves on 3,256,518 APEX candidate pairs.
* **`figures/fig13_classification_confusion_matrices.png`**: Empirical 2x2 confusion matrices with exact candidate counts.

---

## 7. Quickstart & Reproduction

### 7.1 Setup Environment
```bash
# Clone repository
git clone https://github.com/dheerajs60/CTG.git
cd CTG

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 7.2 Run Unit Regression Tests
```bash
# Runs 17 unit regression tests verifying candidate stratification, determinism, and models
pytest tests/test_baselines_and_sampling.py tests/test_evolvegcn_h.py tests/test_gv_math.py
```

### 7.3 Recompute Metrics & Benchmarks
```bash
# 1. Multi-scale graph dynamics (Table 1)
python3 scripts/analyze_multi_scale_dynamics.py

# 2. Five-seed benchmark across Setting A and Setting B (Tables 2 & 3)
python3 scripts/run_five_seed_benchmark.py

# 3. Uncapped enterprise continuous evaluation (Figures 12 & 13)
python3 scripts/run_evolvegcn_apex.py
```

### 7.4 Compile Manuscript Documents
```bash
cd paper/

# Generate standalone MathJax HTML
pandoc manuscript.md -s --mathjax -o manuscript.html

# Generate Microsoft Word DOCX
pandoc manuscript.md -o manuscript.docx

# Generate Publication PDF (via Google Chrome Headless)
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu --print-to-pdf=manuscript.pdf manuscript.html
```

---

## 8. Repository Layout

```
.
├── figures/                          # Verified publication figures (Figures 1 to 13, PNG & PDF)
├── models/                           # Predictor implementations
│   ├── baselines.py                  # Persistence, EdgeBank, Common Neighbors, Jaccard, Adamic-Adar
│   └── evolve_gcn.py                 # EvolveGCN-H with deterministic topological features
├── paper/                            # Manuscript sources and compiled documents
│   ├── manuscript.md                 # Markdown paper source (445 lines)
│   ├── manuscript.pdf                # Publication PDF (embedded figures)
│   ├── manuscript.docx               # Formatted Word document
│   ├── manuscript.html               # Standalone MathJax HTML document
│   ├── EXPERIMENT_PROTOCOL.md        # Definitive candidate sampling protocol
│   └── LIMITATIONS.md                # Detailed threats to validity
├── results/metrics/                  # Machine-readable evaluation outputs
│   ├── apex_dynamics_{6h,12h,24h}.csv
│   ├── cic_dynamics_{1h,6h,24h}.csv
│   ├── benchmark_five_seed_results.json
│   └── benchmark_five_seed_summary.csv
├── scripts/                          # Experiment execution scripts
│   ├── analyze_multi_scale_dynamics.py
│   ├── run_five_seed_benchmark.py
│   └── run_evolvegcn_apex.py
├── src/evaluation/                   # Evaluation infrastructure
│   ├── candidate_sampler.py          # Strict anti-leakage candidate samplers
│   └── metrics.py                    # Threshold-free and classification metrics
└── tests/                            # Pytest test suite (17 passed tests)
    ├── test_baselines_and_sampling.py
    ├── test_evolvegcn_h.py
    └── test_gv_math.py
```

---

## 9. License & Citation

The source code and benchmark scripts are released under the [MIT License](LICENSE).  
The APEX-IDS2026 dataset is distributed under the [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) license (DOI: `10.5281/zenodo.22013914`).

If you find this work or benchmark useful, please cite:
```bibtex
@article{kovoord2026temporal,
  title={Temporal Link Prediction in Network Security Telemetry: Evaluating Graph Dynamics, Heuristic Baselines, and Negative Sampling Regimes},
  author={Kovoord, Dheeraj and Research Team},
  journal={arXiv preprint},
  year={2026}
}
```

