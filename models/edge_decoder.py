import torch
import torch.nn as nn

class MLPEdgeDecoder(nn.Module):
    """
    MLP Edge Decoder.
    Takes the concatenated node embeddings of source and destination and predicts
    the probability of an edge existing between them in the next temporal window.
    """
    def __init__(self, in_channels, hidden_channels=32):
        super(MLPEdgeDecoder, self).__init__()
        
        self.mlp = nn.Sequential(
            nn.Linear(in_channels * 2, hidden_channels),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_channels, 1),
            nn.Sigmoid()
        )
        
    def forward(self, node_emb, edge_index):
        """
        node_emb: Node embeddings from EvolveGCN (N, in_channels)
        edge_index: Pairs of nodes to predict edges for (2, E)
        """
        src, dst = edge_index
        
        # Concatenate embeddings: z_uv = [h_u || h_v]
        edge_features = torch.cat([node_emb[src], node_emb[dst]], dim=1)
        
        # Score and probability
        prob = self.mlp(edge_features).squeeze()
        return prob
