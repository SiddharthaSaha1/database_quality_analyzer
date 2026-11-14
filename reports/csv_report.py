"""
CSV Report Generator Module
Formats and generates downloadable CSV summaries of detected data quality issues.
"""

import io
import pandas as pd

class CSVReportGenerator:
    """Exports structured data quality findings to CSV format."""

    @staticmethod
    def generate_consolidated_csv(consolidated_df):
        """Generates CSV bytes or string for the consolidated anomalies dataset."""
        if consolidated_df is None or consolidated_df.empty:
            return "No anomalies detected or analysis not yet executed.\n".encode("utf-8")
        
        output = io.StringIO()
        consolidated_df.to_csv(output, index=False)
        return output.getvalue().encode("utf-8")

    @staticmethod
    def generate_summary_csv(quality_summary, model_comparison):
        """Exports key executive metrics into a key-value CSV."""
        data = [
            {"Metric": "Data Quality Score", "Value": quality_summary.get("score", "N/A")},
            {"Metric": "Quality Grade", "Value": quality_summary.get("grade", "N/A")},
            {"Metric": "Total Records Analyzed", "Value": quality_summary.get("total_records", 0)},
            {"Metric": "Deduplicated Issues Flagged", "Value": quality_summary.get("deduplicated_issues", 0)},
            {"Metric": "High Severity Issues", "Value": quality_summary.get("severity_counts", {}).get("HIGH", 0)},
            {"Metric": "Medium Severity Issues", "Value": quality_summary.get("severity_counts", {}).get("MEDIUM", 0)},
            {"Metric": "Low Severity Issues", "Value": quality_summary.get("severity_counts", {}).get("LOW", 0)},
            {"Metric": "Isolation Forest Outliers", "Value": model_comparison.get("isolation_forest_total", 0)},
            {"Metric": "DBSCAN Noise Records", "Value": model_comparison.get("dbscan_total", 0)},
            {"Metric": "Jointly Flagged (Both Models)", "Value": model_comparison.get("both_count", 0)}
        ]
        df = pd.DataFrame(data)
        output = io.StringIO()
        df.to_csv(output, index=False)
        return output.getvalue().encode("utf-8")

