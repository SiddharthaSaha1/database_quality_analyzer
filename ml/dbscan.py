"""
DBSCAN Density-Based Clustering and Anomaly Detection Module
Identifies noise records lying in sparse, low-density regions of the feature space.
"""

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from utils.config import DBSCAN_EPS, DBSCAN_MIN_SAMPLES

class DBSCANDetector:
    """Density-Based Spatial Clustering of Applications with Noise."""

    def __init__(self, eps=DBSCAN_EPS, min_samples=DBSCAN_MIN_SAMPLES, metric="euclidean"):
        self.eps = eps
        self.min_samples = min_samples
        self.metric = metric
        self.model = DBSCAN(eps=self.eps, min_samples=self.min_samples, metric=self.metric)
        self.is_fitted = False

    def fit_predict(self, X_scaled, analytical_df):
        """
        Executes DBSCAN clustering. Noise observations are assigned label -1.
        Returns:
            results_df: analytical_df enriched with DBSCAN_CLUSTER (int) and DBSCAN_IS_ANOMALOUS (bool).
        """
        labels = self.model.fit_predict(X_scaled)
        self.is_fitted = True

        results_df = analytical_df.copy()
        results_df["DBSCAN_CLUSTER"] = labels
        results_df["DBSCAN_IS_ANOMALOUS"] = (labels == -1)

        return results_df

    def get_config(self):
        return {
            "algorithm": "DBSCAN",
            "eps": self.eps,
            "min_samples": self.min_samples,
            "metric": self.metric,
            "is_fitted": self.is_fitted
        }

