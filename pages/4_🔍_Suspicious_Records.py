"""
Page 4: Suspicious Records Explorer
Searchable, sortable, and filterable investigation panel with drill-down record inspection,
original feature attribute values, mathematical anomaly explanations, and severity badges.
"""

import streamlit as st
import pandas as pd
from utils.helpers import deserialize_record

st.title("🔍 Suspicious Records Investigation Panel")
st.markdown("""
Interactive triage workspace. Inspect consolidated issues flagged across Oracle SQL/PLSQL rules 
and machine learning anomaly detectors.
""")

consolidated = st.session_state.get("consolidated_df")
if consolidated is None or consolidated.empty:
    st.info("No consolidated anomalies found. Please execute the audit from the sidebar.")
    st.stop()

# Filter Controls
with st.expander("🛠️ Filter & Search Controls", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        search_query = st.text_input("Search by Record ID or keyword:", placeholder="e.g. STU1015, ATT10012, email")
    with col2:
        sev_options = consolidated["SEVERITY"].unique().tolist()
        selected_sevs = st.multiselect("Severity Level:", options=sev_options, default=sev_options)
    with col3:
        table_options = consolidated["TABLE_NAME"].unique().tolist()
        selected_tables = st.multiselect("Source Table:", options=table_options, default=table_options)

    col4, col5 = st.columns(2)
    with col4:
        method_options = consolidated["DETECTION_METHOD"].unique().tolist()
        selected_methods = st.multiselect("Detection Engine:", options=method_options, default=method_options)
    with col5:
        min_score = st.slider("Minimum Anomaly Score (ML Flags):", min_value=0.0, max_value=1.0, value=0.0, step=0.05)

# Apply Filters
filtered = consolidated[
    consolidated["SEVERITY"].isin(selected_sevs) &
    consolidated["TABLE_NAME"].isin(selected_tables) &
    consolidated["DETECTION_METHOD"].isin(selected_methods)
]

if search_query:
    q = search_query.lower()
    mask = (
        filtered["RECORD_ID"].astype(str).str.lower().str.contains(q) |
        filtered["EXPLANATION"].astype(str).str.lower().str.contains(q) |
        filtered["ISSUE_CATEGORY"].astype(str).str.lower().str.contains(q)
    )
    filtered = filtered[mask]

if min_score > 0.0:
    filtered = filtered[
        filtered["ANOMALY_SCORE"].isna() | (filtered["ANOMALY_SCORE"] >= min_score)
    ]

st.markdown(f"**Found {len(filtered)} matching flagged records** (out of {len(consolidated)} total):")

# Main Interactive Table
disp_cols = ["ANOMALY_ID", "RECORD_ID", "TABLE_NAME", "SEVERITY", "DETECTION_METHOD", "ISSUE_CATEGORY", "ANOMALY_SCORE"]
st.dataframe(
    filtered[disp_cols],
    use_container_width=True,
    hide_index=True
)

st.markdown("---")

# Record Inspector Drilldown
st.subheader("🔎 Deep-Dive Record Inspector")
if not filtered.empty:
    selected_id = st.selectbox(
        "Select a Record to Inspect:",
        options=filtered["ANOMALY_ID"].tolist(),
        format_func=lambda x: f"Anomaly #{x} - Rec: {filtered.loc[filtered['ANOMALY_ID']==x, 'RECORD_ID'].values[0]} ({filtered.loc[filtered['ANOMALY_ID']==x, 'TABLE_NAME'].values[0]} | {filtered.loc[filtered['ANOMALY_ID']==x, 'SEVERITY'].values[0]})"
    )

    rec = filtered[filtered["ANOMALY_ID"] == selected_id].iloc[0]

    # Two Column Layout
    detail_col1, detail_col2 = st.columns([1, 1])

    with detail_col1:
        st.markdown(f"""
        <div style="background-color:#1E293B; border:1px solid #334155; border-radius:8px; padding:16px;">
            <h4 style="margin-top:0; color:#38BDF8;">Audit Identification</h4>
            <table style="width:100%; font-size:13px; color:#F8FAFC;">
                <tr><td style="color:#94A3B8;">Anomaly ID:</td><td><b>#{rec['ANOMALY_ID']}</b></td></tr>
                <tr><td style="color:#94A3B8;">Target Record ID:</td><td><code>{rec['RECORD_ID']}</code></td></tr>
                <tr><td style="color:#94A3B8;">Database Table:</td><td><b>{rec['TABLE_NAME']}</b></td></tr>
                <tr><td style="color:#94A3B8;">Detection Engine:</td><td>{rec['DETECTION_METHOD']}</td></tr>
                <tr><td style="color:#94A3B8;">Issue Category:</td><td>{rec['ISSUE_CATEGORY']}</td></tr>
                <tr><td style="color:#94A3B8;">Severity Rating:</td><td><b>{rec['SEVERITY']}</b></td></tr>
                <tr><td style="color:#94A3B8;">ML Anomaly Score:</td><td>{rec['ANOMALY_SCORE'] if pd.notna(rec['ANOMALY_SCORE']) else 'N/A (Rule Engine)'}</td></tr>
                <tr><td style="color:#94A3B8;">Detected At:</td><td>{rec['DETECTION_TIMESTAMP']}</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background-color:#1E293B; border-left:4px solid #38BDF8; border-radius:4px; padding:12px;">
            <b style="color:#38BDF8;">Audit Explanation & Root Cause:</b><br>
            <p style="margin:4px 0 0 0; font-size:13px; color:#F1F5F9;">{rec['EXPLANATION']}</p>
        </div>
        """, unsafe_allow_html=True)

    with detail_col2:
        st.markdown("#### Original Database Attribute Values")
        orig_dict = deserialize_record(rec["ORIGINAL_VALUES"])
        if orig_dict:
            orig_df = pd.DataFrame(list(orig_dict.items()), columns=["Attribute / Column", "Recorded Value"])
            st.dataframe(orig_df, use_container_width=True, hide_index=True)
        else:
            st.write("No raw column dictionary attached.")
else:
    st.info("No records match the current filter criteria.")

