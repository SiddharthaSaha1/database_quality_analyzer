"""
Machine Learning Anomaly Explanation Engine
Derives factual, evidence-based mathematical explanations for ML outliers
by assessing feature z-scores and multivariate deviation from normal population baselines.
"""

import numpy as np
import pandas as pd

class AnomalyExplainer:
    """Computes exact mathematical explanations for flagged anomalies."""

    FEATURE_DESCRIPTIONS = {
        "ATTENDANCE_VS_MARKS_GAP": "Attendance vs Exam Score Discrepancy",
        "ATTENDANCE_CONSISTENCY": "Attendance Percentage vs Ratio Mismatch",
        "ATTENDANCE_PERCENTAGE": "Attendance Rate",
        "MARKS_PERCENTAGE": "Exam Score Percentage",
        "AGE": "Student Age",
        "YEAR_OF_STUDY": "Academic Year of Study"
    }

    @staticmethod
    def explain_record(row, feature_stats):
        """
        Calculates feature-level deviations (z-scores) against feature_stats dict.
        Returns:
            primary_reason (str), relevant_column (str), deviation_summary (dict)
        """
        reasons = []
        max_dev = -1.0
        primary_col = "MULTIVARIATE"

        for col, stats in feature_stats.items():
            if col not in row or pd.isna(row[col]):
                continue
            val = float(row[col])
            mean = stats["mean"]
            std = stats["std"] if stats["std"] > 1e-6 else 1.0

            z_score = abs(val - mean) / std

            # Check significant deviations (e.g. z > 2.2)
            if z_score >= 2.2:
                col_name = AnomalyExplainer.FEATURE_DESCRIPTIONS.get(col, col)
                direction = "higher" if val > mean else "lower"
                detail = f"{col_name} ({val:.1f}) is {z_score:.1f}σ {direction} than cohort mean ({mean:.1f})"
                reasons.append((z_score, detail, col))

                if z_score > max_dev:
                    max_dev = z_score
                    primary_col = col

        if reasons:
            # Sort by highest statistical deviation
            reasons.sort(key=lambda x: x[0], reverse=True)
            explanation = "; ".join([r[1] for r in reasons[:3]])
        else:
            explanation = "Multivariate density outlier: record lies in an isolated low-density region of the feature space."

        return explanation, primary_col

    @staticmethod
    def compute_population_stats(analytical_df):
        """Precomputes mean, std, median for feature columns across dataset."""
        features = ["AGE", "YEAR_OF_STUDY", "ATTENDANCE_PERCENTAGE", "MARKS_PERCENTAGE", 
                    "ATTENDANCE_CONSISTENCY", "ATTENDANCE_VS_MARKS_GAP"]
        stats = {}
        for feat in features:
            if feat in analytical_df.columns:
                series = pd.to_numeric(analytical_df[feat], errors="coerce").dropna()
                stats[feat] = {
                    "mean": float(series.mean()) if not series.empty else 0.0,
                    "std": float(series.std()) if not series.empty else 1.0,
                    "median": float(series.median()) if not series.empty else 0.0,
                    "q25": float(series.quantile(0.25)) if not series.empty else 0.0,
                    "q75": float(series.quantile(0.75)) if not series.empty else 0.0,
                }
        return stats

