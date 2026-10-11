# Comprehensive Limitations

## 1. Passive Telemetry Constraints
Both CIC-IDS2017 and UNSW-NB15 are passive packet/flow captures. They can record that two IP addresses exchanged packets, but they cannot inherently establish causal dependencies (e.g., that flow B happened *because* of flow A). This severely restricts topological interpretation.

## 2. Lack of Attack Replay Ground Truth
The evaluation dataset is immutable. Advanced counterfactual components (CGB, RGAR, Adaptive Defense) inherently require an environment where actions can be blocked and the attack process can be replayed to observe differing outcomes. Because this does not exist, these components are documented as strictly theoretical.

## 3. Persistence Baseline Supremacy
The chronological endpoint topology evaluation reveals an overwhelming short-term inertia. Endpoints communicating at timestep $t$ generally communicate at $t+1$. This establishes Persistence as a very hard-to-beat baseline, diluting the theoretical advantage of temporal graph convolutions in this domain.

## 4. Run-to-Run Variability
EvolveGCN-H displays considerable fluctuation across independent parameter seeds (42, 123, 999), raising concerns regarding its predictive stability against static persistence vectors.

## 5. Dataset Support
UNSW-NB15 provides robust flow parameters but natively lacks unified endpoint tracking matrices essential for constructing true chronological topologies matching CIC-IDS2017. As such, it is not utilized for the temporal graph tests to prevent corrupting evidence integrity.
