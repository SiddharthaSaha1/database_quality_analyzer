"""
Consistency and Format Validation Module
Detects mathematical contradictions, cross-field logical conflicts, and format defects.
"""

import re
from datetime import datetime
import pandas as pd

class ConsistencyDetector:
    """Validates multi-column consistency and regex pattern syntax."""

    EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
    # Phone number allowing international codes, dashes, spaces, brackets, 10-15 digits
    PHONE_REGEX = re.compile(r"^\+?[0-9]{1,4}?[-. ]?(\([0-9]{2,4}\)|[0-9]{2,4})[-. ]?[0-9]{3,4}[-. ]?[0-9]{3,4}$")

    @staticmethod
    def detect_inconsistencies(tables_dict, source="SQL_ENGINE"):
        issues = []

        # -------------------------------------------------------------
        # 1. ATTENDANCE MATHEMATICAL & LOGICAL CONSISTENCY
        # -------------------------------------------------------------
        att_df = tables_dict.get("ATTENDANCE")
        if att_df is not None and not att_df.empty:
            tot = pd.to_numeric(att_df.get("TOTAL_CLASSES"), errors="coerce")
            att = pd.to_numeric(att_df.get("ATTENDED_CLASSES"), errors="coerce")
            pct = pd.to_numeric(att_df.get("ATTENDANCE_PERCENTAGE"), errors="coerce")

            # Condition A: Attended > Total
            att_gt_tot = att_df[tot.notna() & att.notna() & (att > tot)]
            for _, row in att_gt_tot.iterrows():
                issues.append({
                    "RECORD_ID": str(row["ATTENDANCE_ID"]),
                    "TABLE_NAME": "ATTENDANCE",
                    "COLUMN_NAME": "ATTENDED_CLASSES",
                    "ISSUE_TYPE": "INCONSISTENCY",
                    "DESCRIPTION": f"Attended classes ({row['ATTENDED_CLASSES']}) strictly exceeds total classes held ({row['TOTAL_CLASSES']}).",
                    "SEVERITY": "HIGH",
                    "DETECTION_SOURCE": source,
                    "DETECTION_TIMESTAMP": datetime.now()
                })

            # Condition B: Total <= 0 yet Attended > 0
            zero_tot = att_df[tot.notna() & att.notna() & (tot <= 0) & (att > 0)]
            for _, row in zero_tot.iterrows():
                issues.append({
                    "RECORD_ID": str(row["ATTENDANCE_ID"]),
                    "TABLE_NAME": "ATTENDANCE",
                    "COLUMN_NAME": "TOTAL_CLASSES",
                    "ISSUE_TYPE": "INCONSISTENCY",
                    "DESCRIPTION": f"Total classes is non-positive ({row['TOTAL_CLASSES']}) but student has attended {row['ATTENDED_CLASSES']}.",
                    "SEVERITY": "HIGH",
                    "DETECTION_SOURCE": source,
                    "DETECTION_TIMESTAMP": datetime.now()
                })

            # Condition C: Attendance Percentage mismatch from attended/total by > 2.0%
            valid_math = (tot > 0) & (att >= 0) & (att <= tot) & pct.notna()
            calc_pct = (att / tot) * 100.0
            discrepancy = (pct - calc_pct).abs()
            mismatch_df = att_df[valid_math & (discrepancy > 2.0)]
            for _, row in mismatch_df.iterrows():
                r_tot = float(row["TOTAL_CLASSES"])
                r_att = float(row["ATTENDED_CLASSES"])
                expected_pct = round((r_att / r_tot) * 100.0, 2)
                issues.append({
                    "RECORD_ID": str(row["ATTENDANCE_ID"]),
                    "TABLE_NAME": "ATTENDANCE",
                    "COLUMN_NAME": "ATTENDANCE_PERCENTAGE",
                    "ISSUE_TYPE": "INCONSISTENCY",
                    "DESCRIPTION": f"Recorded attendance {row['ATTENDANCE_PERCENTAGE']}% conflicts with calculated value {expected_pct}% ({r_att}/{r_tot}).",
                    "SEVERITY": "MEDIUM",
                    "DETECTION_SOURCE": source,
                    "DETECTION_TIMESTAMP": datetime.now()
                })

        # -------------------------------------------------------------
        # 2. STUDENT FORMAT & LOGICAL CHECKS
        # -------------------------------------------------------------
        stu_df = tables_dict.get("STUDENT")
        if stu_df is not None and not stu_df.empty:
            # Email Syntax
            if "EMAIL" in stu_df.columns:
                for _, row in stu_df[stu_df["EMAIL"].notna()].iterrows():
                    em = str(row["EMAIL"]).strip()
                    if em and not ConsistencyDetector.EMAIL_REGEX.match(em):
                        issues.append({
                            "RECORD_ID": str(row["STUDENT_ID"]),
                            "TABLE_NAME": "STUDENT",
                            "COLUMN_NAME": "EMAIL",
                            "ISSUE_TYPE": "FORMAT_ERROR",
                            "DESCRIPTION": f"Malformed email address structure: '{em}'.",
                            "SEVERITY": "LOW",
                            "DETECTION_SOURCE": source,
                            "DETECTION_TIMESTAMP": datetime.now()
                        })

            # Phone Syntax
            if "PHONE_NUMBER" in stu_df.columns:
                for _, row in stu_df[stu_df["PHONE_NUMBER"].notna()].iterrows():
                    ph = str(row["PHONE_NUMBER"]).strip()
                    if ph and (len(ph) < 8 or not ConsistencyDetector.PHONE_REGEX.match(ph)):
                        issues.append({
                            "RECORD_ID": str(row["STUDENT_ID"]),
                            "TABLE_NAME": "STUDENT",
                            "COLUMN_NAME": "PHONE_NUMBER",
                            "ISSUE_TYPE": "FORMAT_ERROR",
                            "DESCRIPTION": f"Invalid phone number syntax: '{ph}'.",
                            "SEVERITY": "LOW",
                            "DETECTION_SOURCE": source,
                            "DETECTION_TIMESTAMP": datetime.now()
                        })

            # Cross-field: Age vs Year of Study
            if "AGE" in stu_df.columns and "YEAR_OF_STUDY" in stu_df.columns:
                age = pd.to_numeric(stu_df["AGE"], errors="coerce")
                yr = pd.to_numeric(stu_df["YEAR_OF_STUDY"], errors="coerce")
                conflicts = stu_df[((yr >= 3) & (age <= 17)) | ((yr == 1) & (age >= 38))]
                for _, row in conflicts.iterrows():
                    issues.append({
                        "RECORD_ID": str(row["STUDENT_ID"]),
                        "TABLE_NAME": "STUDENT",
                        "COLUMN_NAME": "AGE, YEAR_OF_STUDY",
                        "ISSUE_TYPE": "INCONSISTENCY",
                        "DESCRIPTION": f"Logical conflict: Student in Year {row['YEAR_OF_STUDY']} reported with abnormal age {row['AGE']}.",
                        "SEVERITY": "MEDIUM",
                        "DETECTION_SOURCE": source,
                        "DETECTION_TIMESTAMP": datetime.now()
                    })

        return issues

