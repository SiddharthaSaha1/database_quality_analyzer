"""
Page 3: Machine Learning Anomaly Detection Analysis
Interactive exploration of Isolation Forest and DBSCAN models,
multidimensional scatter visualizations, anomaly score distributions, and algorithm comparison.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from ml.preprocessing import MLPreprocessor
from ml.isolation_forest import IsolationForestDetector
from ml.dbscan import DBSCANDetector
from ml.model_evaluation import ModelEvaluator
from utils.config import ML_CONTAMINATION, ML_RANDOM_STATE, DBSCAN_EPS, DBSCAN_MIN_SAMPLES

st.title("🧠 Machine Learning Anomaly Detection")
st.markdown("""
Unsupervised multivariate pattern analysis using **Isolation Forest** (ensemble tree isolation) 
and **DBSCAN** (density-based spatial clustering). Identifies unusual feature combinations that satisfy SQL rules but violate statistical norms.
""")

tables = st.session_state.get("tables_dict", {})
if not tables:
    st.warning("Please load or connect to a dataset first.")
    st.stop()

# Interactive Hyperparameter Controls
st.subheader("Model Hyperparameter Tuning")
c_param1, c_param2, c_param3, c_param4 = st.columns(4)
with c_param1:
    contamination = st.slider("IF Contamination", min_value=0.01, max_value=0.20, value=ML_CONTAMINATION, step=0.01,
                              help="Expected proportion of outliers in the dataset.")
with c_param2:
    n_trees = st.slider("IF Trees (n_estimators)", min_value=50, max_value=300, value=150, step=25)
with c_param3:
    db_eps = st.slider("DBSCAN Epsilon (eps)", min_value=0.1, max_value=2.0, value=DBSCAN_EPS, step=0.05,
                       help="Maximum distance between points to be considered in the same neighborhood.")
with c_param4:
    db_min_samples = st.slider("DBSCAN Min Samples", min_value=2, max_value=15, value=DBSCAN_MIN_SAMPLES, step=1)

# Execution Buttons
b1, b2, b3 = st.columns(3)
with b1:
    run_if_btn = st.button("🌲 Run Isolation Forest Only", use_container_width=True)
with b2:
    run_db_btn = st.button("🌐 Run DBSCAN Only", use_container_width=True)
with b3:
    run_both_btn = st.button("⚡ Run Both & Compare", type="primary", use_container_width=True)

# Pipeline trigger
if run_if_btn or run_db_btn or run_both_btn or st.session_state.ml_results_df.empty:
    with st.spinner("Extracting features and training anomaly detection models..."):
        pre = MLPreprocessor()
        analytical = pre.build_analytical_dataset(tables)
        X_scaled, X_df, full_df = pre.prepare_features(analytical)

        # Run Isolation Forest
        if_model = IsolationForestDetector(contamination=contamination, random_state=ML_RANDOM_STATE, n_estimators=n_trees)
        if_res = if_model.fit_predict(X_scaled, analytical)

        # Run DBSCAN
        db_model = DBSCANDetector(eps=db_eps, min_samples=db_min_samples)
        combined_res = db_model.fit_predict(X_scaled, if_res)

        st.session_state.ml_results_df = combined_res
        st.session_state.model_comparison = ModelEvaluator.compare_models(combined_res)
        st.success("Model execution complete!")

ml_df = st.session_state.ml_results_df
comp = st.session_state.model_comparison

# Metric Summary Cards
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Total Records Modeled", f"{comp.get('total_records', 0):,}")
with m2:
    st.metric("Isolation Forest Outliers", f"{comp.get('isolation_forest_total', 0):,}",
              help="Flagged by recursive binary decision path isolation.")
with m3:
    st.metric("DBSCAN Noise Points", f"{comp.get('dbscan_total', 0):,}",
              help="Observations outside dense cluster cores.")
with m4:
    st.metric("Agreed by Both Models", f"{comp.get('both_count', 0):,}",
              delta=f"Jaccard: {comp.get('jaccard_similarity', 0.0)}")

st.markdown("---")

# Visualizations Row 1: Multidimensional Scatter & Anomaly Score Histogram
v1, v2 = st.columns(2)

with v1:
    st.subheader("Multivariate Feature Space: Attendance vs Exam Score")
    # Color code: Normal (0), IF Only (1), DBSCAN Only (2), Both (3)
    def assign_category(row):
        is_if = row.get("IF_IS_ANOMALOUS", False)
        is_db = row.get("DBSCAN_IS_ANOMALOUS", False)
        if is_if and is_db:
            return "Both Models Flagged"
        elif is_if:
            return "Isolation Forest Only"
        elif is_db:
            return "DBSCAN Only"
        return "Normal"

    ml_df["ML_FLAG_STATUS"] = ml_df.apply(assign_category, axis=1)

    fig_scatter = px.scatter(
        ml_df,
        x="ATTENDANCE_PERCENTAGE",
        y="MARKS_PERCENTAGE",
        color="ML_FLAG_STATUS",
        color_discrete_map={
            "Normal": "#3B82F6",
            "Isolation Forest Only": "#F59E0B",
            "DBSCAN Only": "#A855F7",
            "Both Models Flagged": "#EF4444"
        },
        hover_data=["STUDENT_ID", "COURSE_ID", "AGE", "ATTENDANCE_VS_MARKS_GAP"],
        labels={"ATTENDANCE_PERCENTAGE": "Attendance %", "MARKS_PERCENTAGE": "Exam Score %"}
    )
    fig_scatter.update_layout(
        paper_bgcolor="#1E293B",
        plot_bgcolor="#1E293B",
        font=dict(color="#F8FAFC"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with v2:
    st.subheader("Isolation Forest Anomaly Score Distribution")
    fig_hist = px.histogram(
        ml_df,
        x="IF_ANOMALY_SCORE",
        color="IF_IS_ANOMALOUS",
        nbins=35,
        color_discrete_map={False: "#3B82F6", True: "#EF4444"},
        labels={"IF_ANOMALY_SCORE": "Normalized Anomaly Score (0.0 to 1.0)", "count": "Record Count"}
    )
    fig_hist.update_layout(
        paper_bgcolor="#1E293B",
        plot_bgcolor="#1E293B",
        font=dict(color="#F8FAFC"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_hist, use_container_width=True)

st.markdown("---")

# Algorithm Comparison Breakdown Table
st.subheader("Comparative Cross-Model Contingency Table")
comp_df = pd.DataFrame([
    {"Detection Outcome": "Flagged by BOTH Isolation Forest & DBSCAN", "Record Count": comp.get("both_count", 0), "Clinical Risk": "High (Multi-model consensus)"},
    {"Detection Outcome": "Flagged by Isolation Forest ONLY", "Record Count": comp.get("if_only_count", 0), "Clinical Risk": "Medium (Tree path outlier)"},
    {"Detection Outcome": "Flagged by DBSCAN ONLY", "Record Count": comp.get("dbscan_only_count", 0), "Clinical Risk": "Medium (Low local density)"},
    {"Detection Outcome": "Unflagged by Both (Normal Inliers)", "Record Count": comp.get("neither_count", 0), "Clinical Risk": "None (Within standard distribution)"}
])
st.dataframe(comp_df, use_container_width=True, hide_index=True)

