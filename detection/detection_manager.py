"""
SQL/PLSQL Detection Manager
Coordinates rule-based detection routines across schema tables.
Supports executing directly via Oracle PL/SQL stored procedures or via local relational rule verification.
"""

import pandas as pd
from datetime import datetime
from detection.null_detector import NullDetector
from detection.duplicate_detector import DuplicateDetector
from detection.range_detector import RangeDetector
from detection.consistency_detector import ConsistencyDetector
from utils.helpers import logger

class DetectionManager:
    """Orchestrates rule-based data quality detection across relational tables."""

    def __init__(self, db_manager=None, csv_adapter=None):
        self.db_manager = db_manager
        self.csv_adapter = csv_adapter

    def run_oracle_plsql_engine(self):
        """
        Executes PKG_DATA_QUALITY.RUN_ALL_QUALITY_CHECKS in Oracle Database.
        Retrieves generated issues from AUDIT_LOG.
        """
        if not self.db_manager:
            raise ValueError("Live OracleDatabaseManager instance is required to run Oracle PL/SQL engine.")
        
        logger.info("Executing Oracle PL/SQL data quality package PKG_DATA_QUALITY...")
        total_detected, audit_df = self.db_manager.run_all_oracle_quality_checks()
        return audit_df

    def run_all_rule_checks(self, tables_dict=None, source="SQL_ENGINE"):
        """
        Runs comprehensive rule-based checks across tables dictionary.
        tables_dict format: { 'STUDENT': df, 'COURSE': df, 'ATTENDANCE': df, 'EXAM_RESULT': df }
        """
        if tables_dict is None:
            if self.csv_adapter:
                tables_dict = self.csv_adapter.fetch_all_tables()
            elif self.db_manager:
                tables_dict = {
                    "STUDENT": self.db_manager.fetch_table("STUDENT"),
                    "COURSE": self.db_manager.fetch_table("COURSE"),
                    "ATTENDANCE": self.db_manager.fetch_table("ATTENDANCE"),
                    "EXAM_RESULT": self.db_manager.fetch_table("EXAM_RESULT"),
                }
            else:
                raise ValueError("No table data or database adapter supplied to run rule checks.")

        all_issues = []

        # 1. Null Checks
        table_pk_map = {
            "STUDENT": "STUDENT_ID",
            "COURSE": "COURSE_ID",
            "ATTENDANCE": "ATTENDANCE_ID",
            "EXAM_RESULT": "RESULT_ID"
        }
        for t_name, pk_col in table_pk_map.items():
            if t_name in tables_dict:
                null_issues = NullDetector.detect_in_dataframe(t_name, tables_dict[t_name], pk_col, source=source)
                all_issues.extend(null_issues)

        # 2. Duplicate Checks
        dup_issues = DuplicateDetector.detect_duplicates(tables_dict, source=source)
        all_issues.extend(dup_issues)

        # 3. Range Checks
        range_issues = RangeDetector.detect_range_violations(tables_dict, source=source)
        all_issues.extend(range_issues)

        # 4. Consistency & Format Checks
        cons_issues = ConsistencyDetector.detect_inconsistencies(tables_dict, source=source)
        all_issues.extend(cons_issues)

        issues_df = pd.DataFrame(all_issues)
        if not issues_df.empty:
            issues_df["ISSUE_ID"] = range(1, len(issues_df) + 1)
        else:
            issues_df = pd.DataFrame(columns=[
                "ISSUE_ID", "RECORD_ID", "TABLE_NAME", "COLUMN_NAME",
                "ISSUE_TYPE", "DESCRIPTION", "SEVERITY", "DETECTION_TIMESTAMP", "DETECTION_SOURCE"
            ])

        return issues_df

    def summarize_issues(self, issues_df):
        """Generates statistical breakdowns of rule detection results."""
        if issues_df is None or issues_df.empty:
            return {
                "total": 0,
                "by_type": {},
                "by_severity": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
                "by_table": {}
            }
        
        return {
            "total": len(issues_df),
            "by_type": issues_df["ISSUE_TYPE"].value_counts().to_dict(),
            "by_severity": issues_df["SEVERITY"].value_counts().to_dict(),
            "by_table": issues_df["TABLE_NAME"].value_counts().to_dict()
        }

