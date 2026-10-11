import json
import os
import copy

class AdaptiveDefenseResponse:
    """
    Module 9: Adaptive Defense and Response.
    Safe simulation-only response layer.
    """
    def __init__(self, log_dir='results/logs'):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.actions_log = []
        
    def propose_and_simulate(self, anomaly_evidence, proposed_intervention, target_graph):
        """
        Simulates the proposed intervention and verifies safety before logging.
        """
        if not proposed_intervention:
            return False, "No valid intervention found"
            
        # Simulate response
        mitigated = copy.deepcopy(target_graph)
        edges = set(tuple(e) for e in mitigated['edge_index'].t().tolist())
        
        edge_to_cut = proposed_intervention['edge']
        u, v = edge_to_cut
        if (u, v) in edges: edges.remove((u, v))
        if (v, u) in edges: edges.remove((v, u))
        
        # Safety Check (e.g., does it drop edges below a critical threshold)
        if len(edges) == 0 and target_graph['nodes'] > 2:
            return False, "Safety Violation: Intervention isolates the entire network."
            
        action_report = {
            'evidence': anomaly_evidence,
            'intervention': proposed_intervention,
            'status': 'SIMULATED_SUCCESS',
            'rollback_info': {'restored_edge': edge_to_cut}
        }
        
        self.actions_log.append(action_report)
        self._write_log()
        
        return True, action_report
        
    def _write_log(self):
        with open(os.path.join(self.log_dir, 'defense_actions.json'), 'w') as f:
            json.dump(self.actions_log, f, indent=4)
