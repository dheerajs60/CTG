import numpy as np
from sklearn.metrics import f1_score

class GenesisViolationDetector:
    """
    Module 5: Genesis Violation Detection without data leakage.
    """
    def __init__(self):
        self.threshold = 0.5
        self.is_fitted = False
        
    def fit(self, validation_gvs, validation_labels):
        """
        Select the optimal threshold using ONLY the validation set.
        """
        best_f1 = -1
        best_th = 0.5
        
        if len(set(validation_labels)) <= 1:
            # Fallback if validation set lacks attacks
            self.threshold = np.mean(validation_gvs) + 3 * np.std(validation_gvs)
            self.is_fitted = True
            return self
            
        for th in np.arange(0.01, 1.0, 0.01):
            preds = [1 if gv > th else 0 for gv in validation_gvs]
            f1 = f1_score(validation_labels, preds, zero_division=0)
            if f1 > best_f1:
                best_f1 = f1
                best_th = th
                
        self.threshold = best_th
        self.is_fitted = True
        return self
        
    def predict(self, gvs):
        if not self.is_fitted:
            raise ValueError("Detector must be fitted on validation data before calling predict.")
        return [1 if gv > self.threshold else 0 for gv in gvs]
