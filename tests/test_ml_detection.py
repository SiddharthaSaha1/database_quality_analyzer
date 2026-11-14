"""
Unit and Integration Tests for Machine Learning Anomaly Detection
Tests Preprocessing, Isolation Forest, DBSCAN, Anomaly Explainer, and Model Evaluator.
"""

import pytest
import numpy as np
import pandas as pd
from database.connection import CSVDatabaseAdapter
from ml.preprocessing import MLPreprocessor
from ml.isolation_forest import IsolationForestDetector
from ml.dbscan import DBSCANDetector
from ml.anomaly_explainer import AnomalyExplainer
from ml.model_evaluation import ModelEvaluator

@pytest.fixture
def corrupted_tables():
    adapter = CSVDatabaseAdapter(mode="corrupted")
    return adapter.fetch_all_tables()

def test_ml_preprocessing_pipeline(corrupted_tables):
    preprocessor = MLPreprocessor()
    analytical_df = preprocessor.build_analytical_dataset(corrupted_tables)
    assert not analytical_df.empty
    assert "MARKS_PERCENTAGE" in analytical_df.columns
    assert "ATTENDANCE_VS_MARKS_GAP" in analytical_df.columns
    assert "COMPOSITE_RECORD_ID" in analytical_df.columns

    X_scaled, X_df, full_df = preprocessor.prepare_features(analytical_df)
    assert X_scaled.shape[0] == len(analytical_df)
    assert not np.isnan(X_scaled).any(), "Scaled feature matrix should contain no unhandled NaNs."

def test_isolation_forest_execution(corrupted_tables):
    preprocessor = MLPreprocessor()
    analytical_df = preprocessor.build_analytical_dataset(corrupted_tables)
    X_scaled, _, _ = preprocessor.prepare_features(analytical_df)

    if_detector = IsolationForestDetector(contamination=0.08, random_state=42)
    results_df = if_detector.fit_predict(X_scaled, analytical_df)

    assert "IF_IS_ANOMALOUS" in results_df.columns
    assert "IF_ANOMALY_SCORE" in results_df.columns
    assert results_df["IF_IS_ANOMALOUS"].sum() > 0
    # Check normalized score bounds [0.0, 1.0]
    assert results_df["IF_ANOMALY_SCORE"].min() >= 0.0
    assert results_df["IF_ANOMALY_SCORE"].max() <= 1.0

def test_dbscan_execution(corrupted_tables):
    preprocessor = MLPreprocessor()
    analytical_df = preprocessor.build_analytical_dataset(corrupted_tables)
    X_scaled, _, _ = preprocessor.prepare_features(analytical_df)

    db_detector = DBSCANDetector(eps=0.8, min_samples=4)
    results_df = db_detector.fit_predict(X_scaled, analytical_df)

    assert "DBSCAN_IS_ANOMALOUS" in results_df.columns
    assert "DBSCAN_CLUSTER" in results_df.columns
    # Check that noise (-1) is correctly mapped to anomalous
    noise_count = (results_df["DBSCAN_CLUSTER"] == -1).sum()
    flagged_count = results_df["DBSCAN_IS_ANOMALOUS"].sum()
    assert noise_count == flagged_count

def test_model_comparison_and_explanation(corrupted_tables):
    preprocessor = MLPreprocessor()
    analytical_df = preprocessor.build_analytical_dataset(corrupted_tables)
    X_scaled, _, _ = preprocessor.prepare_features(analytical_df)

    if_detector = IsolationForestDetector(contamination=0.08, random_state=42)
    if_res = if_detector.fit_predict(X_scaled, analytical_df)

    db_detector = DBSCANDetector(eps=0.8, min_samples=4)
    combined_res = db_detector.fit_predict(X_scaled, if_res)

    comparison = ModelEvaluator.compare_models(combined_res)
    assert comparison["total_records"] == len(combined_res)
    assert "both_count" in comparison
    assert "if_only_count" in comparison
    assert "dbscan_only_count" in comparison

    # Test Anomaly Explainer
    stats = AnomalyExplainer.compute_population_stats(combined_res)
    flagged = combined_res[combined_res["IF_IS_ANOMALOUS"]].iloc[0]
    explanation, col = AnomalyExplainer.explain_record(flagged, stats)
    assert len(explanation) > 0
    assert isinstance(col, str)

