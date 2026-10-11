import torch
import torch.nn as nn

class EvolveGCNH(nn.Module):
    """
    EvolveGCN-H model for temporal graph edge prediction.
    Evolves GCN parameters over time using a GRU.
    """
    def __init__(self, num_nodes, in_channels, out_channels):
        super(EvolveGCNH, self).__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.weight_dim = in_channels * out_channels
        
        # GRU evolves the GCN weight matrix. Input is the pooled graph representation.
        self.gru = nn.GRU(in_channels, self.weight_dim)
        
        # Initial weight state
        self.initial_weight = nn.Parameter(torch.Tensor(self.weight_dim))
        nn.init.xavier_uniform_(self.initial_weight.view(in_channels, out_channels))
        
        # Edge prediction head (MLP over concatenated node embeddings)
        self.predictor = nn.Sequential(
            nn.Linear(out_channels * 2, out_channels),
            nn.ReLU(),
            nn.Linear(out_channels, 1)
        )
        
    def forward(self, x, edge_index, h_state=None):
        """Standard nn.Module forward pass delegating to forward_graph."""
        return self.forward_graph(x, edge_index, h_state)

    def forward_graph(self, x, edge_index, h_state=None):
        """
        Processes a single graph snapshot and returns node embeddings and the updated hidden state.
        x: Node features (N, in_channels)
        edge_index: Graph connectivity (2, E)
        h_state: Previous GRU hidden state
        """
        if x.size(0) == 0:
            return x, h_state

        # Mean pooling for graph summary
        Z_t = x.mean(dim=0).unsqueeze(0).unsqueeze(0)
        
        if h_state is None:
            h_state = self.initial_weight.unsqueeze(0).unsqueeze(0)
            
        # Evolve weights
        out, h_state = self.gru(Z_t, h_state)
        W_t = h_state.squeeze().view(self.in_channels, self.out_channels)
        
        # Linear transformation
        xw = torch.matmul(x, W_t)
        
        # Simplified Message Passing (GCN)
        row, col = edge_index
        num_nodes = x.size(0)
        
        # Add self loops
        loop_index = torch.arange(0, num_nodes, dtype=torch.long, device=x.device)
        loop_edge_index = torch.stack([loop_index, loop_index], dim=0)
        
        if row.size(0) > 0:
            full_edge_index = torch.cat([edge_index, loop_edge_index], dim=1)
        else:
            full_edge_index = loop_edge_index
            
        row, col = full_edge_index
        
        # Degree normalization
        deg = torch.zeros(num_nodes, device=x.device)
        deg.scatter_add_(0, row, torch.ones(row.size(0), device=x.device))
        deg_inv_sqrt = deg.pow(-0.5)
        deg_inv_sqrt[deg_inv_sqrt == float('inf')] = 0
        norm = deg_inv_sqrt[row] * deg_inv_sqrt[col]
        
        # Aggregate
        out_node_emb = torch.zeros(num_nodes, self.out_channels, device=x.device)
        out_node_emb.scatter_add_(0, row.unsqueeze(-1).expand(-1, self.out_channels), xw[col] * norm.unsqueeze(-1))
        
        return torch.relu(out_node_emb), h_state

    def predict_edges(self, node_emb, edge_candidates):
        """
        edge_candidates: (2, num_candidates)
        Returns: logits for edge existence
        """
        if edge_candidates.size(1) == 0:
            return torch.zeros((0, 1), device=node_emb.device)
            
        src = edge_candidates[0]
        dst = edge_candidates[1]
        
        src_emb = node_emb[src]
        dst_emb = node_emb[dst]
        
        emb_cat = torch.cat([src_emb, dst_emb], dim=1)
        logits = self.predictor(emb_cat)
        return logits.squeeze(-1)
