"""
Unit and Integration Tests for Hybrid Result Merger & Severity Classification
"""

import pytest
import pandas as pd
from integration.severity_classifier import SeverityClassifier
from integration.result_merger import ResultMerger
from detection.detection_manager import DetectionManager
from ml.preprocessing import MLPreprocessor
from ml.isolation_forest import IsolationForestDetector
from ml.dbscan import DBSCANDetector
from database.connection import CSVDatabaseAdapter

@pytest.fixture
def corrupted_tables():
    adapter = CSVDatabaseAdapter(mode="corrupted")
    return adapter.fetch_all_tables()

def test_severity_classification_rules():
    # Multi-engine corroboration must escalate to HIGH
    sev = SeverityClassifier.classify(
        issue_type="STATISTICAL_ANOMALY",
        detection_methods=["SQL_RULE_ENGINE", "ISOLATION_FOREST"]
    )
    assert sev == "HIGH"

    # Both ML engines with high anomaly score escalates to HIGH
    sev_ml = SeverityClassifier.classify(
        issue_type="STATISTICAL_ANOMALY",
        detection_methods=["ISOLATION_FOREST", "DBSCAN"],
        anomaly_score=0.85
    )
    assert sev_ml == "HIGH"

    # Format errors should remain LOW
    sev_fmt = SeverityClassifier.classify(
        issue_type="FORMAT_ERROR",
        detection_methods=["SQL_RULE_ENGINE"],
        rule_severity="LOW"
    )
    assert sev_fmt == "LOW"

def test_result_merger_consolidation(corrupted_tables):
    # Run SQL Detection
    mgr = DetectionManager()
    sql_issues = mgr.run_all_rule_checks(corrupted_tables)

    # Run ML Detection
    pre = MLPreprocessor()
    analytical = pre.build_analytical_dataset(corrupted_tables)
    X_scaled, _, _ = pre.prepare_features(analytical)
    if_detector = IsolationForestDetector(contamination=0.08, random_state=42)
    if_res = if_detector.fit_predict(X_scaled, analytical)
    db_detector = DBSCANDetector(eps=0.8, min_samples=4)
    ml_res = db_detector.fit_predict(X_scaled, if_res)

    # Merge results
    consolidated = ResultMerger.merge_results(sql_issues, ml_res, raw_tables_dict=corrupted_tables)

    assert not consolidated.empty
    assert "RECORD_ID" in consolidated.columns
    assert "DETECTION_METHOD" in consolidated.columns
    assert "SEVERITY" in consolidated.columns
    assert "ORIGINAL_VALUES" in consolidated.columns

    # Verify no duplicate entries for the exact same (TABLE_NAME, RECORD_ID)
    keys = list(zip(consolidated["TABLE_NAME"], consolidated["RECORD_ID"]))
    assert len(keys) == len(set(keys)), "Consolidated anomalies must deduplicate identical records."

