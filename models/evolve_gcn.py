import torch
import torch.nn as nn

def compute_topological_node_features(edge_index: torch.Tensor, num_nodes: int, feature_dim: int, device=None) -> torch.Tensor:
    """
    Constructs deterministic topological node features from the graph structure:
    - in-degree, out-degree, total degree
    - log(1 + in_degree), log(1 + out_degree)
    - in/out ratio
    Padded with positional structural encodings to feature_dim.
    Eliminates reliance on purely random Gaussian noise vectors.
    """
    if device is None:
        device = edge_index.device if edge_index.numel() > 0 else torch.device('cpu')
        
    features = torch.zeros((num_nodes, feature_dim), dtype=torch.float, device=device)
    if num_nodes == 0:
        return features
        
    in_deg = torch.zeros(num_nodes, dtype=torch.float, device=device)
    out_deg = torch.zeros(num_nodes, dtype=torch.float, device=device)
    
    if edge_index.numel() > 0 and edge_index.size(1) > 0:
        src, dst = edge_index[0], edge_index[1]
        out_deg.scatter_add_(0, src, torch.ones_like(src, dtype=torch.float, device=device))
        in_deg.scatter_add_(0, dst, torch.ones_like(dst, dtype=torch.float, device=device))
        
    total_deg = in_deg + out_deg
    log_in = torch.log1p(in_deg)
    log_out = torch.log1p(out_deg)
    ratio = in_deg / (total_deg + 1e-6)
    
    base_feats = torch.stack([in_deg, out_deg, total_deg, log_in, log_out, ratio], dim=1)
    k = min(feature_dim, base_feats.size(1))
    features[:, :k] = base_feats[:, :k]
    return features


class EvolveGCNH(nn.Module):
    """
    EvolveGCN-H (Pareja et al., AAAI 2020) for Temporal Graph Link Prediction.
    
    Mathematical Formulation:
      Input graph summary: Z_t = Pool(X_t) in R^{in_channels}
      Hidden state (flattened GCN weights): W_{t-1} in R^{in_channels * out_channels}
      Weight evolution: W_t = GRU(Z_t, W_{t-1})
      Graph Convolution: H_t = ReLU( D_tilde^{-1/2} A_tilde D_tilde^{-1/2} X_t W_t )
      Edge Prediction: s(u, v) = MLP( [h_u || h_v] )
    """
    def __init__(self, num_nodes, in_channels, out_channels):
        super(EvolveGCNH, self).__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.weight_dim = in_channels * out_channels
        
        # GRU evolves the flattened GCN weight matrix. Input is the pooled graph representation.
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
