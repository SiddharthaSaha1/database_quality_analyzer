"""
Unit and Integration Tests for SQL/PLSQL Rule-Based Detection
Validates Null, Duplicate, Range, Consistency, and Format detection modules.
"""

import pytest
import pandas as pd
from database.connection import CSVDatabaseAdapter
from detection.null_detector import NullDetector
from detection.duplicate_detector import DuplicateDetector
from detection.range_detector import RangeDetector
from detection.consistency_detector import ConsistencyDetector
from detection.detection_manager import DetectionManager

@pytest.fixture
def clean_tables():
    adapter = CSVDatabaseAdapter(mode="clean")
    return adapter.fetch_all_tables()

@pytest.fixture
def corrupted_tables():
    adapter = CSVDatabaseAdapter(mode="corrupted")
    return adapter.fetch_all_tables()

def test_null_detection_clean_vs_corrupted(clean_tables, corrupted_tables):
    # On clean dataset: zero null issues in mandatory student fields
    clean_issues = NullDetector.detect_in_dataframe("STUDENT", clean_tables["STUDENT"], "STUDENT_ID")
    assert len(clean_issues) == 0

    # On corrupted dataset: detects injected nulls (e.g. STUDENT_NAME, AGE, EMAIL)
    corrupt_issues = NullDetector.detect_in_dataframe("STUDENT", corrupted_tables["STUDENT"], "STUDENT_ID")
    assert len(corrupt_issues) > 0
    issue_cols = [i["COLUMN_NAME"] for i in corrupt_issues]
    assert "STUDENT_NAME" in issue_cols
    assert "AGE" in issue_cols

def test_duplicate_detection(clean_tables, corrupted_tables):
    # Clean dataset should have no duplicate emails or course enrollments
    clean_dups = DuplicateDetector.detect_duplicates(clean_tables)
    assert len(clean_dups) == 0

    # Corrupted dataset has injected duplicate emails and duplicate attendance
    corrupt_dups = DuplicateDetector.detect_duplicates(corrupted_tables)
    assert len(corrupt_dups) > 0
    tables_affected = set(d["TABLE_NAME"] for d in corrupt_dups)
    assert "STUDENT" in tables_affected
    assert "ATTENDANCE" in tables_affected

def test_range_detection(clean_tables, corrupted_tables):
    clean_range = RangeDetector.detect_range_violations(clean_tables)
    assert len(clean_range) == 0

    corrupt_range = RangeDetector.detect_range_violations(corrupted_tables)
    assert len(corrupt_range) > 0
    types = [r["ISSUE_TYPE"] for r in corrupt_range]
    assert all(t == "OUT_OF_RANGE" for t in types)

def test_consistency_and_format_detection(clean_tables, corrupted_tables):
    clean_issues = ConsistencyDetector.detect_inconsistencies(clean_tables)
    assert len(clean_issues) == 0

    corrupt_issues = ConsistencyDetector.detect_inconsistencies(corrupted_tables)
    assert len(corrupt_issues) > 0
    categories = set(c["ISSUE_TYPE"] for c in corrupt_issues)
    assert "INCONSISTENCY" in categories
    assert "FORMAT_ERROR" in categories

def test_detection_manager_full_run(corrupted_tables):
    manager = DetectionManager()
    issues_df = manager.run_all_rule_checks(corrupted_tables)
    assert not issues_df.empty
    assert "ISSUE_ID" in issues_df.columns
    assert "SEVERITY" in issues_df.columns
    assert "DESCRIPTION" in issues_df.columns

    summary = manager.summarize_issues(issues_df)
    assert summary["total"] > 0
    assert "HIGH" in summary["by_severity"]

