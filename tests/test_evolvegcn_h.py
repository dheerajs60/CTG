import torch
from models.evolve_gcn import EvolveGCNH
import os

def test_evolvegcn_forward():
    num_nodes = 5
    in_channels = 8
    out_channels = 4
    
    model = EvolveGCNH(num_nodes=num_nodes, in_channels=in_channels, out_channels=out_channels)
    
    # Snapshot 1
    x1 = torch.rand((num_nodes, in_channels))
    edge_index1 = torch.tensor([[0, 1, 2], [1, 2, 3]], dtype=torch.long)
    
    emb1, h_state1 = model.forward_graph(x1, edge_index1)
    
    assert emb1.shape == (num_nodes, out_channels)
    assert h_state1 is not None
    
    # Predict edges
    candidates = torch.tensor([[0, 3], [2, 4]], dtype=torch.long)
    logits = model.predict_edges(emb1, candidates)
    assert logits.shape == (2,)
    
    # Snapshot 2 (pass hidden state)
    x2 = torch.rand((num_nodes, in_channels))
    edge_index2 = torch.tensor([[1, 3], [0, 4]], dtype=torch.long)
    
    emb2, h_state2 = model.forward_graph(x2, edge_index2, h_state=h_state1)
    
    assert emb2.shape == (num_nodes, out_channels)
    # Ensure state advanced
    assert not torch.allclose(h_state1, h_state2)
    
    # Backprop test
    loss = logits.sum()
    loss.backward()
    
    assert model.initial_weight.grad is not None
    print("EvolveGCN-H tests passed!")

if __name__ == "__main__":
    test_evolvegcn_forward()
