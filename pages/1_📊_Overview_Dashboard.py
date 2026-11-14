"""
Page 1: Overview Dashboard
Visualizes executive summary metrics, data quality scores, issue distributions,
and detection method breakdowns.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.title("📊 Executive Quality Overview Dashboard")
st.markdown("High-level synthesis of database health, quality scoring, and multi-engine anomaly distributions.")

if st.session_state.get("consolidated_df") is None or st.session_state.consolidated_df.empty:
    st.info("⚠️ No audit analysis has been executed yet. Click **'Run Complete Hybrid Audit'** in the sidebar or run individual checks.")
    st.stop()

summary = st.session_state.quality_summary
df_anom = st.session_state.consolidated_df

# KPI Cards
c1, c2, c3, c4 = st.columns(4)
with c1:
    score = summary.get("score", 0.0)
    grade = summary.get("grade", "N/A")
    st.metric("Data Quality Score", f"{score}%", delta=grade)

with c2:
    st.metric("Records Analyzed", f"{summary.get('total_records', 0):,}")

with c3:
    st.metric("Flagged Anomalies", f"{len(df_anom):,}")

with c4:
    sevs = summary.get("severity_counts", {})
    st.metric("High Severity", sevs.get("HIGH", 0), help="Critical defects and cross-engine corroborated flags")

st.markdown("---")

# Row 2: Secondary KPIs Breakdown
k1, k2, k3, k4 = st.columns(4)
cats = df_anom["ISSUE_CATEGORY"].str.upper()
with k1:
    null_cnt = cats.str.contains("NULL").sum()
    st.metric("Missing / NULL Values", null_cnt)
with k2:
    dup_cnt = cats.str.contains("DUPLICATE").sum()
    st.metric("Duplicate Violations", dup_cnt)
with k3:
    range_cnt = (cats.str.contains("RANGE") | cats.str.contains("OUT_OF_RANGE")).sum()
    st.metric("Invalid Range Records", range_cnt)
with k4:
    ml_cnt = cats.str.contains("STATISTICAL").sum()
    st.metric("ML Statistical Outliers", ml_cnt)

st.markdown("---")

# Visualizations Row
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("Issue Distribution by Severity")
    sev_counts = df_anom["SEVERITY"].value_counts().reset_index()
    sev_counts.columns = ["Severity", "Count"]
    
    color_map = {"HIGH": "#EF4444", "MEDIUM": "#F59E0B", "LOW": "#3B82F6"}
    fig_sev = px.pie(
        sev_counts,
        names="Severity",
        values="Count",
        color="Severity",
        color_discrete_map=color_map,
        hole=0.45
    )
    fig_sev.update_layout(
        paper_bgcolor="#1E293B",
        plot_bgcolor="#1E293B",
        font=dict(color="#F8FAFC"),
        margin=dict(t=20, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_sev, use_container_width=True)

with col_chart2:
    st.subheader("Detection Source Breakdown")
    method_counts = df_anom["DETECTION_METHOD"].value_counts().reset_index()
    method_counts.columns = ["Detection Method", "Count"]

    fig_method = px.bar(
        method_counts,
        x="Count",
        y="Detection Method",
        orientation="h",
        color="Count",
        color_continuous_scale="Blues"
    )
    fig_method.update_layout(
        paper_bgcolor="#1E293B",
        plot_bgcolor="#1E293B",
        font=dict(color="#F8FAFC"),
        margin=dict(t=20, b=20, l=20, r=20),
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_method, use_container_width=True)

# Quality Dimension Gauges
st.subheader("Data Quality Dimensions Compliance")
dims = summary.get("dimension_scores", {})
g1, g2, g3, g4 = st.columns(4)

def render_dimension_card(col, name, score_val):
    with col:
        st.markdown(f"""
        <div style="background-color:#1E293B; padding:12px; border-radius:8px; border:1px solid #334155; text-align:center;">
            <p style="color:#94A3B8; margin:0; font-size:13px;">{name}</p>
            <h3 style="color:{'#10B981' if score_val >= 90 else '#F59E0B' if score_val >= 70 else '#EF4444'}; margin:4px 0;">{score_val:.1f}%</h3>
            <small style="color:#64748B;">Target ≥ 95%</small>
        </div>
        """, unsafe_allow_html=True)

render_dimension_card(g1, "Completeness", dims.get("Completeness", 100.0))
render_dimension_card(g2, "Uniqueness", dims.get("Uniqueness", 100.0))
render_dimension_card(g3, "Validity", dims.get("Validity", 100.0))
render_dimension_card(g4, "Consistency", dims.get("Consistency", 100.0))

st.markdown("<br>", unsafe_allow_html=True)

# Recent Suspicious Records
st.subheader("Recent Flagged Records Sample")
display_cols = ["RECORD_ID", "TABLE_NAME", "DETECTION_METHOD", "ISSUE_CATEGORY", "SEVERITY", "EXPLANATION"]
st.dataframe(
    df_anom[display_cols].head(10),
    use_container_width=True,
    hide_index=True
)

