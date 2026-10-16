# Scientific Limitations and Threats to Validity

This document outlines the scientific boundaries, hardware constraints, and sampling limitations of the empirical link prediction benchmarks.

## 1. Empirical Scope & Dataset Constraints
* **Evaluated Datasets:** Findings are strictly restricted to the two evaluated telemetry streams:
  * **APEX-IDS2026:** 44 continuous days (2026-06-21 to 2026-08-03), hybrid-cloud enterprise deployment.
  * **CIC-IDS2017:** 5 days (2017-07-03 to 2017-07-07), controlled laboratory cyber range.
* **Temporal Horizon on CIC-IDS2017:** Under strict chronological partitioning (Days 0–2 train, Day 3 validation), the test evaluation contains **one daily transition** (Thursday to Friday). Sub-daily (1h, 6h) windowing partially mitigates this, but test evaluation represents a single calendar day.
* **Generalization Boundary:** Results do not generalize automatically to unobserved network architectures, operational ISP backbones, or disparate attack scenarios.

## 2. Statistical Unit & PRNG Seed Interpretation
* **Five Seeds (`[42, 100, 123, 456, 999]`):** The five seeds quantify candidate negative sampling variance and neural network initialization sensitivity. Within each seed run, all models are evaluated on strictly identical candidate sets. Across seeds, negative non-edge samples vary deterministically with the PRNG seed.
* **Deterministic Process Reproducibility:** Candidate pools and active node lists are stably sorted in lexicographical order prior to sampling or shuffling, ensuring 100% deterministic, process-independent candidate generation across separate Python environments regardless of `PYTHONHASHSEED`, as verified in unit regression tests.
* **Degrees of Freedom:** With $N=5$, degrees of freedom $\nu = 4$, resulting in a wide Student's $t$ multiplier ($t_{\text{crit}} = 2.776$ at 95% confidence).
* **Limitation:** Multiple seeds across fixed chronological splits do not quantify temporal non-stationarity, concept drift, or long-term seasonal shifts.

## 3. Negative Candidate Sampling & Base-Rate Fallacy
* **Balanced Candidate Benchmark:** Link prediction is evaluated on a balanced 1:1 positive-to-negative candidate set ($K \le 2000$ per step).
* **Base-Rate Fallacy:** In operational production environments, the ratio of active edges to possible non-edges exceeds $1 : 10^5$. Precision, ROC-AUC, and Average Precision reported under a 1:1 balanced candidate set evaluate controlled relative discriminative capacity, but cannot be directly extrapolated to operational detection precision or raw alert volumes.
* **Negative Regimes:** Setting A (Hard Historical Negatives: expired historical communication links) tests link extinction, while Setting B (Mixed Random Negatives) tests general non-edge discrimination.

## 4. Model Training & Optimization Boundaries
* **EvolveGCN-H Training Instability:** When trained purely on structural degree features without normalization layers or gradient clipping, vanilla EvolveGCN-H exhibits exceptionally large initial gradient norms in the link prediction head followed by pre-sigmoid logit saturation, accompanied by degenerate all-zero predictions on seed 456 on APEX-IDS2026 and seed 100 on CIC-IDS2017, and saturated all-one predictions on seed 123 on APEX-IDS2026. While large gradients and logit saturation occurred sequentially, demonstrating a definitive causal mechanism remains an unproven hypothesis requiring controlled ablation studies.
* **Heuristic Baselines:** Deterministic heuristics (Persistence, EdgeBank-tw, Common Neighbors) require no training and display near-zero sampling variance across evaluation seeds.

## 5. Causal & Counterfactual Exclusions
* **Passive Telemetry:** All evaluated telemetry is passive observational data. Causal counterfactual interventions (e.g., active traffic deflection, causal attack replay) cannot be validated on immutable logs and are explicitly decoupled from the empirical findings of this paper.
