"""
Severity Classification Module
Implements domain-aware severity taxonomy:
- HIGH: Clearly invalid values, major logical contradictions, or multi-method corroborated flags.
- MEDIUM: Statistical multivariate anomalies, suspicious value combinations.
- LOW: Minor formatting syntax defects, low-impact omissions.
"""

class SeverityClassifier:
    """Evaluates and escalates severity based on evidence and multi-engine agreement."""

    @staticmethod
    def classify(issue_type, detection_methods, rule_severity=None, anomaly_score=None):
        """
        Determines the final severity level: 'HIGH', 'MEDIUM', or 'LOW'.
        """
        # Rule 1: Multi-engine corroboration (flagged by both SQL rules and ML, or both IF and DBSCAN with high score)
        methods = set(detection_methods) if isinstance(detection_methods, (list, set)) else {str(detection_methods)}
        
        has_sql = any("SQL" in m or "PLSQL" in m or "RULE" in m for m in methods)
        has_ml = any("ISOLATION_FOREST" in m or "DBSCAN" in m for m in methods)
        has_both_ml = ("ISOLATION_FOREST" in methods) and ("DBSCAN" in methods)

        if has_sql and has_ml:
            return "HIGH"  # Multiple independent detection methods flagging the same record

        if has_both_ml and (anomaly_score is not None and anomaly_score >= 0.75):
            return "HIGH"

        # Rule 2: SQL Rule baseline severity
        if rule_severity in ["HIGH", "MEDIUM", "LOW"]:
            # Check for critical issue types
            if issue_type in ["OUT_OF_RANGE", "INCONSISTENCY", "DUPLICATE"]:
                return rule_severity
            elif issue_type == "FORMAT_ERROR":
                return "LOW"
            return rule_severity

        # Rule 3: Pure ML anomaly classification
        if has_ml:
            if anomaly_score is not None and anomaly_score >= 0.85:
                return "HIGH"
            elif anomaly_score is not None and anomaly_score >= 0.40:
                return "MEDIUM"
            return "MEDIUM"

        return "LOW"

