"""
Data Quality Scoring Engine
Calculates a transparent, deterministic data-quality score:
    Score = 100 * (1 - Weighted Deduplicated Error Count / Total Applicable Checks)
Applies configurable severity weights and prevents double-counting across detection engines.
"""

from utils.config import SEVERITY_WEIGHTS

class QualityScorer:
    """Computes comprehensive, auditable database quality indices."""

    @staticmethod
    def calculate_score(consolidated_df, total_records_analyzed, checks_per_record=6, weights=None):
        """
        Calculates normalized quality score (0.0 - 100.0).
        
        consolidated_df: Deduplicated merged findings DataFrame.
        total_records_analyzed: Total rows evaluated across all tables.
        checks_per_record: Number of relational and statistical conditions tested per record.
        """
        if total_records_analyzed <= 0:
            return {
                "score": None,
                "grade": "N/A",
                "status": "No analysis performed.",
                "total_records": 0,
                "total_applicable_checks": 0,
                "weighted_error_count": 0.0,
                "deduplicated_issues": 0,
                "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
                "dimension_scores": {}
            }

        w = weights or SEVERITY_WEIGHTS
        total_checks = max(1, total_records_analyzed * checks_per_record)

        if consolidated_df is None or consolidated_df.empty:
            return {
                "score": 100.0,
                "grade": "A+ (Pristine)",
                "status": "Pristine database quality. Zero issues detected.",
                "total_records": total_records_analyzed,
                "total_applicable_checks": total_checks,
                "weighted_error_count": 0.0,
                "deduplicated_issues": 0,
                "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
                "dimension_scores": {
                    "Completeness": 100.0,
                    "Validity": 100.0,
                    "Consistency": 100.0,
                    "Uniqueness": 100.0
                }
            }

        # Deduplicated issue counts by severity
        sev_counts = consolidated_df["SEVERITY"].value_counts().to_dict()
        high_cnt = int(sev_counts.get("HIGH", 0))
        med_cnt = int(sev_counts.get("MEDIUM", 0))
        low_cnt = int(sev_counts.get("LOW", 0))

        # Weighted penalty
        weighted_errors = (
            (high_cnt * w.get("HIGH", 1.0)) +
            (med_cnt * w.get("MEDIUM", 0.6)) +
            (low_cnt * w.get("LOW", 0.2))
        )

        # Quality Score Calculation
        raw_ratio = weighted_errors / total_checks
        score = max(0.0, min(100.0, 100.0 * (1.0 - raw_ratio)))
        score = round(score, 2)

        # Academic Grade mapping
        if score >= 90.0:
            grade = "A (Excellent)"
        elif score >= 80.0:
            grade = "B (Good)"
        elif score >= 70.0:
            grade = "C (Fair)"
        elif score >= 50.0:
            grade = "D (Needs Remediation)"
        else:
            grade = "F (Critical Degradation)"

        # Dimension Breakdown
        if "ISSUE_CATEGORY" in consolidated_df.columns:
            cats = consolidated_df["ISSUE_CATEGORY"].astype(str).str.upper()
        else:
            cats = pd.Series("", index=consolidated_df.index)
        null_issues = cats.str.contains("NULL").sum()
        dup_issues = cats.str.contains("DUPLICATE").sum()
        range_issues = cats.str.contains("RANGE").sum()
        consist_issues = (cats.str.contains("INCONSISTENCY") | cats.str.contains("STATISTICAL")).sum()

        dim_scores = {
            "Completeness": round(max(0.0, 100.0 - (null_issues / total_records_analyzed * 100.0)), 1),
            "Uniqueness": round(max(0.0, 100.0 - (dup_issues / total_records_analyzed * 100.0)), 1),
            "Validity": round(max(0.0, 100.0 - (range_issues / total_records_analyzed * 100.0)), 1),
            "Consistency": round(max(0.0, 100.0 - (consist_issues / total_records_analyzed * 100.0)), 1),
        }

        return {
            "score": score,
            "grade": grade,
            "status": "Analysis completed.",
            "total_records": total_records_analyzed,
            "total_applicable_checks": total_checks,
            "weighted_error_count": round(weighted_errors, 2),
            "deduplicated_issues": len(consolidated_df),
            "severity_counts": {"HIGH": high_cnt, "MEDIUM": med_cnt, "LOW": low_cnt},
            "dimension_scores": dim_scores
        }
