"""
Page 5: Dataset Management & Database Connectivity
Oracle connection configuration, credential testing, schema inspection,
table preview, column selection, and custom CSV dataset upload.
"""

import streamlit as st
import pandas as pd
from database.connection import OracleDatabaseManager, CSVDatabaseAdapter, ORACLEDB_AVAILABLE
from utils.config import ORACLE_USER, ORACLE_HOST, ORACLE_PORT, ORACLE_SERVICE_NAME

st.title("📁 Dataset Management & Database Connectivity")
st.markdown("""
Manage database connections, inspect relational tables, and upload demonstration data.
Supports **Oracle Database** (Thin mode via `python-oracledb`) and offline **CSV Demonstration Mode**.
""")

tab_conn, tab_tables, tab_upload = st.tabs([
    "🔌 Oracle Database Connection",
    "📋 Schema & Table Explorer",
    "📤 Custom Dataset Ingestion"
])

# -------------------------------------------------------------
# TAB 1: ORACLE CONNECTION
# -------------------------------------------------------------
with tab_conn:
    st.subheader("Oracle Database Configuration")
    st.markdown("""
    Configure connection parameters to your Oracle instance (Oracle XE, Enterprise Edition, or Oracle Cloud Autonomous Database).
    Credentials can also be stored securely in `.env` or `.streamlit/secrets.toml`.
    """)

    c_host, c_port = st.columns([3, 1])
    with c_host:
        host_val = st.text_input("Oracle Host:", value=ORACLE_HOST)
    with c_port:
        port_val = st.number_input("Port:", value=ORACLE_PORT, step=1)

    c_svc, c_usr = st.columns(2)
    with c_svc:
        svc_val = st.text_input("Service Name / PDB:", value=ORACLE_SERVICE_NAME, help="e.g. XEPDB1 or FREEPDB1")
    with c_usr:
        usr_val = st.text_input("Username:", value=ORACLE_USER)

    pwd_val = st.text_input("Password:", type="password", help="Secure password for Oracle schema owner.")

    col_tst, col_status = st.columns([1, 3])
    with col_tst:
        if st.button("🧪 Test Connection", type="primary"):
            test_mgr = OracleDatabaseManager(
                user=usr_val,
                password=pwd_val,
                host=host_val,
                port=port_val,
                service_name=svc_val
            )
            success, msg = test_mgr.test_connection()
            if success:
                st.session_state.oracle_manager = test_mgr
                st.session_state.db_mode = "Oracle"
                st.success(f"Connection Successful! {msg}")
            else:
                st.error(f"Connection Failed:\n{msg}")
                st.info("""
                **Troubleshooting Checklist:**
                - Ensure Oracle Database listener is active (`lsnrctl status`).
                - Ensure target port (default 1521) is unblocked by firewall.
                - Verify service name (`XEPDB1`) and user grant permissions (`GRANT CONNECT, RESOURCE TO user;`).
                - If testing without a running Oracle instance, switch to **CSV Demonstration Mode** in the sidebar.
                """)

    st.markdown("---")
    st.subheader("Database Schema Initialization Instructions")
    st.markdown("""
    To create the initial schema and stored procedures inside Oracle SQL*Plus or SQL Developer:
    1. Run `database/schema.sql` to generate `STUDENT`, `COURSE`, `ATTENDANCE`, `EXAM_RESULT`.
    2. Run `database/audit_tables.sql` to initialize `AUDIT_LOG` and `CONSOLIDATED_ANOMALIES`.
    3. Run `database/procedures.sql` to compile package `PKG_DATA_QUALITY`.
    4. Run `database/sample_data.sql` (clean) or `database/corrupted_data.sql` (controlled corrupted).
    """)

# -------------------------------------------------------------
# TAB 2: SCHEMA & TABLE EXPLORER
# -------------------------------------------------------------
with tab_tables:
    st.subheader("Relational Schema Inspection")
    tables = st.session_state.get("tables_dict", {})

    if not tables:
        st.warning("No tables currently loaded.")
    else:
        table_name = st.selectbox("Select Table to Preview:", list(tables.keys()))
        df_target = tables[table_name]

        t_col1, t_col2 = st.columns(2)
        with t_col1:
            st.metric("Total Rows", f"{len(df_target):,}")
        with t_col2:
            st.metric("Total Columns", len(df_target.columns))

        # Column Selector
        all_cols = list(df_target.columns)
        selected_cols = st.multiselect("Select Columns to Display:", options=all_cols, default=all_cols)

        row_limit = st.slider("Preview Rows:", min_value=5, max_value=200, value=25, step=5)
        st.dataframe(df_target[selected_cols].head(row_limit), use_container_width=True)

# -------------------------------------------------------------
# TAB 3: CUSTOM DATASET INGESTION
# -------------------------------------------------------------
with tab_upload:
    st.subheader("Upload Custom Demonstration CSV File")
    st.markdown("Upload a custom student performance CSV to analyze for quality anomalies.")

    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
    if uploaded_file is not None:
        try:
            custom_df = pd.read_csv(uploaded_file)
            st.success(f"Uploaded successfully! Loaded {len(custom_df)} rows and {len(custom_df.columns)} columns.")
            st.dataframe(custom_df.head(10), use_container_width=True)

            target_table = st.selectbox("Assign to Staging Table:", ["STUDENT", "ATTENDANCE", "EXAM_RESULT"])
            if st.button("Ingest into Active Session"):
                st.session_state.tables_dict[target_table] = custom_df
                st.success(f"Updated {target_table} in memory with uploaded data.")
        except Exception as e:
            st.error(f"Error parsing CSV file: {e}")

