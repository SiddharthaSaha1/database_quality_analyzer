"""
Isolation Forest Anomaly Detection Module
Primary unsupervised tree-based ensemble for isolating multidimensional outliers.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from utils.config import ML_CONTAMINATION, ML_RANDOM_STATE

class IsolationForestDetector:
    """Trains and executes Isolation Forest on student analytical feature vectors."""

    def __init__(self, contamination=ML_CONTAMINATION, random_state=ML_RANDOM_STATE, n_estimators=150):
        self.contamination = contamination
        self.random_state = random_state
        self.n_estimators = n_estimators
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=self.n_estimators,
            max_samples="auto"
        )
        self.is_fitted = False

    def fit_predict(self, X_scaled, analytical_df):
        """
        Fits Isolation Forest and predicts anomaly flags and normalized anomaly scores.
        Returns:
            results_df: analytical_df enriched with IF_ANOMALY (bool), IF_SCORE (float 0-1)
        """
        self.model.fit(X_scaled)
        self.is_fitted = True

        # raw_scores: lower values mean more anomalous (negative for outliers)
        decision_scores = self.model.decision_function(X_scaled)
        # binary preds: -1 for outlier, +1 for inlier
        raw_preds = self.model.predict(X_scaled)

        # Normalize score into [0.0, 1.0] where 1.0 = highly suspicious, 0.0 = completely normal
        min_s = decision_scores.min()
        max_s = decision_scores.max()
        if max_s > min_s:
            norm_scores = 1.0 - ((decision_scores - min_s) / (max_s - min_s))
        else:
            norm_scores = np.zeros_like(decision_scores)

        results_df = analytical_df.copy()
        results_df["IF_RAW_SCORE"] = decision_scores
        results_df["IF_ANOMALY_SCORE"] = np.round(norm_scores, 4)
        results_df["IF_IS_ANOMALOUS"] = (raw_preds == -1)

        return results_df

    def get_config(self):
        """Returns model hyperparameters and reproducibility parameters."""
        return {
            "algorithm": "Isolation Forest",
            "contamination": self.contamination,
            "random_state": self.random_state,
            "n_estimators": self.n_estimators,
            "is_fitted": self.is_fitted
        }

