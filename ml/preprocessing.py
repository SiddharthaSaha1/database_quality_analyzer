"""
Machine Learning Preprocessing Pipeline
Joins relational tables into an analytical feature matrix.
Performs feature engineering, explicit missingness handling, and scaling.
Identifies identifiers and strictly excludes them from model training.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

class MLPreprocessor:
    """Extracts, merges, and transforms database records into feature vectors."""

    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_names = []
        self.fitted = False

    def build_analytical_dataset(self, tables_dict):
        """
        Merges STUDENT, ATTENDANCE, and EXAM_RESULT into a unified observation record.
        Primary unit of analysis: Student course performance instance.
        """
        stu = tables_dict.get("STUDENT")
        att = tables_dict.get("ATTENDANCE")
        exam = tables_dict.get("EXAM_RESULT")

        if stu is None or att is None or exam is None:
            raise ValueError("All three tables (STUDENT, ATTENDANCE, EXAM_RESULT) must be present.")

        # Ensure string IDs for joining
        s = stu.copy()
        a = att.copy()
        e = exam.copy()
        for df in [s, a, e]:
            for col in ["STUDENT_ID", "COURSE_ID"]:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()

        # Join Attendance and Exam by STUDENT_ID and COURSE_ID
        merged = pd.merge(a, e, on=["STUDENT_ID", "COURSE_ID"], how="inner", suffixes=("_ATT", "_EXAM"))
        # Join with Student metadata
        full_df = pd.merge(merged, s, on="STUDENT_ID", how="inner")

        # Feature Engineering:
        # 1. MARKS_PERCENTAGE
        max_marks = pd.to_numeric(full_df.get("MAX_MARKS", 100), errors="coerce").fillna(100.0)
        marks = pd.to_numeric(full_df.get("MARKS"), errors="coerce")
        full_df["MARKS_PERCENTAGE"] = (marks / max_marks) * 100.0

        # 2. NUMERIC CONVERSIONS
        full_df["AGE"] = pd.to_numeric(full_df.get("AGE"), errors="coerce")
        full_df["YEAR_OF_STUDY"] = pd.to_numeric(full_df.get("YEAR_OF_STUDY"), errors="coerce")
        full_df["ATTENDANCE_PERCENTAGE"] = pd.to_numeric(full_df.get("ATTENDANCE_PERCENTAGE"), errors="coerce")
        full_df["TOTAL_CLASSES"] = pd.to_numeric(full_df.get("TOTAL_CLASSES"), errors="coerce")
        full_df["ATTENDED_CLASSES"] = pd.to_numeric(full_df.get("ATTENDED_CLASSES"), errors="coerce")

        # 3. ATTENDANCE_CONSISTENCY (Discrepancy between stored % and calculated ratio)
        safe_tot = full_df["TOTAL_CLASSES"].replace(0, np.nan)
        calc_pct = (full_df["ATTENDED_CLASSES"] / safe_tot) * 100.0
        full_df["ATTENDANCE_CONSISTENCY"] = (full_df["ATTENDANCE_PERCENTAGE"] - calc_pct).abs()

        # 4. ATTENDANCE_VS_MARKS_GAP (Captures anomalies like 98% attendance but 5% marks, or vice-versa)
        full_df["ATTENDANCE_VS_MARKS_GAP"] = full_df["ATTENDANCE_PERCENTAGE"] - full_df["MARKS_PERCENTAGE"]

        # Composite Record ID for tracking
        full_df["COMPOSITE_RECORD_ID"] = (
            full_df["STUDENT_ID"] + ":" + full_df["COURSE_ID"] + ":" + 
            full_df.get("ATTENDANCE_ID", "").astype(str) + ":" + full_df.get("RESULT_ID", "").astype(str)
        )

        return full_df

    def prepare_features(self, analytical_df, fit=True):
        """
        Prepares scaled numerical feature vectors without arbitrary identifiers.
        Handles missing values explicitly with median imputation + missing indicators.
        """
        feature_cols = [
            "AGE",
            "YEAR_OF_STUDY",
            "ATTENDANCE_PERCENTAGE",
            "MARKS_PERCENTAGE",
            "ATTENDANCE_CONSISTENCY",
            "ATTENDANCE_VS_MARKS_GAP"
        ]

        # Extract features copy
        X_df = analytical_df[feature_cols].copy()

        # Explicit Missingness Handling: track missingness without silently zeroing
        for col in feature_cols:
            if X_df[col].isna().any():
                X_df[f"{col}_IS_MISSING"] = X_df[col].isna().astype(float)
                # Impute median so model can evaluate remaining valid features
                median_val = X_df[col].median() if not pd.isna(X_df[col].median()) else 0.0
                X_df[col] = X_df[col].fillna(median_val)

        # Convert to numpy array
        self.feature_names = list(X_df.columns)
        X_raw = X_df.values

        if fit or not self.fitted:
            X_scaled = self.scaler.fit_transform(X_raw)
            self.fitted = True
        else:
            X_scaled = self.scaler.transform(X_raw)

        return X_scaled, X_df, analytical_df

