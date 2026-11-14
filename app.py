"""
AI-Based Database Data-Quality Analyzer
Main Streamlit Application Entrypoint
Coordinates session state, Oracle connectivity, and multi-page routing.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database.connection import OracleDatabaseManager, CSVDatabaseAdapter, ORACLEDB_AVAILABLE
from detection.detection_manager import DetectionManager
from ml.preprocessing import MLPreprocessor
from ml.isolation_forest import IsolationForestDetector
from ml.dbscan import DBSCANDetector
from ml.model_evaluation import ModelEvaluator
from integration.result_merger import ResultMerger
from integration.quality_scorer import QualityScorer
from utils.config import (
    ORACLE_USER, ORACLE_HOST, ORACLE_PORT, ORACLE_SERVICE_NAME,
    ML_CONTAMINATION, ML_RANDOM_STATE, DBSCAN_EPS, DBSCAN_MIN_SAMPLES,
    SEVERITY_WEIGHTS
)

# Streamlit Page Configuration
st.set_page_config(
    page_title="AI Database Quality Analyzer",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark navy / charcoal minimal UI styling
st.markdown("""
<style>
    .reportview-container, .main, .block-container {
        background-color: #0F172A;
        color: #F8FAFC;
    }
    .stMetric {
        background-color: #1E293B;
        padding: 14px;
        border-radius: 8px;
        border: 1px solid #334155;
    }
    .metric-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .badge-high {
        background-color: #7F1D1D;
        color: #FCA5A5;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 11px;
    }
    .badge-med {
        background-color: #78350F;
        color: #FCD34D;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 11px;
    }
    .badge-low {
        background-color: #1E3A8A;
        color: #93C5FD;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 11px;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initializes global state variables."""
    if "db_mode" not in st.session_state:
        st.session_state.db_mode = "CSV_Demo"  # Default fallback mode
    if "demo_dataset_type" not in st.session_state:
        st.session_state.demo_dataset_type = "corrupted"
    if "csv_adapter" not in st.session_state:
        st.session_state.csv_adapter = CSVDatabaseAdapter(mode=st.session_state.demo_dataset_type)
    if "oracle_manager" not in st.session_state:
        st.session_state.oracle_manager = OracleDatabaseManager()
    if "tables_dict" not in st.session_state:
        st.session_state.tables_dict = st.session_state.csv_adapter.fetch_all_tables()
    if "sql_issues_df" not in st.session_state:
        st.session_state.sql_issues_df = pd.DataFrame()
    if "ml_results_df" not in st.session_state:
        st.session_state.ml_results_df = pd.DataFrame()
    if "consolidated_df" not in st.session_state:
        st.session_state.consolidated_df = pd.DataFrame()
    if "quality_summary" not in st.session_state:
        st.session_state.quality_summary = {}
    if "model_comparison" not in st.session_state:
        st.session_state.model_comparison = {}
    if "last_run_timestamp" not in st.session_state:
        st.session_state.last_run_timestamp = None

initialize_session_state()

def run_full_pipeline():
    """Executes the entire hybrid data quality pipeline end-to-end."""
    with st.spinner("Executing SQL/PLSQL Rule Engine, Isolation Forest, and DBSCAN..."):
        # 1. Fetch data
        if st.session_state.db_mode == "Oracle":
            oracle_ok, msg = st.session_state.oracle_manager.test_connection()
            if not oracle_ok:
                st.error(f"Cannot run on Oracle Database: {msg}")
                return
            tables = {
                "STUDENT": st.session_state.oracle_manager.fetch_table("STUDENT"),
                "COURSE": st.session_state.oracle_manager.fetch_table("COURSE"),
                "ATTENDANCE": st.session_state.oracle_manager.fetch_table("ATTENDANCE"),
                "EXAM_RESULT": st.session_state.oracle_manager.fetch_table("EXAM_RESULT")
            }
            # Attempt to execute PL/SQL package
            try:
                sql_issues = st.session_state.oracle_manager.run_all_oracle_quality_checks()[1]
            except Exception as e:
                # Fallback to local rule engine against oracle tables
                mgr = DetectionManager(db_manager=st.session_state.oracle_manager)
                sql_issues = mgr.run_all_rule_checks(tables, source="ORACLE_SQL")
        else:
            tables = st.session_state.csv_adapter.fetch_all_tables()
            mgr = DetectionManager(csv_adapter=st.session_state.csv_adapter)
            sql_issues = mgr.run_all_rule_checks(tables, source="DEMO_SQL_ENGINE")

        st.session_state.tables_dict = tables
        st.session_state.sql_issues_df = sql_issues

        # 2. ML Engine Execution
        preprocessor = MLPreprocessor()
        analytical_df = preprocessor.build_analytical_dataset(tables)
        X_scaled, _, _ = preprocessor.prepare_features(analytical_df)

        if_detector = IsolationForestDetector(contamination=ML_CONTAMINATION, random_state=ML_RANDOM_STATE)
        if_res = if_detector.fit_predict(X_scaled, analytical_df)

        db_detector = DBSCANDetector(eps=DBSCAN_EPS, min_samples=DBSCAN_MIN_SAMPLES)
        ml_res = db_detector.fit_predict(X_scaled, if_res)

        st.session_state.ml_results_df = ml_res
        st.session_state.model_comparison = ModelEvaluator.compare_models(ml_res)

        # 3. Hybrid Result Consolidation
        consolidated = ResultMerger.merge_results(sql_issues, ml_res, raw_tables_dict=tables)
        st.session_state.consolidated_df = consolidated

        # 4. Transparent Quality Scoring
        total_recs = len(tables.get("STUDENT", [])) + len(tables.get("ATTENDANCE", [])) + len(tables.get("EXAM_RESULT", []))
        summary = QualityScorer.calculate_score(consolidated, total_records_analyzed=total_recs)
        st.session_state.quality_summary = summary
        st.session_state.last_run_timestamp = datetime.now()

        st.success(f"Audit pipeline finished successfully at {st.session_state.last_run_timestamp.strftime('%H:%M:%S')}!")

# Sidebar Controls & Navigation Header
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=64)
    st.title("Data-Quality Analyzer")
    st.markdown("<small style='color:#94A3B8;'>Oracle SQL/PLSQL + ML Anomaly Detection</small>", unsafe_allow_html=True)
    st.divider()

    st.subheader("Data Source Mode")
    source_choice = st.radio(
        "Select Active Engine:",
        ["CSV Demonstration Mode", "Live Oracle Database"],
        index=0 if st.session_state.db_mode == "CSV_Demo" else 1
    )
    if source_choice == "Live Oracle Database":
        st.session_state.db_mode = "Oracle"
        st.info(f"Target: `{ORACLE_HOST}:{ORACLE_PORT}/{ORACLE_SERVICE_NAME}`")
    else:
        st.session_state.db_mode = "CSV_Demo"
        demo_type = st.selectbox(
            "Demo Dataset:",
            ["Controlled Corrupted (Staging)", "Clean Baseline (Pristine)"],
            index=0 if st.session_state.demo_dataset_type == "corrupted" else 1
        )
        new_mode = "corrupted" if "Corrupted" in demo_type else "clean"
        if new_mode != st.session_state.demo_dataset_type:
            st.session_state.demo_dataset_type = new_mode
            st.session_state.csv_adapter = CSVDatabaseAdapter(mode=new_mode)
            st.session_state.tables_dict = st.session_state.csv_adapter.fetch_all_tables()
            st.session_state.consolidated_df = pd.DataFrame()
            st.session_state.quality_summary = {}

    st.divider()
    if st.button("🚀 Run Complete Hybrid Audit", use_container_width=True, type="primary"):
        run_full_pipeline()
        st.rerun()

    if st.session_state.last_run_timestamp:
        st.caption(f"Last audit: {st.session_state.last_run_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

# Landing Page Content
st.title("🛡️ AI-Based Database Data-Quality Analyzer")
st.markdown("""
A hybrid academic and enterprise data quality audit platform that merges **Oracle SQL/PLSQL rule-based validation** 
with **unsupervised machine learning anomaly detection** (Isolation Forest & DBSCAN).
""")

# Top Overview Cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    cur_score = st.session_state.quality_summary.get("score")
    if cur_score is not None:
        st.metric("Data Quality Score", f"{cur_score}/100", delta=f"{st.session_state.quality_summary.get('grade', '')}")
    else:
        st.metric("Data Quality Score", "N/A", help="Run audit pipeline to calculate score.")

with col2:
    tot_rec = st.session_state.quality_summary.get("total_records", 0)
    st.metric("Records Analyzed", f"{tot_rec:,}")

with col3:
    tot_issues = st.session_state.quality_summary.get("deduplicated_issues", 0)
    st.metric("Flagged Issues", f"{tot_issues:,}")

with col4:
    sevs = st.session_state.quality_summary.get("severity_counts", {})
    st.metric("Critical (High)", sevs.get("HIGH", 0), delta_color="inverse")

st.markdown("---")

col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("System Architecture & Hybrid Detection Workflow")
    st.markdown("""
    1. **Relational Database Staging**: Ingests student cohorts, course enrollment, class attendance, and examination marks into Oracle relational schema.
    2. **Oracle SQL & PL/SQL Stored Procedures**: Executes deterministic validation queries checking for mandatory `NULL` violations, primary/foreign key uniqueness, boundary range constraints, and arithmetic consistency (`ATTENDED_CLASSES <= TOTAL_CLASSES`).
    3. **Machine Learning Anomaly Detection**:
       - **Isolation Forest**: Identifies multidimensional outliers in attendance vs. performance distributions without arbitrary identifiers.
       - **DBSCAN**: Detects isolated noise records lying in sparse feature regions.
    4. **Hybrid Result Merger & Severity Classification**: Deduplicates findings across both engines, escalates multi-method corroborated flags to `HIGH` severity, and stores results in `CONSOLIDATED_ANOMALIES`.
    5. **Transparent Governance Scoring**: Calculates audit scores with mathematical explanations.
    """)

with col_right:
    st.subheader("Active Configuration Status")
    st.markdown(f"""
    - **Current Engine**: `{'Live Oracle Database' if st.session_state.db_mode == 'Oracle' else 'Local Demonstration (CSV Adapter)'}`
    - **Dataset Profile**: `{st.session_state.demo_dataset_type.title() if st.session_state.db_mode == 'CSV_Demo' else 'Oracle Staging Schema'}`
    - **python-oracledb Driver**: `{'Installed & Ready' if ORACLEDB_AVAILABLE else 'Not Installed'}`
    - **Isolation Forest Contamination**: `{ML_CONTAMINATION}`
    - **DBSCAN Hyperparameters**: `eps={DBSCAN_EPS}, min_samples={DBSCAN_MIN_SAMPLES}`
    - **Severity Weights**: `HIGH={SEVERITY_WEIGHTS['HIGH']}, MED={SEVERITY_WEIGHTS['MEDIUM']}, LOW={SEVERITY_WEIGHTS['LOW']}`
    """)

    if st.session_state.consolidated_df.empty:
        st.info("💡 **Ready to begin**: Click **'Run Complete Hybrid Audit'** in the sidebar to analyze the database and generate findings.")
    else:
        st.success("✅ Audit active! Navigate using the sidebar pages to explore detailed SQL rules, ML distributions, suspicious records, and reports.")

