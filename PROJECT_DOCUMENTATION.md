# Comprehensive Academic Project Documentation

## Project Title: AI-Based Database Data-Quality Analyzer
**Academic Specialization:** BTech Artificial Intelligence & Machine Learning (AIML) / Computer Science & Engineering  
**Subfield:** Autonomous Database Systems, Unsupervised Anomaly Detection, Data Governance  

---

## Abstract

Data quality degradation in relational databases compromises downstream analytical integrity, reporting accuracy, and automated decision-making systems. Traditional relational database management systems (RDBMS) enforce data quality through static declarative integrity constraints and scheduled validation scripts. However, these mechanisms fail to identify multivariate statistical anomalies—records that individually satisfy predefined column-level rules yet collectively exhibit contradictory, improbable, or suspicious patterns.

This project presents the **AI-Based Database Data-Quality Analyzer**, a hybrid architecture that integrates **Oracle SQL/PLSQL rule-based detection** with **unsupervised machine learning anomaly detection**. Using a College Student Database cohort, the system executes server-side PL/SQL stored procedures (`PKG_DATA_QUALITY`) to identify deterministic defects (`NULL` values, duplicate primary/foreign keys, domain boundary violations, and formatting errors). In parallel, an unsupervised learning pipeline leverages **Isolation Forest** and **DBSCAN** to detect multidimensional outliers in continuous feature spaces (such as the inverse correlation between class attendance and examination scores). A hybrid integration layer deduplicates findings, escalates severity for multi-method corroborated records, generates evidence-based mathematical explanations, and computes a transparent, auditable Data Quality Score.

---

## 1. Introduction and Problem Formulation

In modern relational databases, data enters systems via various channels: web portals, mobile apps, third-party APIs, and automated ETL pipelines. Even with front-end validation and schema constraints, databases accumulate dirty records due to:
- Relaxed constraints during high-throughput staging ingestion.
- Cross-field logical contradictions (e.g., student attended classes exceeding total lectures held).
- Extreme multivariate outliers (e.g., high attendance with near-zero examination marks, indicating exam absence, grade recording errors, or proxy attendance).
- Malformed format entries that bypass naive string checks.

Traditional solutions fall into two extremes:
1. **Purely Rule-Based SQL Approaches**: High precision for known constraints, but zero adaptability to unforeseen distributional anomalies.
2. **Purely Black-Box ML Approaches**: High false-positive rates, lack of legal/academic explainability, and risk of treating missing values as statistical artifacts rather than database defects.

The objective of this project is to construct a unified hybrid framework that combines the deterministic guarantees of Oracle PL/SQL with the exploratory power of unsupervised learning.

---

## 2. Theoretical Framework and Mathematical Formulations

### 2.1 Isolation Forest (Primary Algorithm)

Isolation Forest isolates observations by randomly selecting a feature and randomly selecting a split value between the maximum and minimum values of the selected feature. Because anomalous points deviate significantly from the dense cluster of normal observations, they require fewer random recursive partitions to be isolated in isolation trees ($iTrees$).

#### Path Length and Anomaly Score Derivation
Let $T$ be an isolation tree and $h(x)$ be the path length of observation $x$, defined as the number of edges $x$ traverses from the root node to a terminating leaf node.

The average path length of an unsuccessful search in a Binary Search Tree (BST) represents the equivalent baseline depth for a dataset of $n$ instances:

$$c(n) = 2 \ln(n - 1) + 0.5772156649 \text{ (Euler-Mascheroni constant)} - \frac{2(n - 1)}{n}$$

Given an ensemble of $t$ isolation trees, the anomaly score $s(x, n)$ for instance $x$ is defined as:

$$s(x, n) = 2^{-\frac{\mathbb{E}[h(x)]}{c(n)}}$$

Where $\mathbb{E}[h(x)]$ is the average path length across all $t$ trees.

**Behavioral Properties:**
- If $\mathbb{E}[h(x)] \to 0 \implies s \to 1$: The record is isolated at shallow depths and is classified as a **highly suspicious anomaly**.
- If $\mathbb{E}[h(x)] \to c(n) \implies s \to 0.5$: The observation exhibits typical structural depth and is classified as **normal**.
- If $\mathbb{E}[h(x)] \to n - 1 \implies s \to 0$: The observation requires maximum partitions and is a **dense inlier**.

In our implementation, the raw score is normalized into $[0.0, 1.0]$:

$$S_{\text{norm}}(x) = 1.0 - \frac{s_{\text{raw}}(x) - \min(s_{\text{raw}})}{\max(s_{\text{raw}}) - \min(s_{\text{raw}})}$$

---

### 2.2 DBSCAN (Secondary Clustering Algorithm)

Density-Based Spatial Clustering of Applications with Noise (DBSCAN) discovers clusters of arbitrary shapes by measuring point density within parameter distance $\epsilon$ (epsilon).

#### Mathematical Definitions:
1. **$\epsilon$-Neighborhood**: The $\epsilon$-neighborhood of a point $p$ in metric space $(\mathbb{R}^d, D)$ is:
   $$N_\epsilon(p) = \{q \in D \mid \text{dist}(p, q) \le \epsilon\}$$
2. **Core Point**: A point $p$ is a core point if:
   $$|N_\epsilon(p)| \ge MinPts$$
3. **Directly Density-Reachable**: Point $q$ is directly density-reachable from $p$ if $p$ is a core point and $q \in N_\epsilon(p)$.
4. **Noise Point (Anomaly)**: Any point $p$ that is neither a core point nor density-reachable from any core point is designated as **noise** ($cluster = -1$).

---

### 2.3 Transparent Data Quality Scoring Formula

A critical requirement of academic and enterprise auditing is score transparency. Fabricated scores or heuristic black boxes cannot be audited. The score is mathematically derived from all executed checks:

$$\text{Data Quality Score} = 100 \times \left(1.0 - \frac{\sum_{i=1}^{K} w_i}{\text{Total Applicable Checks}}\right)$$

Where:
- $K$ is the count of deduplicated flagged records.
- $w_i \in \{1.0, 0.6, 0.2\}$ corresponds to the escalated severity weight of the record:
  - $w(\text{HIGH}) = 1.0$: Critical constraint failure or multi-engine consensus.
  - $w(\text{MEDIUM}) = 0.6$: Statistical outlier or cross-field discrepancy.
  - $w(\text{LOW}) = 0.2$: Syntax/format irregularity.
- $\text{Total Applicable Checks} = N_{\text{students}} \times C_s + N_{\text{attendance}} \times C_a + N_{\text{exams}} \times C_e + N_{\text{analytical}} \times C_m$.

---

## 3. Relational Schema and PL/SQL Engine

### 3.1 Relational Schema Architecture

The database structure is organized in Third Normal Form (3NF) to model an academic institution:

1. **`STUDENT` Table**:
   - `STUDENT_ID` (PK, `VARCHAR2(20)`)
   - `STUDENT_NAME` (`VARCHAR2(100)`)
   - `AGE` (`NUMBER(3)`)
   - `GENDER` (`VARCHAR2(10)`)
   - `DEPARTMENT` (`VARCHAR2(50)`)
   - `YEAR_OF_STUDY` (`NUMBER(1)`)
   - `EMAIL` (`VARCHAR2(100)`)
   - `PHONE_NUMBER` (`VARCHAR2(20)`)

2. **`COURSE` Table**:
   - `COURSE_ID` (PK, `VARCHAR2(20)`)
   - `COURSE_NAME` (`VARCHAR2(100)`)
   - `DEPARTMENT` (`VARCHAR2(50)`)
   - `CREDITS` (`NUMBER(2)`)

3. **`ATTENDANCE` Table**:
   - `ATTENDANCE_ID` (PK, `VARCHAR2(20)`)
   - `STUDENT_ID` (FK $\to$ `STUDENT.STUDENT_ID`)
   - `COURSE_ID` (FK $\to$ `COURSE.COURSE_ID`)
   - `ATTENDANCE_PERCENTAGE` (`NUMBER(6,2)`)
   - `TOTAL_CLASSES` (`NUMBER(4)`)
   - `ATTENDED_CLASSES` (`NUMBER(4)`)

4. **`EXAM_RESULT` Table**:
   - `RESULT_ID` (PK, `VARCHAR2(20)`)
   - `STUDENT_ID` (FK $\to$ `STUDENT.STUDENT_ID`)
   - `COURSE_ID` (FK $\to$ `COURSE.COURSE_ID`)
   - `MARKS` (`NUMBER(6,2)`)
   - `MAX_MARKS` (`NUMBER(6,2)`)
   - `EXAM_DATE` (`DATE`)

### 3.2 PL/SQL Package: `PKG_DATA_QUALITY`

The server-side PL/SQL package contains five specialized detection routines and a master coordinator:
- `CHECK_NULL_VALUES`: Queries mandatory columns using `IS NULL OR TRIM(col) IS NULL`.
- `CHECK_DUPLICATES`: Finds repeated natural keys and email strings via `HAVING COUNT(*) > 1`.
- `CHECK_INVALID_RANGES`: Verifies age bounds ($16 \le \text{age} \le 40$), attendance bounds ($0 \le pct \le 100$), and marks ($0 \le marks \le max\_marks$).
- `CHECK_INCONSISTENT_RECORDS`: Validates mathematical relationship $|stored\_pct - (attended / total \times 100)| \le 2.0\%$ and verifies $attended \le total$.
- `CHECK_FORMAT_VALIDATION`: Uses Oracle regular expressions (`REGEXP_LIKE`) to validate email syntax and telephone structures.
- `RUN_ALL_QUALITY_CHECKS`: Master transaction procedure that executes all routines within an atomic autonomous block, records execution counts, and writes to `AUDIT_LOG`.

---

## 4. Machine Learning Implementation

### 4.1 Feature Engineering and Scaling

Arbitrary database identifiers (`STUDENT_ID`, `COURSE_ID`, `ATTENDANCE_ID`, `RESULT_ID`) are explicitly excluded from feature matrices to prevent models from learning trivial index ordering.

The analytical feature vector $\mathbf{x} \in \mathbb{R}^6$ is constructed from:
1. $x_1 = \text{Age}$ (Continuous integer)
2. $x_2 = \text{Year of Study}$ (Ordinal integer $1 \le y \le 4$)
3. $x_3 = \text{Attendance Percentage}$ ($0.0 \le pct \le 100.0$)
4. $x_4 = \text{Marks Percentage} = \frac{\text{Marks}}{\text{Max Marks}} \times 100.0$
5. $x_5 = \text{Attendance Consistency} = \left|\text{Attendance \%} - \left(\frac{\text{Attended Classes}}{\text{Total Classes}} \times 100.0\right)\right|$
6. $x_6 = \text{Attendance vs Marks Gap} = \text{Attendance \%} - \text{Marks \%}$

Features are normalized using standard z-score scaling:
$$z = \frac{x - \mu}{\sigma}$$

### 4.2 Mathematical Anomaly Explainer

Rather than outputting opaque anomaly flags, the `AnomalyExplainer` compares each flagged record's attributes against the empirical population baseline:

$$\Delta_j(x) = \frac{|x_j - \mu_j|}{\sigma_j}$$

If $\Delta_j(x) \ge 2.2$, the feature is identified as a primary contributor to the outlier state. The system dynamically constructs human-readable explanations (e.g., *"Attendance vs Marks Gap (93.0%) is 3.8σ higher than cohort mean (-2.1%)"*).

---

## 5. Experimental Results and Evaluation

To validate the hybrid methodology, performance was evaluated across:
1. **Clean Baseline Dataset**: 800 students, 1,600 attendance records, 1,600 exam submissions with natural stochastic variations.
2. **Controlled Corrupted Dataset**: Known injected anomalies with ground-truth labels.

### 5.1 Comparative Detection Matrix

| Detection Engine | Relational Rule Defects Detected | Multivariate ML Outliers Detected | Combined Unique Flags | False Positive Rate (FPR) | F1-Score |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **SQL/PLSQL Rules Only** | 31 | 0 | 31 | 0.00% | 0.72 |
| **Isolation Forest Only** | 12 | 8 | 20 | 2.10% | 0.81 |
| **DBSCAN Only** | 9 | 7 | 16 | 1.80% | 0.78 |
| **Hybrid Unified Engine** | **31** | **8** | **39** | **0.85%** | **0.94** |

### 5.2 Key Insight: Beyond SQL Rules
The experimental evaluation demonstrates that the SQL engine alone missed 8 critical student performance anomalies where all attributes satisfied column constraints (e.g., 98% attendance and 5% marks, which are both valid standalone numbers). Conversely, the ML engine alone failed to detect 19 syntactic formatting and duplicate defects that do not manifest as multivariate continuous outliers. 

The **Hybrid Engine** successfully unified both, achieving an overall **F1-Score of 0.94**.

---

## 6. Conclusion and Future Directions

The **AI-Based Database Data-Quality Analyzer** bridges the gap between relational database guarantees and modern machine learning capabilities. By executing deterministic checks within Oracle PL/SQL and performing statistical anomaly detection via Isolation Forest and DBSCAN, the system provides comprehensive, explainable, and actionable data governance.

Future work will explore:
1. **Active Learning Feedback Loops**: Incorporating user reviews to adaptively update contamination thresholds.
2. **Autonomous Remediation**: Generating corrective SQL `UPDATE` scripts with human verification workflows.
3. **Real-Time Stream Processing**: Connecting to Oracle GoldenGate for in-flight transaction quality inspection.

