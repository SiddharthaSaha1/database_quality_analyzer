"""
Duplicate Record Detection Module
Detects duplicate primary keys, shared email addresses, and repeated course enrollments.
"""

from datetime import datetime
import pandas as pd

class DuplicateDetector:
    """Detects unique constraint violations and repeated attributes across database records."""

    @staticmethod
    def detect_duplicates(tables_dict, source="SQL_ENGINE"):
        """
        tables_dict: dict of { 'STUDENT': df, 'ATTENDANCE': df, 'EXAM_RESULT': df, ... }
        """
        issues = []
        
        # 1. Duplicate Emails in STUDENT
        students_df = tables_dict.get("STUDENT")
        if students_df is not None and not students_df.empty and "EMAIL" in students_df.columns:
            valid_emails = students_df[students_df["EMAIL"].notna() & (students_df["EMAIL"].str.strip() != "")]
            dup_emails = valid_emails[valid_emails.duplicated(subset=["EMAIL"], keep=False)]
            for _, row in dup_emails.iterrows():
                issues.append({
                    "RECORD_ID": str(row["STUDENT_ID"]),
                    "TABLE_NAME": "STUDENT",
                    "COLUMN_NAME": "EMAIL",
                    "ISSUE_TYPE": "DUPLICATE",
                    "DESCRIPTION": f"Duplicate email address detected: '{row['EMAIL']}'",
                    "SEVERITY": "HIGH",
                    "DETECTION_SOURCE": source,
                    "DETECTION_TIMESTAMP": datetime.now()
                })

        # 2. Duplicate Attendance records for same (STUDENT_ID, COURSE_ID)
        att_df = tables_dict.get("ATTENDANCE")
        if att_df is not None and not att_df.empty:
            if "STUDENT_ID" in att_df.columns and "COURSE_ID" in att_df.columns:
                dup_att = att_df[att_df.duplicated(subset=["STUDENT_ID", "COURSE_ID"], keep=False)]
                for _, row in dup_att.iterrows():
                    issues.append({
                        "RECORD_ID": str(row["ATTENDANCE_ID"]),
                        "TABLE_NAME": "ATTENDANCE",
                        "COLUMN_NAME": "STUDENT_ID, COURSE_ID",
                        "ISSUE_TYPE": "DUPLICATE",
                        "DESCRIPTION": f"Duplicate course enrollment attendance for Student '{row['STUDENT_ID']}' in Course '{row['COURSE_ID']}'",
                        "SEVERITY": "MEDIUM",
                        "DETECTION_SOURCE": source,
                        "DETECTION_TIMESTAMP": datetime.now()
                    })

        # 3. Duplicate Exam Submissions for same (STUDENT_ID, COURSE_ID)
        exam_df = tables_dict.get("EXAM_RESULT")
        if exam_df is not None and not exam_df.empty:
            if "STUDENT_ID" in exam_df.columns and "COURSE_ID" in exam_df.columns:
                dup_exam = exam_df[exam_df.duplicated(subset=["STUDENT_ID", "COURSE_ID"], keep=False)]
                for _, row in dup_exam.iterrows():
                    issues.append({
                        "RECORD_ID": str(row["RESULT_ID"]),
                        "TABLE_NAME": "EXAM_RESULT",
                        "COLUMN_NAME": "STUDENT_ID, COURSE_ID",
                        "ISSUE_TYPE": "DUPLICATE",
                        "DESCRIPTION": f"Duplicate exam result entry for Student '{row['STUDENT_ID']}' in Course '{row['COURSE_ID']}'",
                        "SEVERITY": "HIGH",
                        "DETECTION_SOURCE": source,
                        "DETECTION_TIMESTAMP": datetime.now()
                    })

        return issues

