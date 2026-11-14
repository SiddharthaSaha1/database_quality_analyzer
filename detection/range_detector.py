"""
Range Validation Module
Validates values against configured domain boundaries (Age, Attendance %, Marks, Credits).
"""

from datetime import datetime
import pandas as pd

class RangeDetector:
    """Validates numeric ranges against university business rules."""

    MIN_AGE = 16
    MAX_AGE = 40
    MIN_ATTENDANCE = 0.0
    MAX_ATTENDANCE = 100.0

    @staticmethod
    def detect_range_violations(tables_dict, source="SQL_ENGINE"):
        issues = []

        # 1. Age Range in STUDENT
        students_df = tables_dict.get("STUDENT")
        if students_df is not None and not students_df.empty and "AGE" in students_df.columns:
            age_series = pd.to_numeric(students_df["AGE"], errors="coerce")
            invalid_age = students_df[age_series.notna() & ((age_series < RangeDetector.MIN_AGE) | (age_series > RangeDetector.MAX_AGE))]
            for _, row in invalid_age.iterrows():
                issues.append({
                    "RECORD_ID": str(row["STUDENT_ID"]),
                    "TABLE_NAME": "STUDENT",
                    "COLUMN_NAME": "AGE",
                    "ISSUE_TYPE": "OUT_OF_RANGE",
                    "DESCRIPTION": f"Student age {row['AGE']} is outside realistic academic limits ({RangeDetector.MIN_AGE}-{RangeDetector.MAX_AGE}).",
                    "SEVERITY": "HIGH",
                    "DETECTION_SOURCE": source,
                    "DETECTION_TIMESTAMP": datetime.now()
                })

        # 2. Attendance % Range (0 to 100)
        att_df = tables_dict.get("ATTENDANCE")
        if att_df is not None and not att_df.empty and "ATTENDANCE_PERCENTAGE" in att_df.columns:
            att_series = pd.to_numeric(att_df["ATTENDANCE_PERCENTAGE"], errors="coerce")
            invalid_att = att_df[att_series.notna() & ((att_series < RangeDetector.MIN_ATTENDANCE) | (att_series > RangeDetector.MAX_ATTENDANCE))]
            for _, row in invalid_att.iterrows():
                issues.append({
                    "RECORD_ID": str(row["ATTENDANCE_ID"]),
                    "TABLE_NAME": "ATTENDANCE",
                    "COLUMN_NAME": "ATTENDANCE_PERCENTAGE",
                    "ISSUE_TYPE": "OUT_OF_RANGE",
                    "DESCRIPTION": f"Attendance percentage {row['ATTENDANCE_PERCENTAGE']}% is outside valid bounds (0-100%).",
                    "SEVERITY": "HIGH",
                    "DETECTION_SOURCE": source,
                    "DETECTION_TIMESTAMP": datetime.now()
                })

        # 3. Exam Marks Range (0 to MAX_MARKS)
        exam_df = tables_dict.get("EXAM_RESULT")
        if exam_df is not None and not exam_df.empty and "MARKS" in exam_df.columns:
            marks = pd.to_numeric(exam_df["MARKS"], errors="coerce")
            max_marks = pd.to_numeric(exam_df["MAX_MARKS"], errors="coerce").fillna(100.0)
            invalid_marks = exam_df[marks.notna() & ((marks < 0) | (marks > max_marks))]
            for _, row in invalid_marks.iterrows():
                issues.append({
                    "RECORD_ID": str(row["RESULT_ID"]),
                    "TABLE_NAME": "EXAM_RESULT",
                    "COLUMN_NAME": "MARKS",
                    "ISSUE_TYPE": "OUT_OF_RANGE",
                    "DESCRIPTION": f"Marks scored {row['MARKS']} is negative or strictly exceeds maximum marks ({row.get('MAX_MARKS', 100)}).",
                    "SEVERITY": "HIGH",
                    "DETECTION_SOURCE": source,
                    "DETECTION_TIMESTAMP": datetime.now()
                })

        # 4. Course Credits Range (1 to 6)
        course_df = tables_dict.get("COURSE")
        if course_df is not None and not course_df.empty and "CREDITS" in course_df.columns:
            credits = pd.to_numeric(course_df["CREDITS"], errors="coerce")
            invalid_credits = course_df[credits.notna() & ((credits <= 0) | (credits > 10))]
            for _, row in invalid_credits.iterrows():
                issues.append({
                    "RECORD_ID": str(row["COURSE_ID"]),
                    "TABLE_NAME": "COURSE",
                    "COLUMN_NAME": "CREDITS",
                    "ISSUE_TYPE": "OUT_OF_RANGE",
                    "DESCRIPTION": f"Course credits ({row['CREDITS']}) outside standard curriculum limits (1-10).",
                    "SEVERITY": "MEDIUM",
                    "DETECTION_SOURCE": source,
                    "DETECTION_TIMESTAMP": datetime.now()
                })

        return issues

