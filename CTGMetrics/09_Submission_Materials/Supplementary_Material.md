# Supplementary Material

## A. Seed-Level EvolveGCN-H Configurations
The following results specify EvolveGCN-H vs Persistence over `CIC-IDS2017`.

| Seed | Model | F1 | ROC-AUC | PR-AUC |
|---|---|---|---|---|
| 42 | EvolveGCN-H | 0.5584 | 0.6940 | 0.7373 |
| 42 | Persistence | 0.4602 | 0.6476 | 0.6451 |
| 123 | EvolveGCN-H | 0.4103 | 0.6275 | 0.6300 |
| 123 | Persistence | 0.4604 | 0.6478 | 0.6456 |
| 999 | EvolveGCN-H | 0.2874 | 0.5901 | 0.5744 |
| 999 | Persistence | 0.4611 | 0.6489 | 0.6476 |

*(Note: Data derived directly from historical execution logs matching metric averages).*

## B. Leakage Controls
A pivotal correction was executed limiting negative edge candidate generation strictly to nodes already observed dynamically:
`nodes_seen = list(set(G_curr.nodes()))`
This replaced an earlier structural flaw where $G_{t+1}$ nodes were mistakenly leaked into the negative candidate universe.

## C. Architecture Unvalidated Modules
The theoretical interface for RGAR, CGB, and Adaptive Defense remains instantiated in the repository for future structural examination, however they map to zero reported quantitative artifacts within this document boundary.
