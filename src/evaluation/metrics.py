"""
Evaluation Metrics Module for Temporal Link Prediction.
Enforces strict distinction between classification metrics and ranking metrics.
"""

from typing import Dict, Any, List, Optional
import numpy as np
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, precision_score, 
    recall_score, f1_score, roc_auc_score, average_precision_score,
    confusion_matrix
)


def compute_classification_metrics(
    y_true: List[int],
    y_pred: List[int]
) -> Dict[str, Any]:
    """
    Computes thresholded binary classification metrics.
    Suitable for all models (both binary predictors and thresholded continuous scores).
    """
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    
    acc = accuracy_score(y_true, y_pred) * 100.0
    bacc = balanced_accuracy_score(y_true, y_pred) * 100.0
    prec = precision_score(y_true, y_pred, zero_division=0) * 100.0
    rec = recall_score(y_true, y_pred, zero_division=0) * 100.0
    spec = (tn / max(1, tn + fp)) * 100.0
    f1 = f1_score(y_true, y_pred, zero_division=0) * 100.0
    
    return {
        "accuracy": acc,
        "balanced_accuracy": bacc,
        "precision": prec,
        "recall": rec,
        "specificity": spec,
        "f1": f1,
        "confusion_matrix": {
            "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)
        }
    }


def compute_ranking_metrics(
    y_true: List[int],
    y_scores: np.ndarray,
    is_ranking_eligible: bool
) -> Dict[str, Any]:
    """
    Computes continuous ranking and area metrics:
    - ROC-AUC
    - Average Precision (PR-AUC)
    - Mean Reciprocal Rank (MRR)
    - Hits@10, Hits@50
    
    Strict Rule: If is_ranking_eligible is False, ranking metrics are mathematically
    invalid (degenerate step function) and return 'NOT EVALUABLE (Discrete Binary Predictor)'.
    """
    if not is_ranking_eligible:
        return {
            "roc_auc": "NOT EVALUABLE (Discrete Binary Predictor)",
            "average_precision": "NOT EVALUABLE (Discrete Binary Predictor)",
            "mrr": "NOT EVALUABLE (Discrete Binary Predictor)",
            "hits@10": "NOT EVALUABLE (Discrete Binary Predictor)",
            "hits@50": "NOT EVALUABLE (Discrete Binary Predictor)"
        }
        
    y_true_arr = np.array(y_true)
    classes = np.unique(y_true_arr)
    if len(classes) < 2:
        return {
            "roc_auc": "NOT EVALUABLE (Single Class Present)",
            "average_precision": "NOT EVALUABLE (Single Class Present)",
            "mrr": "NOT EVALUABLE (Single Class Present)",
            "hits@10": "NOT EVALUABLE (Single Class Present)",
            "hits@50": "NOT EVALUABLE (Single Class Present)"
        }
        
    try:
        roc = float(roc_auc_score(y_true_arr, y_scores))
    except Exception:
        roc = None
        
    try:
        ap = float(average_precision_score(y_true_arr, y_scores))
    except Exception:
        ap = None
        
    # Ranking metrics (sorting descending by score)
    # Higher score = higher rank (rank 1 = highest score)
    order = np.argsort(-y_scores)
    sorted_labels = y_true_arr[order]
    
    # Positive rank indices (1-indexed)
    pos_ranks = np.where(sorted_labels == 1)[0] + 1
    
    if len(pos_ranks) > 0:
        # Mean Reciprocal Rank across positive items
        mrr = float(np.mean(1.0 / pos_ranks))
        
        # Hits@K: proportion of positive edges appearing within top K
        n_pos = len(pos_ranks)
        hits10 = float(np.sum(pos_ranks <= 10) / n_pos)
        hits50 = float(np.sum(pos_ranks <= 50) / n_pos)
    else:
        mrr, hits10, hits50 = 0.0, 0.0, 0.0
        
    return {
        "roc_auc": roc,
        "average_precision": ap,
        "mrr": mrr,
        "hits@10": hits10,
        "hits@50": hits50
    }
