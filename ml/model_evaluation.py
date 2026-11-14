"""
Model Evaluation and Comparison Module
Calculates intersection/union statistics between Isolation Forest and DBSCAN.
Evaluates metrics (Precision, Recall, F1, Confusion Matrix, FPR) when ground-truth labels exist.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

class ModelEvaluator:
    """Evaluates and compares unsupervised models and hybrid ensembles."""

    @staticmethod
    def compare_models(results_df):
        """
        Calculates cross-model agreement between Isolation Forest and DBSCAN.
        """
        if "IF_IS_ANOMALOUS" not in results_df.columns or "DBSCAN_IS_ANOMALOUS" not in results_df.columns:
            raise ValueError("Results DataFrame must contain IF_IS_ANOMALOUS and DBSCAN_IS_ANOMALOUS.")

        if_flags = results_df["IF_IS_ANOMALOUS"].astype(bool)
        db_flags = results_df["DBSCAN_IS_ANOMALOUS"].astype(bool)

        both_detected = results_df[if_flags & db_flags]
        if_only = results_df[if_flags & (~db_flags)]
        db_only = results_df[(~if_flags) & db_flags]
        either_detected = results_df[if_flags | db_flags]
        neither_detected = results_df[(~if_flags) & (~db_flags)]

        comparison = {
            "total_records": len(results_df),
            "isolation_forest_total": int(if_flags.sum()),
            "dbscan_total": int(db_flags.sum()),
            "both_count": len(both_detected),
            "if_only_count": len(if_only),
            "dbscan_only_count": len(db_only),
            "union_total": len(either_detected),
            "neither_count": len(neither_detected),
            "jaccard_similarity": round(len(both_detected) / max(1, len(either_detected)), 4)
        }
        return comparison

    @staticmethod
    def evaluate_ground_truth(y_true, y_pred, model_name="Model"):
        """
        Computes precision, recall, f1, and confusion matrix against ground truth.
        """
        y_t = np.array(y_true).astype(int)
        y_p = np.array(y_pred).astype(int)

        if len(y_t) == 0 or len(np.unique(y_t)) < 2:
            return {
                "model_name": model_name,
                "note": "Ground truth labels not available or single-class. Evaluation metrics cannot be calculated."
            }

        cm = confusion_matrix(y_t, y_p)
        # Handle binary matrix
        if cm.shape == (2, 2):
            tn, fp, fn, tp = cm.ravel()
        else:
            tn, fp, fn, tp = 0, 0, 0, 0

        prec = precision_score(y_t, y_p, zero_division=0)
        rec = recall_score(y_t, y_p, zero_division=0)
        f1 = f1_score(y_t, y_p, zero_division=0)
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

        return {
            "model_name": model_name,
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "false_positive_rate": round(float(fpr), 4),
            "true_positives": int(tp),
            "false_positives": int(fp),
            "true_negatives": int(tn),
            "false_negatives": int(fn),
            "total_samples": len(y_t)
        }

