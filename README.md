# AI-Based Database Data-Quality Analyzer

> **A Hybrid Academic and Enterprise Data-Quality System integrating Oracle SQL/PLSQL Rule-Based Validation with Scikit-Learn Machine Learning Anomaly Detection.**

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-Oracle%2019c%20%7C%2021c%20%7C%20XE-red.svg)](https://www.oracle.com/database/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Machine Learning](https://img.shields.io/badge/ML-Isolation%20Forest%20%7C%20DBSCAN-orange.svg)](https://scikit-learn.org/)
[![Tests](https://img.shields.io/badge/Tests-16%20Passed-green.svg)](https://pytest.org/)

---

## 1. Project Introduction & Problem Statement

Modern enterprise and educational databases store massive volumes of transactional, demographic, and academic performance data. Conventional database management systems rely heavily on declarative constraints (`NOT NULL`, `CHECK`, `PRIMARY KEY`, `FOREIGN KEY`). However, real-world data pipelines face subtle data quality defects:
1. **Rule Violations**: Missing fields, duplicate enrollments, out-of-range numerical metrics, and syntax format errors that bypass relaxed staging tables.
2. **Multivariate Statistical Anomalies**: Records that are individually compliant with all predefined SQL boundary checks, but represent suspicious or contradictory combinations (e.g., a student with 98% class attendance who scores 4% on the exam, or an attendance count that contradicts class records).
3. **Inflexible Static Rules**: Traditional SQL rules cannot adapt to shifting cohort patterns without constant manual rule rewriting.

### The Proposed Solution
The **AI-Based Database Data-Quality Analyzer** provides a **hybrid detection architecture**:
- **Oracle SQL/PLSQL Engine (`PKG_DATA_QUALITY`)**: Directly executes stored procedures inside Oracle to identify missing values, duplicates, domain range breaches, and mathematical inconsistencies.
- **Unsupervised Machine Learning Engine**: Uses **Isolation Forest** (ensemble tree recursive partitioning) and **DBSCAN** (density-based noise isolation) on scaled feature vectors to detect multivariate statistical outliers.
- **Hybrid Result Merger & Severity Classifier**: Combines findings, escalates multi-method corroborated records to `HIGH` severity, eliminates double-counting, explains anomalies using feature z-scores, and generates an auditable **Data Quality Score**.

> **Important Data Governance Principle:** A machine learning anomaly represents a statistical outlier warranting human review—it is never automatically assumed to be an error, nor are flagged records automatically deleted.

---

## 2. System Architecture

```
                          ┌─────────────────────────────────────┐
                          │     College Student Database        │
                          │   STUDENT | COURSE | ATTENDANCE     │
                          │            EXAM_RESULT              │
                          └──────────────────┬──────────────────┘
                                             │
                     ┌───────────────────────┴───────────────────────┐
                     ▼                                               ▼
       ┌───────────────────────────┐                   ┌───────────────────────────┐
       │   Oracle SQL / PLSQL      │                   │   Python Feature Matrix   │
       │     Rule Engine           │                   │   Preprocessing & Scaling │
       │  (PKG_DATA_QUALITY)       │                   │   (StandardScaler + Eng)  │
       └─────────────┬─────────────┘                   └─────────────┬─────────────┘
                     │                                               │
                     │ Audit Findings                                ├──────────────────────────────┐
                     │                                               ▼                              ▼
                     │                                 ┌───────────────────────────┐  ┌───────────────────────────┐
                     │                                 │     Isolation Forest      │  │          DBSCAN           │
                     │                                 │ (Recursive Tree Outliers) │  │   (Density-Based Noise)   │
                     │                                 └─────────────┬─────────────┘  └─────────────┬─────────────┘
                     │                                               │                              │
                     └───────────────────────┬───────────────────────┴──────────────────────────────┘
                                             ▼
                               ┌───────────────────────────┐
                               │   Hybrid Result Merger    │
                               │  & Severity Classifier    │
                               │  (HIGH / MEDIUM / LOW)    │
                               └─────────────┬─────────────┘
                                             ▼
                               ┌───────────────────────────┐
                               │    CONSOLIDATED_ANOMALIES │
                               │  & Transparent Scorer     │
                               └─────────────┬─────────────┘
                                             ▼
                               ┌───────────────────────────┐
                               │    Streamlit Dashboard    │
                               │  6 Interactive Web Pages  │
                               │   + PDF & CSV Exporters   │
                               └───────────────────────────┘
```

---

## 3. Technology Stack

- **Primary Database**: Oracle Database (XE / Enterprise / Cloud Autonomous Database)
- **Database Connectivity**: `python-oracledb` (Thin mode, zero external C-client dependencies)
- **PL/SQL Engine**: Oracle Package `PKG_DATA_QUALITY` writing directly to `AUDIT_LOG`
- **Application Framework**: Python 3.12 + Streamlit
- **Machine Learning**: `scikit-learn` (`IsolationForest`, `DBSCAN`, `StandardScaler`)
- **Data Analysis**: `pandas`, `numpy`
- **Interactive Visualizations**: `plotly` (multidimensional scatters, donuts, bar charts)
- **Report Generation**: `reportlab` (Academic/Enterprise PDF compilation)
- **Testing**: `pytest`

---

## 4. Database Design

The demonstration database models an academic institution across four relational tables:

| Table Name | Primary Key | Foreign Keys | Key Monitored Attributes |
| :--- | :--- | :--- | :--- |
| **`STUDENT`** | `STUDENT_ID` | None | `STUDENT_NAME`, `AGE`, `GENDER`, `DEPARTMENT`, `YEAR_OF_STUDY`, `EMAIL`, `PHONE_NUMBER` |
| **`COURSE`** | `COURSE_ID` | None | `COURSE_NAME`, `DEPARTMENT`, `CREDITS` |
| **`ATTENDANCE`** | `ATTENDANCE_ID`| `STUDENT_ID`, `COURSE_ID` | `ATTENDANCE_PERCENTAGE`, `TOTAL_CLASSES`, `ATTENDED_CLASSES` |
| **`EXAM_RESULT`**| `RESULT_ID` | `STUDENT_ID`, `COURSE_ID` | `MARKS`, `MAX_MARKS`, `EXAM_DATE` |

### Audit & Integration Schema
- **`AUDIT_LOG`**: Captures rule-based findings executed by Oracle SQL/PLSQL (`ISSUE_ID`, `RECORD_ID`, `TABLE_NAME`, `COLUMN_NAME`, `ISSUE_TYPE`, `DESCRIPTION`, `SEVERITY`, `DETECTION_SOURCE`).
- **`CONSOLIDATED_ANOMALIES`**: Captures merged multi-engine findings with feature evidence, explanations, anomaly scores, and escalated severity ratings.

---

## 5. Machine Learning Methodology

1. **Feature Engineering**:
   - `AGE`, `YEAR_OF_STUDY`
   - `ATTENDANCE_PERCENTAGE`
   - `MARKS_PERCENTAGE` = $(MARKS / MAX\_MARKS) \times 100$
   - `ATTENDANCE_CONSISTENCY` = $|Stored\% - (Attended / Total \times 100)|$
   - `ATTENDANCE_VS_MARKS_GAP` = $Attendance\% - Marks\%$
   *(Identifiers such as `STUDENT_ID` and `COURSE_ID` are strictly excluded from the ML feature matrix).*
2. **Explicit Missingness Handling**:
   - Tracks missing values via boolean indicator columns rather than silently dropping or zero-filling.
3. **Isolation Forest (Primary Model)**:
   - Evaluates path lengths in an ensemble of isolation trees.
   - Maps raw decision scores into a normalized anomaly score $S \in [0.0, 1.0]$.
4. **DBSCAN (Secondary Model)**:
   - Evaluates density clusters and isolates points located outside $\epsilon$-neighborhoods as noise records ($label = -1$).
5. **Anomaly Explainer**:
   - Compares the anomalous observation against the cohort mean and standard deviation to explain *why* it was flagged (e.g. *"Attendance vs Marks Gap (+93.0%) is 3.8σ higher than cohort mean"*).

---

## 6. Installation & Execution Instructions

### Prerequisites
- Python 3.10+ (Tested on Python 3.12)
- Oracle Database (Optional for live mode; CSV Demo mode runs standalone)

### Step 1: Clone and Navigate to Directory
```bash
cd "C:\Users\Siddharta Saha\.gemini\antigravity\scratch\database_quality_analyzer"
```

### Step 2: Initialize Virtual Environment
```bash
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run Automated Tests
```bash
python -m pytest tests -v
```

### Step 5: Launch the Streamlit Dashboard
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 7. Oracle Database Setup (For Live Mode)

1. Open Oracle SQL*Plus, SQL Developer, or Oracle Cloud Database Actions as schema user.
2. Execute the DDL scripts in sequence:
   ```sql
   @database/schema.sql;
   @database/audit_tables.sql;
   @database/procedures.sql;
   ```
3. Load the staged test data:
   ```sql
   -- To ingest the controlled corrupted staging dataset:
   @database/corrupted_data.sql;

   -- Or to ingest the clean baseline dataset:
   @database/sample_data.sql;
   ```
4. Copy `.env.example` to `.env` and configure your credentials:
   ```ini
   ORACLE_USER=admin
   ORACLE_PASSWORD=your_secure_password
   ORACLE_HOST=localhost
   ORACLE_PORT=1521
   ORACLE_SERVICE_NAME=XEPDB1
   ```
5. In the Streamlit UI, navigate to **Dataset Management**, verify your credentials using **Test Connection**, and switch to **Live Oracle Database** mode.

---

## 8. Dashboard Pages Overview

- **Page 1: Overview Dashboard**: KPI cards, overall Data Quality Score gauge, issue severity distribution (Plotly donut), detection source breakdown, and dimension compliance bars.
- **Page 2: SQL/PLSQL Analysis**: Individual procedure execution cards (`CHECK_NULL_VALUES`, `CHECK_DUPLICATES`, etc.), live execution button, and interactive audit log filters.
- **Page 3: Machine Learning Analysis**: Interactive slider controls for contamination and DBSCAN eps, attendance vs. exam scatter plot with cluster overlay, anomaly score histogram, and contingency comparison table.
- **Page 4: Suspicious Records**: Searchable and filterable table with full drill-down inspector showing original database attributes and mathematical evidence.
- **Page 5: Dataset Management**: Live Oracle connection tester, table browser, column previewer, and custom CSV uploader.
- **Page 6: Reports**: One-click download of enterprise PDF audit reports and consolidated CSV findings.

---

## 9. Transparent Data Quality Scoring Formula

$$\text{Data Quality Score} = 100 \times \left(1 - \frac{\sum_{i=1}^{N_{\text{issues}}} \text{Weight}(\text{Severity}_i)}{\text{Total Applicable Checks}}\right)$$

Where:
- $\text{Weight}(\text{HIGH}) = 1.0$ (Critical rule violation or cross-engine confirmed anomaly)
- $\text{Weight}(\text{MEDIUM}) = 0.6$ (Statistical multivariate anomaly or count mismatch)
- $\text{Weight}(\text{LOW}) = 0.2$ (Formatting syntax error)
- **Deduplication Safeguard**: If a single record violates multiple checks or is flagged by both SQL and ML engines, it is counted once with its escalated severity weight, strictly preventing artificial score degradation.

---

## 10. Limitations & Future Scope

### Current Limitations
- Supervised classification metrics require synthetic ground-truth labels; purely unsupervised deployments must rely on cross-model consensus.
- Extreme data volumes (multi-million rows) require batch-chunked streaming when running DBSCAN due to $O(N^2)$ memory constraints.

### Future Scope
- **Active Learning**: Incorporate human-in-the-loop validation where domain users approve or reject flagged anomalies, fine-tuning classifier weights over time.
- **Automated Remediation Workflows**: Generate suggested SQL `UPDATE` patches or staging quarantine triggers for human review.
- **Streaming Pipeline Ingestion**: Connect to Apache Kafka or Oracle GoldenGate for real-time transactional data quality auditing.

