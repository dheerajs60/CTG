import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score

class GenesisEngineModel(nn.Module):
    """Module 3 & 4: Proposed CTG Engine (GCN + GRU)."""
    def __init__(self, in_features, hidden_dim, num_nodes):
        super(GenesisEngineModel, self).__init__()
        self.num_nodes = num_nodes
        self.gcn = GCNConv(in_features, hidden_dim)
        self.gru = nn.GRUCell(hidden_dim, hidden_dim)
        
        self.decoder = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

    def forward(self, x, edge_index, h_state):
        spatial_emb = F.relu(self.gcn(x, edge_index))
        h_next = self.gru(spatial_emb, h_state)
        
        h_i = h_next.unsqueeze(1).repeat(1, self.num_nodes, 1)
        h_j = h_next.unsqueeze(0).repeat(self.num_nodes, 1, 1)
        pair_features = torch.cat([h_i, h_j], dim=-1)
        
        pred_adj = self.decoder(pair_features).squeeze(-1)
        return pred_adj, h_next

class BaselineStaticGCN(nn.Module):
    """Comparative Research Baseline: Static GCN Link Predictor (No Temporal Tracking)."""
    def __init__(self, in_features, hidden_dim, num_nodes):
        super(BaselineStaticGCN, self).__init__()
        self.num_nodes = num_nodes
        self.gcn1 = GCNConv(in_features, hidden_dim)
        self.gcn2 = GCNConv(hidden_dim, hidden_dim)
        self.decoder = nn.Sequential(
            nn.Linear(hidden_dim * 2, 1),
            nn.Sigmoid()
        )

    def forward(self, x, edge_index):
        h = F.relu(self.gcn1(x, edge_index))
        h = F.relu(self.gcn2(h, edge_index))
        
        h_i = h.unsqueeze(1).repeat(1, self.num_nodes, 1)
        h_j = h.unsqueeze(0).repeat(self.num_nodes, 1, 1)
        pair_features = torch.cat([h_i, h_j], dim=-1)
        return self.decoder(pair_features).squeeze(-1)

class EvaluationMetrics:
    """Research Evaluation Metrics helper for paper tables."""
    @staticmethod
    def compute_paper_metrics(y_true, y_pred_scores, threshold=0.08):
        y_pred_binary = (np.array(y_pred_scores) > threshold).astype(int)
        y_true = np.array(y_true).astype(int)

        precision = precision_score(y_true, y_pred_binary, zero_division=0)
        recall = recall_score(y_true, y_pred_binary, zero_division=0)
        f1 = f1_score(y_true, y_pred_binary, zero_division=0)
        try:
            auc = roc_auc_score(y_true, y_pred_scores)
        except ValueError:
            auc = 0.5

        return {
            'Precision': precision,
            'Recall': recall,
            'F1-Score': f1,
            'ROC-AUC': auc
        }

class GenesisViolationDetector:
    def __init__(self, violation_threshold=0.08):
        self.threshold = violation_threshold

    def compute_violation_score(self, pred_adj, actual_adj):
        diff = torch.abs(pred_adj - actual_adj)
        gv_score = torch.mean(diff).item()
        is_violation = gv_score > self.threshold
        return gv_score, is_violation

class TopologyGrammar:
    def __init__(self, num_nodes):
        self.grammar_weights = torch.zeros((num_nodes, num_nodes))

    def update_grammar(self, valid_adj, lr=0.1):
        self.grammar_weights = (1.0 - lr) * self.grammar_weights + lr * valid_adj.cpu()