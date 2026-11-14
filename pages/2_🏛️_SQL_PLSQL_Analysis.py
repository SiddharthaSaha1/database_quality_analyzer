"""
Page 2: SQL/PLSQL Rule-Based Analysis
Explores relational database validation rules, PL/SQL package procedures,
and audit findings by individual check.
"""

import streamlit as st
import pandas as pd
from detection.detection_manager import DetectionManager
from detection.null_detector import NullDetector
from detection.duplicate_detector import DuplicateDetector
from detection.range_detector import RangeDetector
from detection.consistency_detector import ConsistencyDetector

st.title("🏛️ Oracle SQL & PL/SQL Quality Analysis")
st.markdown("""
Deterministic rule-based database inspection. In an active Oracle deployment, these procedures execute inside
the database engine using the `PKG_DATA_QUALITY` package and record audit findings directly to `AUDIT_LOG`.
""")

tables = st.session_state.get("tables_dict", {})
if not tables:
    st.warning("No table data loaded. Please check Dataset Management.")
    st.stop()

# Execution Buttons
btn_col1, btn_col2 = st.columns([1, 3])
with btn_col1:
    if st.button("⚡ Execute All SQL Checks", type="primary", use_container_width=True):
        with st.spinner("Executing SQL/PLSQL checks..."):
            mgr = DetectionManager(
                db_manager=st.session_state.oracle_manager if st.session_state.db_mode == "Oracle" else None,
                csv_adapter=st.session_state.csv_adapter if st.session_state.db_mode == "CSV_Demo" else None
            )
            issues_df = mgr.run_all_rule_checks(tables, source="SQL_ENGINE")
            st.session_state.sql_issues_df = issues_df
            st.success(f"Executed all checks! Detected {len(issues_df)} relational defects.")

sql_issues = st.session_state.get("sql_issues_df", pd.DataFrame())

# Rule Categories Status Card
st.subheader("Configured SQL/PLSQL Rule Procedures")

rules_catalog = [
    {
        "Procedure": "PKG_DATA_QUALITY.CHECK_NULL_VALUES",
        "Target Tables": "STUDENT, COURSE, ATTENDANCE, EXAM_RESULT",
        "Rule Description": "Flags NULL or blank values in mandatory attributes (Student Name, Age, Dept, Email, Marks, Attendance %).",
        "Type": "NULL_VALUE"
    },
    {
        "Procedure": "PKG_DATA_QUALITY.CHECK_DUPLICATES",
        "Target Tables": "STUDENT, ATTENDANCE, EXAM_RESULT",
        "Rule Description": "Detects repeated emails, multiple course enrollments per student, and duplicate exam submissions.",
        "Type": "DUPLICATE"
    },
    {
        "Procedure": "PKG_DATA_QUALITY.CHECK_INVALID_RANGES",
        "Target Tables": "STUDENT, ATTENDANCE, EXAM_RESULT, COURSE",
        "Rule Description": "Asserts Age (16-40), Attendance % (0-100), Marks (0 to MAX_MARKS), and Credits (1-10).",
        "Type": "OUT_OF_RANGE"
    },
    {
        "Procedure": "PKG_DATA_QUALITY.CHECK_INCONSISTENT_RECORDS",
        "Target Tables": "ATTENDANCE, STUDENT",
        "Rule Description": "Ensures ATTENDED_CLASSES <= TOTAL_CLASSES, validates calculated ratio vs stored %, checks Age vs Year.",
        "Type": "INCONSISTENCY"
    },
    {
        "Procedure": "PKG_DATA_QUALITY.CHECK_FORMAT_VALIDATION",
        "Target Tables": "STUDENT",
        "Rule Description": "Executes REGEXP_LIKE pattern validation for Email RFC syntax and phone number lengths.",
        "Type": "FORMAT_ERROR"
    }
]

cat_cols = st.columns(len(rules_catalog))
for i, rule in enumerate(rules_catalog):
    with cat_cols[i]:
        cnt = 0
        if not sql_issues.empty and "ISSUE_TYPE" in sql_issues.columns:
            cnt = (sql_issues["ISSUE_TYPE"] == rule["Type"]).sum()
        st.markdown(f"""
        <div style="background-color:#1E293B; border:1px solid #334155; border-radius:8px; padding:10px; min-height:130px;">
            <b style="color:#60A5FA; font-size:12px;">{rule['Type']}</b><br>
            <span style="font-size:22px; font-weight:700; color:{'#EF4444' if cnt > 0 else '#10B981'};">{cnt}</span><br>
            <small style="color:#94A3B8;">{rule['Target Tables']}</small>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Filterable SQL Issues Table
st.subheader("Relational Audit Log Details")
if not sql_issues.empty:
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        type_filter = st.multiselect(
            "Filter by Check Type:",
            options=sql_issues["ISSUE_TYPE"].unique().tolist(),
            default=sql_issues["ISSUE_TYPE"].unique().tolist()
        )
    with f_col2:
        table_filter = st.multiselect(
            "Filter by Table:",
            options=sql_issues["TABLE_NAME"].unique().tolist(),
            default=sql_issues["TABLE_NAME"].unique().tolist()
        )
    with f_col3:
        sev_filter = st.multiselect(
            "Filter by Severity:",
            options=sql_issues["SEVERITY"].unique().tolist(),
            default=sql_issues["SEVERITY"].unique().tolist()
        )

    filtered_df = sql_issues[
        sql_issues["ISSUE_TYPE"].isin(type_filter) &
        sql_issues["TABLE_NAME"].isin(table_filter) &
        sql_issues["SEVERITY"].isin(sev_filter)
    ]

    st.write(f"Showing **{len(filtered_df)}** of **{len(sql_issues)}** detected rule violations.")
    st.dataframe(
        filtered_df[["RECORD_ID", "TABLE_NAME", "COLUMN_NAME", "ISSUE_TYPE", "SEVERITY", "DESCRIPTION"]],
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No SQL rule violations detected or checks have not been run. Click 'Execute All SQL Checks' above.")

