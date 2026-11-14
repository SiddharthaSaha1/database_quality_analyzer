"""
Null and Missing Value Detection Module
Executes relational checks for missing mandatory columns across all schema tables.
"""

import pandas as pd
from datetime import datetime

class NullDetector:
    """Detects missing/null fields in student, course, attendance, and exam tables."""

    MANDATORY_FIELDS = {
        "STUDENT": [
            ("STUDENT_ID", "HIGH"),
            ("STUDENT_NAME", "HIGH"),
            ("AGE", "MEDIUM"),
            ("DEPARTMENT", "HIGH"),
            ("YEAR_OF_STUDY", "HIGH"),
            ("EMAIL", "MEDIUM"),
            ("PHONE_NUMBER", "LOW")
        ],
        "COURSE": [
            ("COURSE_ID", "HIGH"),
            ("COURSE_NAME", "HIGH"),
            ("CREDITS", "HIGH")
        ],
        "ATTENDANCE": [
            ("ATTENDANCE_ID", "HIGH"),
            ("STUDENT_ID", "HIGH"),
            ("COURSE_ID", "HIGH"),
            ("ATTENDANCE_PERCENTAGE", "HIGH"),
            ("TOTAL_CLASSES", "HIGH"),
            ("ATTENDED_CLASSES", "HIGH")
        ],
        "EXAM_RESULT": [
            ("RESULT_ID", "HIGH"),
            ("STUDENT_ID", "HIGH"),
            ("COURSE_ID", "HIGH"),
            ("MARKS", "HIGH"),
            ("MAX_MARKS", "HIGH")
        ]
    }

    @staticmethod
    def detect_in_dataframe(table_name, df, id_col, source="SQL_ENGINE"):
        """Scans a table DataFrame for missing values and returns list of issue dicts."""
        issues = []
        if df is None or df.empty:
            return issues

        checks = NullDetector.MANDATORY_FIELDS.get(table_name.upper(), [])
        for col, severity in checks:
            if col not in df.columns:
                continue
            
            # Detect null or whitespace-only strings
            null_mask = df[col].isna()
            if df[col].dtype == object:
                null_mask = null_mask | (df[col].astype(str).str.strip().isin(["", "None", "nan", "NULL"]))
            
            flagged = df[null_mask]
            for _, row in flagged.iterrows():
                rec_id = str(row.get(id_col, "UNKNOWN"))
                issues.append({
                    "RECORD_ID": rec_id,
                    "TABLE_NAME": table_name.upper(),
                    "COLUMN_NAME": col,
                    "ISSUE_TYPE": "NULL_VALUE",
                    "DESCRIPTION": f"Mandatory column '{col}' is missing or null.",
                    "SEVERITY": severity,
                    "DETECTION_SOURCE": source,
                    "DETECTION_TIMESTAMP": datetime.now()
                })
        return issues

