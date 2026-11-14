"""
Page 6: Executive Reports & Export
Generates and downloads audit summaries in CSV and enterprise-grade PDF formats.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from reports.csv_report import CSVReportGenerator
from reports.pdf_report import PDFReportGenerator

st.title("📑 Audit Reports & Download Center")
st.markdown("""
Generate exportable audit artifacts for compliance verification, academic submissions,
and executive data governance reporting.
""")

consolidated = st.session_state.get("consolidated_df")
summary = st.session_state.get("quality_summary", {})
comp = st.session_state.get("model_comparison", {})

if consolidated is None or consolidated.empty:
    st.info("No audit has been performed yet. Run the hybrid audit first to compile findings into reports.")
    st.stop()

# Report Configuration Card
st.subheader("Report Contents Summary")
r_col1, r_col2, r_col3 = st.columns(3)
with r_col1:
    st.metric("Quality Score", f"{summary.get('score', 0.0)}%", delta=summary.get("grade", ""))
with r_col2:
    st.metric("Deduplicated Findings", len(consolidated))
with r_col3:
    st.metric("Analyzed Records", f"{summary.get('total_records', 0):,}")

st.markdown("---")

# Download Action Buttons
st.subheader("Download Export Packages")
d_col1, d_col2 = st.columns(2)

# 1. PDF Report
with d_col1:
    st.markdown("""
    <div style="background-color:#1E293B; border:1px solid #334155; border-radius:8px; padding:18px;">
        <h4 style="margin-top:0; color:#38BDF8;">📄 Academic & Executive PDF Report</h4>
        <p style="color:#94A3B8; font-size:13px;">
            Comprehensive formatted audit document with quality score badges, dimension breakdown, 
            comparative ML analytics, and top suspicious record case studies.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    with st.spinner("Compiling PDF document..."):
        try:
            pdf_bytes = PDFReportGenerator.generate_report(summary, comp, consolidated, top_n=20)
            st.download_button(
                label="📥 Download Audit Report (PDF)",
                data=pdf_bytes,
                file_name=f"Data_Quality_Audit_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error compiling PDF report: {e}")

# 2. CSV Raw Export
with d_col2:
    st.markdown("""
    <div style="background-color:#1E293B; border:1px solid #334155; border-radius:8px; padding:18px;">
        <h4 style="margin-top:0; color:#38BDF8;">📊 Consolidated Findings (CSV)</h4>
        <p style="color:#94A3B8; font-size:13px;">
            Full structured CSV export conforming to the CONSOLIDATED_ANOMALIES schema, including 
            record IDs, original values, severity classifications, and anomaly scores.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    csv_bytes = CSVReportGenerator.generate_consolidated_csv(consolidated)
    st.download_button(
        label="📥 Download Consolidated Anomalies (CSV)",
        data=csv_bytes,
        file_name=f"Consolidated_Anomalies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# Preview of Exported Data
st.subheader("Report Table Preview")
st.dataframe(
    consolidated[["ANOMALY_ID", "RECORD_ID", "TABLE_NAME", "DETECTION_METHOD", "SEVERITY", "EXPLANATION"]].head(15),
    use_container_width=True,
    hide_index=True
)

