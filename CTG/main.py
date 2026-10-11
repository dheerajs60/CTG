import torch
import torch.nn as nn
from dataset_parser import NetworkDatasetParser
from ctg_engine import GenesisEngineModel, GenesisViolationDetector, TopologyGrammar
from rgar_cgb_search import ReverseGenesisReconstruction, CounterfactualGenesisBarrier

def generate_cisco_ios_acl(src_ip, dst_ip):
    return f"""
========================================================================
             AUTOMATED CISCO PACKET TRACER MITIGATION SCRIPT            
========================================================================
Paste the following CLI commands into your Packet Tracer Core Router:

Router# configure terminal
Router(config)# ip access-list extended CTG_COUNTERFACTUAL_BARRIER
Router(config-ext-nacl)# deny ip host {src_ip} host {dst_ip}
Router(config-ext-nacl)# permit ip any any
Router(config-ext-nacl)# exit
Router(config)# interface GigabitEthernet0/0
Router(config-if)# ip access-group CTG_COUNTERFACTUAL_BARRIER in
Router(config-if)# end
Router# write memory
========================================================================"""

def run_ctg_architecture():
    print("=========================================================================")
    print("   CTG: COUNTERFACTUAL TOPOLOGY GENESIS ARCHITECTURE PIPELINE")
    print("=========================================================================\n")

    print("[Module 1 & 2] Loading network data and slicing into temporal graphs...")
    parser = NetworkDatasetParser(window_size_seconds=10)
    graphs, num_nodes = parser.parse_csv_to_temporal_graphs("network_flows.csv")
    print(f"    --> Total Nodes Indexed: {num_nodes}")
    print(f"    --> Total Temporal Windows: {len(graphs)}\n")

    train_graphs = graphs[:7]
    test_graphs = graphs[7:]

    hidden_dim = 16
    model = GenesisEngineModel(in_features=3, hidden_dim=hidden_dim, num_nodes=num_nodes)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_fn = nn.MSELoss()

    detector = GenesisViolationDetector(violation_threshold=0.08)
    grammar = TopologyGrammar(num_nodes=num_nodes)
    rgar_search = ReverseGenesisReconstruction(max_search_depth=5)
    cgb_engine = CounterfactualGenesisBarrier(model)

    print("[Module 3 & 4] Training Topology Genesis Engine on normal sequence...")
    model.train()
    for epoch in range(50):
        h_state = torch.zeros(num_nodes, hidden_dim)
        total_loss = 0.0
        for t in range(len(train_graphs) - 1):
            curr_g = train_graphs[t]
            next_g = train_graphs[t+1]

            optimizer.zero_grad()
            pred_adj, h_state = model(curr_g['x'], curr_g['edge_index'], h_state.detach())
            loss = loss_fn(pred_adj, next_g['adj'])
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            grammar.update_grammar(next_g['adj'])

    print("    --> Model training and baseline grammar initialization complete.\n")

    print("[Module 5, 6, 7 & 8] Processing live streaming test windows...")
    model.eval()
    h_state = torch.zeros(num_nodes, hidden_dim)

    with torch.no_grad():
        for i in range(len(test_graphs) - 1):
            curr_g = test_graphs[i]
            target_g = test_graphs[i+1]
            t_span = target_g['time_range']

            pred_adj, h_state = model(curr_g['x'], curr_g['edge_index'], h_state)

            gv_score, is_violation = detector.compute_violation_score(pred_adj, target_g['adj'])
            print(f"-------------------------------------------------------------------------")
            print(f"Window [{t_span[0]:.0f}s - {t_span[1]:.0f}s] | GV_t Score: {gv_score:.4f} | Status: {'[VIOLATION]' if is_violation else '[NORMAL]'}")

            if is_violation:
                print("\n  [!] ANOMALOUS TOPOLOGY DETECTED! Triggering CTG Analysis...")
                
                path = rgar_search.reconstruct_attack_path(target_g['adj'], curr_g['adj'])
                print("\n  [Module 6: RGAR] Reconstructed Attack Genesis Transformation Path (Pi*):")
                for step_idx, edge in enumerate(path, 1):
                    src_ip = parser.node_to_ip[edge[0]]
                    dst_ip = parser.node_to_ip[edge[1]]
                    print(f"    Step {step_idx}: REMOVE_TRANSFORMATION ({src_ip} <---> {dst_ip})")

                barrier = cgb_engine.find_minimal_intervention(target_g, h_state)
                if barrier:
                    b_src = parser.node_to_ip[barrier['edge'][0]]
                    b_dst = parser.node_to_ip[barrier['edge'][1]]
                    print("\n  [Module 7: CGB] Computed Counterfactual Genesis Barrier (B*):")
                    print(f"    --> Recommended Minimal Structural Edit: BLOCK_LINK ({b_src} <---> {b_dst})")
                    print(f"    --> Intervention Disruption Penalty:    {barrier['cost']}")
                    print(f"    --> Predicted Post-Barrier Residual Risk: {barrier['residual_risk']:.4f}")
                    
                    # Module 9 Output
                    print(generate_cisco_ios_acl(b_src, b_dst))
            else:
                grammar.update_grammar(target_g['adj'])
                print("  [Module 8] Normal evolution confirmed. Updated Legitimate Grammar Weights.")

if __name__ == "__main__":
    run_ctg_architecture()