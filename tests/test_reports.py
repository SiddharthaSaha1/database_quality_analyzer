"""
Unit Tests for CSV and PDF Report Generation
"""

import pytest
import pandas as pd
from reports.csv_report import CSVReportGenerator
from reports.pdf_report import PDFReportGenerator
from integration.quality_scorer import QualityScorer
from ml.model_evaluation import ModelEvaluator

def test_csv_report_generation():
    sample_df = pd.DataFrame([
        {"ANOMALY_ID": 1, "RECORD_ID": "STU1001", "TABLE_NAME": "STUDENT", "SEVERITY": "HIGH", "EXPLANATION": "Invalid age"}
    ])
    csv_bytes = CSVReportGenerator.generate_consolidated_csv(sample_df)
    assert len(csv_bytes) > 0
    assert b"STU1001" in csv_bytes

def test_pdf_report_generation():
    sample_df = pd.DataFrame([
        {"ANOMALY_ID": 1, "RECORD_ID": "STU1001", "TABLE_NAME": "STUDENT", "SEVERITY": "HIGH",
         "DETECTION_METHOD": "SQL_RULES", "ISSUE_CATEGORY": "OUT_OF_RANGE", "EXPLANATION": "Age negative (-2)", "ORIGINAL_VALUES": "{}", "ANOMALY_SCORE": None, "DETECTION_TIMESTAMP": "2026-11-12"}
    ])
    summary = QualityScorer.calculate_score(sample_df, total_records_analyzed=100)
    comp = {"isolation_forest_total": 5, "dbscan_total": 4, "both_count": 2, "jaccard_similarity": 0.28}

    pdf_bytes = PDFReportGenerator.generate_report(summary, comp, sample_df)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")
