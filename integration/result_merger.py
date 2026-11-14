"""
Hybrid Result Merger Module
Combines findings from Oracle SQL/PLSQL rules, Isolation Forest, and DBSCAN into
a unified, deduplicated consolidated anomalies structure conforming to CONSOLIDATED_ANOMALIES.
"""

from datetime import datetime
import pandas as pd
from integration.severity_classifier import SeverityClassifier
from ml.anomaly_explainer import AnomalyExplainer
from utils.helpers import serialize_record

class ResultMerger:
    """Consolidates rule-based and ML-based anomaly detections into a unified schema."""

    @staticmethod
    def merge_results(sql_issues_df, ml_results_df=None, raw_tables_dict=None):
        """
        Merges SQL rule violations and ML outlier predictions.
        
        sql_issues_df: DataFrame from DetectionManager
        ml_results_df: DataFrame from IsolationForest + DBSCAN
        raw_tables_dict: dict of source DataFrames to pull original record values
        """
        consolidated = []
        record_map = {} # Key: (TABLE_NAME, RECORD_ID) -> consolidated entry dict

        # -------------------------------------------------------------
        # 1. PROCESS SQL RULE FINDINGS
        # -------------------------------------------------------------
        if sql_issues_df is not None and not sql_issues_df.empty:
            for _, row in sql_issues_df.iterrows():
                tbl = str(row["TABLE_NAME"]).upper()
                rec_id = str(row["RECORD_ID"])
                key = (tbl, rec_id)

                # Fetch original values from source table if available
                orig_vals = {}
                if raw_tables_dict and tbl in raw_tables_dict:
                    src_df = raw_tables_dict[tbl]
                    id_col_map = {"STUDENT": "STUDENT_ID", "COURSE": "COURSE_ID", "ATTENDANCE": "ATTENDANCE_ID", "EXAM_RESULT": "RESULT_ID"}
                    id_col = id_col_map.get(tbl)
                    if id_col and id_col in src_df.columns:
                        matched = src_df[src_df[id_col].astype(str) == rec_id]
                        if not matched.empty:
                            orig_vals = matched.iloc[0].to_dict()

                method = str(row.get("DETECTION_SOURCE", "SQL_RULE_ENGINE"))
                issue_type = str(row.get("ISSUE_TYPE", "RULE_VIOLATION"))
                desc = str(row.get("DESCRIPTION", "Rule violation"))
                sev = str(row.get("SEVERITY", "MEDIUM"))
                col = str(row.get("COLUMN_NAME", "MULTIPLE"))

                if key in record_map:
                    # Merge existing entry
                    entry = record_map[key]
                    if method not in entry["DETECTION_METHODS"]:
                        entry["DETECTION_METHODS"].append(method)
                    if issue_type not in entry["ISSUE_CATEGORIES"]:
                        entry["ISSUE_CATEGORIES"].append(issue_type)
                    entry["EXPLANATIONS"].append(desc)
                    # Re-classify severity with multiple corroborations
                    entry["SEVERITY"] = SeverityClassifier.classify(
                        issue_type=entry["ISSUE_CATEGORIES"][0],
                        detection_methods=entry["DETECTION_METHODS"],
                        rule_severity=sev,
                        anomaly_score=entry.get("ANOMALY_SCORE")
                    )
                else:
                    record_map[key] = {
                        "RECORD_ID": rec_id,
                        "TABLE_NAME": tbl,
                        "DETECTION_METHODS": [method],
                        "ISSUE_CATEGORIES": [issue_type],
                        "EXPLANATIONS": [desc],
                        "SEVERITY": sev,
                        "RELEVANT_COLUMN": col,
                        "ORIGINAL_VALUES": serialize_record(orig_vals),
                        "ANOMALY_SCORE": None,
                        "DETECTION_TIMESTAMP": row.get("DETECTION_TIMESTAMP", datetime.now())
                    }

        # -------------------------------------------------------------
        # 2. PROCESS MACHINE LEARNING OUTLIERS
        # -------------------------------------------------------------
        if ml_results_df is not None and not ml_results_df.empty:
            feature_stats = AnomalyExplainer.compute_population_stats(ml_results_df)

            # Filter records flagged by either Isolation Forest or DBSCAN
            is_if = ml_results_df.get("IF_IS_ANOMALOUS", pd.Series(False, index=ml_results_df.index)).astype(bool)
            is_db = ml_results_df.get("DBSCAN_IS_ANOMALOUS", pd.Series(False, index=ml_results_df.index)).astype(bool)
            flagged_ml = ml_results_df[is_if | is_db]

            for _, row in flagged_ml.iterrows():
                methods = []
                if row.get("IF_IS_ANOMALOUS"):
                    methods.append("ISOLATION_FOREST")
                if row.get("DBSCAN_IS_ANOMALOUS"):
                    methods.append("DBSCAN")

                if_score = float(row.get("IF_ANOMALY_SCORE", 0.0)) if "IF_ANOMALY_SCORE" in row else None

                # Derive mathematical explanation from feature deviations
                explanation, primary_col = AnomalyExplainer.explain_record(row, feature_stats)

                # Link to both student and attendance/result tables
                stu_id = str(row.get("STUDENT_ID", ""))
                att_id = str(row.get("ATTENDANCE_ID", ""))
                res_id = str(row.get("RESULT_ID", ""))

                # Build original values summary
                orig_dict = {
                    "STUDENT_ID": stu_id,
                    "COURSE_ID": str(row.get("COURSE_ID", "")),
                    "AGE": row.get("AGE"),
                    "ATTENDANCE_PERCENTAGE": row.get("ATTENDANCE_PERCENTAGE"),
                    "MARKS_PERCENTAGE": row.get("MARKS_PERCENTAGE"),
                    "ATTENDANCE_CONSISTENCY": row.get("ATTENDANCE_CONSISTENCY"),
                    "ATTENDANCE_VS_MARKS_GAP": row.get("ATTENDANCE_VS_MARKS_GAP")
                }

                # Associate primarily with student or composite performance entity
                target_keys = [("STUDENT", stu_id)]
                if att_id:
                    target_keys.append(("ATTENDANCE", att_id))
                if res_id:
                    target_keys.append(("EXAM_RESULT", res_id))

                for tbl, r_id in target_keys:
                    key = (tbl, r_id)
                    if key in record_map:
                        entry = record_map[key]
                        for m in methods:
                            if m not in entry["DETECTION_METHODS"]:
                                entry["DETECTION_METHODS"].append(m)
                        if "STATISTICAL_ANOMALY" not in entry["ISSUE_CATEGORIES"]:
                            entry["ISSUE_CATEGORIES"].append("STATISTICAL_ANOMALY")
                        entry["EXPLANATIONS"].append(f"[ML] {explanation}")
                        entry["ANOMALY_SCORE"] = if_score
                        # Escalation: Flagged by both SQL rules and ML
                        entry["SEVERITY"] = SeverityClassifier.classify(
                            issue_type="STATISTICAL_ANOMALY",
                            detection_methods=entry["DETECTION_METHODS"],
                            rule_severity=entry["SEVERITY"],
                            anomaly_score=if_score
                        )
                    else:
                        # New ML-only flag
                        init_sev = SeverityClassifier.classify(
                            issue_type="STATISTICAL_ANOMALY",
                            detection_methods=methods,
                            anomaly_score=if_score
                        )
                        record_map[key] = {
                            "RECORD_ID": r_id,
                            "TABLE_NAME": tbl,
                            "DETECTION_METHODS": methods,
                            "ISSUE_CATEGORIES": ["STATISTICAL_ANOMALY"],
                            "EXPLANATIONS": [f"[ML] {explanation}"],
                            "SEVERITY": init_sev,
                            "RELEVANT_COLUMN": primary_col,
                            "ORIGINAL_VALUES": serialize_record(orig_dict),
                            "ANOMALY_SCORE": if_score,
                            "DETECTION_TIMESTAMP": datetime.now()
                        }

        # -------------------------------------------------------------
        # 3. FORMAT FINAL CONSOLIDATED DATAFRAME
        # -------------------------------------------------------------
        final_rows = []
        for (tbl, rec_id), data in record_map.items():
            final_rows.append({
                "RECORD_ID": data["RECORD_ID"],
                "TABLE_NAME": data["TABLE_NAME"],
                "DETECTION_METHOD": " + ".join(data["DETECTION_METHODS"]),
                "ISSUE_CATEGORY": " / ".join(data["ISSUE_CATEGORIES"]),
                "EXPLANATION": " | ".join(data["EXPLANATIONS"]),
                "SEVERITY": data["SEVERITY"],
                "RELEVANT_COLUMN": data["RELEVANT_COLUMN"],
                "ORIGINAL_VALUES": data["ORIGINAL_VALUES"],
                "ANOMALY_SCORE": data["ANOMALY_SCORE"],
                "DETECTION_TIMESTAMP": data["DETECTION_TIMESTAMP"]
            })

        consolidated_df = pd.DataFrame(final_rows)
        if not consolidated_df.empty:
            consolidated_df.insert(0, "ANOMALY_ID", range(1, len(consolidated_df) + 1))
        else:
            consolidated_df = pd.DataFrame(columns=[
                "ANOMALY_ID", "RECORD_ID", "TABLE_NAME", "DETECTION_METHOD",
                "ISSUE_CATEGORY", "EXPLANATION", "SEVERITY", "RELEVANT_COLUMN",
                "ORIGINAL_VALUES", "ANOMALY_SCORE", "DETECTION_TIMESTAMP"
            ])

        return consolidated_df

