"""
Database Connection and Management Module
Supports:
1. Native Oracle Database connectivity via python-oracledb (Thin mode).
2. Diagnostic connection testing, transaction handling, and parameterized query execution.
3. PL/SQL procedure execution.
4. Separate CSV Demo Adapter for offline evaluation when Oracle server is not accessible.
"""

import os
from pathlib import Path
import pandas as pd
from utils.config import (
    ORACLE_USER, ORACLE_PASSWORD, ORACLE_HOST, ORACLE_PORT,
    ORACLE_SERVICE_NAME, ORACLE_DSN, ALLOW_DEMO_MODE,
    CLEAN_DATA_DIR, CORRUPTED_DATA_DIR, BASE_DIR
)
from utils.helpers import logger

try:
    import oracledb
    ORACLEDB_AVAILABLE = True
except ImportError:
    ORACLEDB_AVAILABLE = False
    logger.warning("python-oracledb is not installed. Live Oracle connectivity will be unavailable.")

class OracleDatabaseManager:
    """Manages live connections, queries, and stored procedures on Oracle Database."""
    
    def __init__(self, user=None, password=None, host=None, port=None, service_name=None, dsn=None):
        self.user = user or ORACLE_USER
        self.password = password or ORACLE_PASSWORD
        self.host = host or ORACLE_HOST
        self.port = port or ORACLE_PORT
        self.service_name = service_name or ORACLE_SERVICE_NAME
        self.dsn = dsn or ORACLE_DSN
        self._connection = None

    def get_dsn(self):
        if self.dsn:
            return self.dsn
        return f"{self.host}:{self.port}/{self.service_name}"

    def connect(self):
        """Establishes connection to Oracle Database in Thin mode."""
        if not ORACLEDB_AVAILABLE:
            raise RuntimeError("python-oracledb is not installed. Please run: pip install oracledb")
        
        if not self.password:
            raise ValueError(
                "Oracle Database password is not set. Please provide credentials via environment variable "
                "ORACLE_PASSWORD or the Dataset Management settings page."
            )

        try:
            conn = oracledb.connect(
                user=self.user,
                password=self.password,
                dsn=self.get_dsn()
            )
            return conn
        except oracledb.Error as e:
            error_obj, = e.args
            err_msg = (
                f"Oracle Connection Error [{error_obj.code}]: {error_obj.message}\n"
                f"Target DSN: {self.get_dsn()} | User: {self.user}\n"
                "Remediation: Verify that Oracle Database listener is running, port 1521 is accessible, "
                "and the service name is valid."
            )
            logger.error(err_msg)
            raise ConnectionError(err_msg) from e

    def test_connection(self):
        """Tests live Oracle connectivity and returns (success_bool, status_message)."""
        if not ORACLEDB_AVAILABLE:
            return False, "python-oracledb library is not installed."
        if not self.password:
            return False, "No Oracle password configured. Set ORACLE_PASSWORD in .env or the UI."

        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT banner FROM v$version WHERE ROWNUM = 1")
                    row = cursor.fetchone()
                    banner = row[0] if row else "Oracle Database (Active)"
                    return True, f"Successfully connected! Banner: {banner}"
        except Exception as e:
            return False, str(e)

    def execute_query(self, query, params=None):
        """Executes a SELECT query and returns a pandas DataFrame."""
        with self.connect() as conn:
            return pd.read_sql(query, conn, params=params)

    def execute_non_query(self, sql, params=None):
        """Executes DDL/DML statements."""
        with self.connect() as conn:
            with conn.cursor() as cursor:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
            conn.commit()

    def execute_plsql_procedure(self, proc_name, params=None):
        """Invokes a PL/SQL stored procedure."""
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.callproc(proc_name, params or [])
            conn.commit()

    def run_all_oracle_quality_checks(self):
        """Executes PKG_DATA_QUALITY.RUN_ALL_QUALITY_CHECKS in Oracle and retrieves AUDIT_LOG."""
        with self.connect() as conn:
            with conn.cursor() as cursor:
                out_count = cursor.var(oracledb.NUMBER)
                cursor.callproc("PKG_DATA_QUALITY.RUN_ALL_QUALITY_CHECKS", [out_count])
                total_detected = out_count.getvalue()
            conn.commit()
            
            # Fetch recent audit findings
            audit_df = pd.read_sql(
                "SELECT ISSUE_ID, RECORD_ID, TABLE_NAME, COLUMN_NAME, ISSUE_TYPE, DESCRIPTION, "
                "SEVERITY, DETECTION_TIMESTAMP, DETECTION_SOURCE "
                "FROM AUDIT_LOG ORDER BY DETECTION_TIMESTAMP DESC",
                conn
            )
            return int(total_detected or 0), audit_df

    def fetch_table(self, table_name, limit=5000):
        """Safely fetches rows from an allowed relational table."""
        allowed_tables = ["STUDENT", "COURSE", "ATTENDANCE", "EXAM_RESULT", "AUDIT_LOG", "CONSOLIDATED_ANOMALIES"]
        t_upper = table_name.upper().strip()
        if t_upper not in allowed_tables:
            raise ValueError(f"Table '{table_name}' is not in the recognized schema catalog.")
        
        query = f"SELECT * FROM {t_upper} WHERE ROWNUM <= :lim"
        with self.connect() as conn:
            return pd.read_sql(query, conn, params={"lim": limit})


class CSVDatabaseAdapter:
    """
    Clearly separated demonstration mode adapter.
    Reads local clean or controlled-corrupted CSV datasets when Oracle is not locally accessible.
    Does NOT pretend to be Oracle - explicitly identifies itself as Local CSV Demo Mode.
    """
    
    def __init__(self, mode="corrupted"):
        self.mode = mode
        self.data_dir = CORRUPTED_DATA_DIR if mode == "corrupted" else CLEAN_DATA_DIR

    def is_available(self):
        return (self.data_dir / "students.csv").exists()

    def fetch_table(self, table_name):
        mapping = {
            "STUDENT": "students.csv",
            "COURSE": "courses.csv",
            "ATTENDANCE": "attendance.csv",
            "EXAM_RESULT": "exam_results.csv"
        }
        filename = mapping.get(table_name.upper().strip())
        if not filename:
            raise ValueError(f"Table '{table_name}' is not in local demonstration schema.")
        
        filepath = self.data_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Demonstration data file {filepath} not found. Run mock generator.")
        
        df = pd.read_csv(filepath)
        # Drop internal ground truth markers from display/analytics view if needed, or preserve
        return df

    def fetch_all_tables(self):
        return {
            "STUDENT": self.fetch_table("STUDENT"),
            "COURSE": self.fetch_table("COURSE"),
            "ATTENDANCE": self.fetch_table("ATTENDANCE"),
            "EXAM_RESULT": self.fetch_table("EXAM_RESULT"),
        }

