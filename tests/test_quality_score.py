"""
Unit Tests for Data-Quality Scoring Algorithm
Validates mathematical transparency, weighted penalties, and boundary handling.
"""

import pytest
import pandas as pd
from integration.quality_scorer import QualityScorer

def test_clean_database_score():
    empty_findings = pd.DataFrame()
    res = QualityScorer.calculate_score(empty_findings, total_records_analyzed=1000)
    assert res["score"] == 100.0
    assert "Pristine" in res["grade"]
    assert res["weighted_error_count"] == 0.0

def test_empty_state_handling():
    res = QualityScorer.calculate_score(None, total_records_analyzed=0)
    assert res["score"] is None
    assert res["grade"] == "N/A"

def test_weighted_penalties():
    # 2 High severity (weight 1.0 each = 2.0)
    # 1 Medium severity (weight 0.6 = 0.6)
    # 1 Low severity (weight 0.2 = 0.2)
    # Total weighted penalty = 2.8
    # Checks per record = 5, Total records = 100 -> Total checks = 500
    # Expected score = 100 * (1 - 2.8 / 500) = 100 * (1 - 0.0056) = 99.44
    sample_df = pd.DataFrame([
        {"RECORD_ID": "1", "SEVERITY": "HIGH", "ISSUE_CATEGORY": "NULL_VALUE"},
        {"RECORD_ID": "2", "SEVERITY": "HIGH", "ISSUE_CATEGORY": "OUT_OF_RANGE"},
        {"RECORD_ID": "3", "SEVERITY": "MEDIUM", "ISSUE_CATEGORY": "STATISTICAL"},
        {"RECORD_ID": "4", "SEVERITY": "LOW", "ISSUE_CATEGORY": "FORMAT_ERROR"},
    ])

    res = QualityScorer.calculate_score(sample_df, total_records_analyzed=100, checks_per_record=5)
    assert res["weighted_error_count"] == 2.8
    assert res["score"] == 99.44
    assert res["severity_counts"]["HIGH"] == 2
    assert res["severity_counts"]["MEDIUM"] == 1
    assert res["severity_counts"]["LOW"] == 1

