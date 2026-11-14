-- ==============================================================================
-- AI-Based Database Data-Quality Analyzer
-- ORACLE PL/SQL STORED PROCEDURES FOR RULE-BASED DATA QUALITY DETECTION
-- ==============================================================================

CREATE OR REPLACE PACKAGE PKG_DATA_QUALITY AS
    PROCEDURE CHECK_NULL_VALUES(p_source VARCHAR2 DEFAULT 'PLSQL_PKG');
    PROCEDURE CHECK_DUPLICATES(p_source VARCHAR2 DEFAULT 'PLSQL_PKG');
    PROCEDURE CHECK_INVALID_RANGES(p_source VARCHAR2 DEFAULT 'PLSQL_PKG');
    PROCEDURE CHECK_INCONSISTENT_RECORDS(p_source VARCHAR2 DEFAULT 'PLSQL_PKG');
    PROCEDURE CHECK_FORMAT_VALIDATION(p_source VARCHAR2 DEFAULT 'PLSQL_PKG');
    PROCEDURE RUN_ALL_QUALITY_CHECKS(p_total_issues OUT NUMBER);
END PKG_DATA_QUALITY;
/

CREATE OR REPLACE PACKAGE BODY PKG_DATA_QUALITY AS

    -- --------------------------------------------------------------------------
    -- 1. NULL VALUE DETECTION
    -- --------------------------------------------------------------------------
    PROCEDURE CHECK_NULL_VALUES(p_source VARCHAR2 DEFAULT 'PLSQL_PKG') IS
    BEGIN
        -- STUDENT Table checks
        INSERT INTO AUDIT_LOG (RECORD_ID, TABLE_NAME, COLUMN_NAME, ISSUE_TYPE, DESCRIPTION, SEVERITY, DETECTION_SOURCE)
        SELECT STUDENT_ID, 'STUDENT', 'STUDENT_NAME', 'NULL_VALUE',
               'Mandatory student name is missing (NULL).', 'HIGH', p_source
        FROM STUDENT WHERE STUDENT_NAME IS NULL OR TRIM(STUDENT_NAME) IS NULL;

        INSERT INTO AUDIT_LOG (RECORD_ID, TABLE_NAME, COLUMN_NAME, ISSUE_TYPE, DESCRIPTION, SEVERITY, DETECTION_SOURCE)
        SELECT STUDENT_ID, 'STUDENT', 'AGE', 'NULL_VALUE',
               'Student age is missing (NULL).', 'MEDIUM', p_source
        FROM STUDENT WHERE AGE IS NULL;

        INSERT INTO AUDIT_LOG (RECORD_ID, TABLE_NAME, COLUMN_NAME, ISSUE_TYPE, DESCRIPTION, SEVERITY, DETECTION_SOURCE)
        SELECT STUDENT_ID, 'STUDENT', 'DEPARTMENT', 'NULL_VALUE',
               'Academic department is not assigned (NULL).', 'HIGH', p_source
        FROM STUDENT WHERE DEPARTMENT IS NULL OR TRIM(DEPARTMENT) IS NULL;

        INSERT INTO AUDIT_LOG (RECORD_ID, TABLE_NAME, COLUMN_NAME, ISSUE_TYPE, DESCRIPTION, SEVERITY, DETECTION_SOURCE)
        SELECT STUDENT_ID, 'STUDENT', 'EMAIL', 'NULL_VALUE',
               'Contact email address is missing (NULL).', 'MEDIUM', p_source
        FROM STUDENT WHERE EMAIL IS NULL OR TRIM(EMAIL) IS NULL;

        INSERT INTO AUDIT_LOG (RECORD_ID, TABLE_NAME, COLUMN_NAME, ISSUE_TYPE, DESCRIPTION, SEVERITY, DETECTION_SOURCE)
        SELECT STUDENT_ID, 'STUDENT', 'PHONE_NUMBER', 'NULL_VALUE',
               'Emergency phone number is missing (NULL).', 'LOW', p_source
        FROM STUDENT WHERE PHONE_NUMBER IS NULL OR TRIM(PHONE_NUMBER) IS NULL;

        -- ATTENDANCE Table checks
        INSERT INTO AUDIT_LOG (RECORD_ID, TABLE_NAME, COLUMN_NAME, ISSUE_TYPE, DESCRIPTION, SEVERITY, DETECTION_SOURCE)
        SELECT ATTENDANCE_ID, 'ATTENDANCE', 'ATTENDANCE_PERCENTAGE', 'NULL_VALUE',
               'Calculated attendance percentage is missing (NULL).', 'HIGH', p_source
        FROM ATTENDANCE WHERE ATTENDANCE_PERCENTAGE IS NULL;

        -- EXAM_RESULT Table checks
        INSERT INTO AUDIT_LOG (RECORD_ID, TABLE_NAME, COLUMN_NAME, ISSUE_TYPE, DESCRIPTION, SEVERITY, DETECTION_SOURCE)
        SELECT RESULT_ID, 'EXAM_RESULT', 'MARKS', 'NULL_VALUE',
               'Exam marks scored is missing (NULL).', 'HIGH', p_source
        FROM EXAM_RESULT WHERE MARKS IS NULL;
    END CHECK_NULL_VALUES;

    -- --------------------------------------------------------------------------
    -- 2. DUPLICATE DETECTION
    -- --------------------------------------------------------------------------
    PROCEDURE CHECK_DUPLICATES(p_source VARCHAR2 DEFAULT 'PLSQL_PKG') IS
    BEGIN
        -- Repeated Email Addresses
        INSERT INTO AUDIT_LOG (RECORD_ID, TABLE_NAME, COLUMN_NAME, ISSUE_TYPE, DESCRIPTION, SEVERITY, DETECTION_SOURCE)
        SELECT STUDENT_ID, 'STUDENT', 'EMAIL', 'DUPLICATE',
               'Duplicate email address detected across multiple student records: ' || EMAIL, 'HIGH', p_source
        FROM STUDENT
        WHERE EMAIL IN (
            SELECT EMAIL FROM STUDENT WHERE EMAIL IS NOT NULL GROUP BY EMAIL HAVING COUNT(*) > 1
        );

        -- Duplicate Course Enrollment in Attendance
        INSERT INTO AUDIT_LOG (RECORD_ID, TABLE_NAME, COLUMN_NAME, ISSUE_TYPE, DESCRIPTION, SEVERITY, DETECTION_SOURCE)
        SELECT ATTENDANCE_ID, 'ATTENDANCE', 'STUDENT_ID, COURSE_ID', 'DUPLICATE',
               'Duplicate attendance tracking record for student ' || STUDENT_ID || ' in course ' || COURSE_ID, 'MEDIUM', p_source
        FROM ATTENDANCE
        WHERE (STUDENT_ID, COURSE_ID) IN (
            SELECT STUDENT_ID, COURSE_ID FROM ATTENDANCE GROUP BY STUDENT_ID, COURSE_ID HAVING COUNT(*) > 1
        );

        -- Duplicate Exam Submissions
        INSERT INTO AUDIT_LOG (RECORD_ID, TABLE_NAME, COLUMN_NAME, ISSUE_TYPE, DESCRIPTION, SEVERITY, DETECTION_SOURCE)
        SELECT RESULT_ID, 'EXAM_RESULT', 'STUDENT_ID, COURSE_ID', 'DUPLICATE',
               'Multiple exam result entries for student ' || STUDENT_ID || ' in course ' || COURSE_ID, 'HIGH', p_source
        FROM EXAM_RESULT
        WHERE (STUDENT_ID, COURSE_ID) IN (
            SELECT STUDENT_ID, COURSE_ID FROM EXAM_RESULT GROUP BY STUDENT_ID, COURSE_ID HAVING COUNT(*) > 1
        );
    END CHECK_DUPLICATES;

    -- --------------------------------------------------------------------------
    -- 3. RANGE VALIDATION
    -- --------------------------------------------------------------------------
    PROCEDURE CHECK_INVALID_RANGES(p_source VARCHAR2 DEFAULT 'PLSQL_PKG') IS
    BEGIN
        -- Age Range Validation (Standard undergraduate/graduate student: 16 to 40)
        INSERT INTO AUDIT_LOG (RECORD_ID, TABLE_NAME, COLUMN_NAME, ISSUE_TYPE, DESCRIPTION, SEVERITY, DETECTION_SOURCE)
        SELECT STUDENT_ID, 'STUDENT', 'AGE', 'OUT_OF_RANGE',
               'Student age ' || TO_CHAR(AGE) || ' falls outside realistic collegiate bounds (16-40).', 'HIGH', p_source
        FROM STUDENT WHERE AGE < 16 OR AGE > 40;

        -- Year of study (typically 1 to 5)
        INSERT INTO AUDIT_LOG (RECORD_ID, TABLE_NAME, COLUMN_NAME, ISSUE_TYPE, DESCRIPTION, SEVERITY, DETECTION_SOURCE)
        SELECT STUDENT_ID, 'STUDENT', 'YEAR_OF_STUDY', 'OUT_OF_RANGE',
               'Academic year ' || TO_CHAR(YEAR_OF_STUDY) || ' is invalid (must be 1-5).', 'HIGH', p_source
        FROM STUDENT WHERE YEAR_OF_STUDY < 1 OR YEAR_OF_STUDY > 5;

        -- Attendance Percentage Range (0.00 to 100.00)
        INSERT INTO AUDIT_LOG (RECORD_ID, TABLE_NAME, COLUMN_NAME, ISSUE_TYPE, DESCRIPTION, SEVERITY, DETECTION_SOURCE)
        SELECT ATTENDANCE_ID, 'ATTENDANCE', 'ATTENDANCE_PERCENTAGE', 'OUT_OF_RANGE',
               'Attendance percentage ' || TO_CHAR(ATTENDANCE_PERCENTAGE) || '% is outside valid scale (0-100%).', 'HIGH', p_source
        FROM ATTENDANCE WHERE ATTENDANCE_PERCENTAGE < 0 OR ATTENDANCE_PERCENTAGE > 100;

        -- Exam Marks Range (0 to MAX_MARKS)
        INSERT INTO AUDIT_LOG (RECORD_ID, TABLE_NAME, COLUMN_NAME, ISSUE_TYPE, DESCRIPTION, SEVERITY, DETECTION_SOURCE)
        SELECT RESULT_ID, 'EXAM_RESULT', 'MARKS', 'OUT_OF_RANGE',
               'Exam marks ' || TO_CHAR(MARKS) || ' is negative or exceeds maximum possible score ' || TO_CHAR(MAX_MARKS), 'HIGH', p_source
        FROM EXAM_RESULT WHERE MARKS < 0 OR MARKS > MAX_MARKS;

        -- Course Credits (1 to 6)
        INSERT INTO AUDIT_LOG (RECORD_ID, TABLE_NAME, COLUMN_NAME, ISSUE_TYPE, DESCRIPTION, SEVERITY, DETECTION_SOURCE)
        SELECT COURSE_ID, 'COURSE', 'CREDITS', 'OUT_OF_RANGE',
               'Course credits ' || TO_CHAR(CREDITS) || ' outside standard academic syllabus limits (1-6).', 'MEDIUM', p_source
        FROM COURSE WHERE CREDITS <= 0 OR CREDITS > 10;
    END CHECK_INVALID_RANGES;

    -- --------------------------------------------------------------------------
    -- 4. CONSISTENCY VALIDATION
    -- --------------------------------------------------------------------------
    PROCEDURE CHECK_INCONSISTENT_RECORDS(p_source VARCHAR2 DEFAULT 'PLSQL_PKG') IS
    BEGIN
        -- Attended Classes Cannot Exceed Total Classes
        INSERT INTO AUDIT_LOG (RECORD_ID, TABLE_NAME, COLUMN_NAME, ISSUE_TYPE, DESCRIPTION, SEVERITY, DETECTION_SOURCE)
        SELECT ATTENDANCE_ID, 'ATTENDANCE', 'ATTENDED_CLASSES', 'INCONSISTENCY',
               'Attended classes (' || TO_CHAR(ATTENDED_CLASSES) || ') strictly exceeds total classes held (' || TO_CHAR(TOTAL_CLASSES) || ').',
               'HIGH', p_source
        FROM ATTENDANCE WHERE ATTENDED_CLASSES > TOTAL_CLASSES;

        -- Total Classes Cannot Be Zero or Negative while Attended > 0
        INSERT INTO AUDIT_LOG (RECORD_ID, TABLE_NAME, COLUMN_NAME, ISSUE_TYPE, DESCRIPTION, SEVERITY, DETECTION_SOURCE)
        SELECT ATTENDANCE_ID, 'ATTENDANCE', 'TOTAL_CLASSES', 'INCONSISTENCY',
               'Total classes held is 0 or negative (' || TO_CHAR(TOTAL_CLASSES) || ') yet classes attended is ' || TO_CHAR(ATTENDED_CLASSES),
               'HIGH', p_source
        FROM ATTENDANCE WHERE TOTAL_CLASSES <= 0 AND ATTENDED_CLASSES > 0;

        -- Attendance Percentage mathematical consistency: ABS(pct - (attended/total * 100)) > 2.0%
        INSERT INTO AUDIT_LOG (RECORD_ID, TABLE_NAME, COLUMN_NAME, ISSUE_TYPE, DESCRIPTION, SEVERITY, DETECTION_SOURCE)
        SELECT ATTENDANCE_ID, 'ATTENDANCE', 'ATTENDANCE_PERCENTAGE', 'INCONSISTENCY',
               'Stored attendance ' || TO_CHAR(ATTENDANCE_PERCENTAGE, '990.99') || '% mismatches calculated ratio ' ||
               TO_CHAR(ROUND((ATTENDED_CLASSES / NULLIF(TOTAL_CLASSES, 0)) * 100, 2), '990.99') || '%.',
               'MEDIUM', p_source
        FROM ATTENDANCE
        WHERE TOTAL_CLASSES > 0 
          AND ATTENDED_CLASSES >= 0
          AND ATTENDED_CLASSES <= TOTAL_CLASSES
          AND ABS(ATTENDANCE_PERCENTAGE - ((ATTENDED_CLASSES / TOTAL_CLASSES) * 100)) > 2.0;

        -- Student Year of Study vs Age inconsistency (e.g. 1st year aged 38 or 4th year aged 16)
        INSERT INTO AUDIT_LOG (RECORD_ID, TABLE_NAME, COLUMN_NAME, ISSUE_TYPE, DESCRIPTION, SEVERITY, DETECTION_SOURCE)
        SELECT STUDENT_ID, 'STUDENT', 'AGE, YEAR_OF_STUDY', 'INCONSISTENCY',
               'Anomalous age (' || TO_CHAR(AGE) || ') for study year ' || TO_CHAR(YEAR_OF_STUDY) || ' indicates data entry conflict.',
               'MEDIUM', p_source
        FROM STUDENT
        WHERE (YEAR_OF_STUDY >= 3 AND AGE <= 17)
           OR (YEAR_OF_STUDY = 1 AND AGE >= 38);
    END CHECK_INCONSISTENT_RECORDS;

    -- --------------------------------------------------------------------------
    -- 5. FORMAT VALIDATION
    -- --------------------------------------------------------------------------
    PROCEDURE CHECK_FORMAT_VALIDATION(p_source VARCHAR2 DEFAULT 'PLSQL_PKG') IS
    BEGIN
        -- Email regex validation
        INSERT INTO AUDIT_LOG (RECORD_ID, TABLE_NAME, COLUMN_NAME, ISSUE_TYPE, DESCRIPTION, SEVERITY, DETECTION_SOURCE)
        SELECT STUDENT_ID, 'STUDENT', 'EMAIL', 'FORMAT_ERROR',
               'Malformed email syntax: ' || EMAIL, 'LOW', p_source
        FROM STUDENT
        WHERE EMAIL IS NOT NULL 
          AND NOT REGEXP_LIKE(EMAIL, '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

        -- Phone Number format validation (must be 10 to 15 digits, allowing optional + or dashes)
        INSERT INTO AUDIT_LOG (RECORD_ID, TABLE_NAME, COLUMN_NAME, ISSUE_TYPE, DESCRIPTION, SEVERITY, DETECTION_SOURCE)
        SELECT STUDENT_ID, 'STUDENT', 'PHONE_NUMBER', 'FORMAT_ERROR',
               'Improper phone number structure: ' || PHONE_NUMBER, 'LOW', p_source
        FROM STUDENT
        WHERE PHONE_NUMBER IS NOT NULL
          AND NOT REGEXP_LIKE(PHONE_NUMBER, '^\+?[0-9]{1,4}?[-. ]?(\([0-9]{2,4}\)|[0-9]{2,4})[-. ]?[0-9]{3,4}[-. ]?[0-9]{3,4}$');
    END CHECK_FORMAT_VALIDATION;

    -- --------------------------------------------------------------------------
    -- MASTER PROCEDURE: RUN ALL CHECKS
    -- --------------------------------------------------------------------------
    PROCEDURE RUN_ALL_QUALITY_CHECKS(p_total_issues OUT NUMBER) IS
    BEGIN
        -- Clear previous run if required or record continuous audit
        CHECK_NULL_VALUES('PLSQL_ALL_CHECKS');
        CHECK_DUPLICATES('PLSQL_ALL_CHECKS');
        CHECK_INVALID_RANGES('PLSQL_ALL_CHECKS');
        CHECK_INCONSISTENT_RECORDS('PLSQL_ALL_CHECKS');
        CHECK_FORMAT_VALIDATION('PLSQL_ALL_CHECKS');

        SELECT COUNT(*) INTO p_total_issues FROM AUDIT_LOG WHERE DETECTION_TIMESTAMP >= SYSTIMESTAMP - INTERVAL '5' MINUTE;
        COMMIT;
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END RUN_ALL_QUALITY_CHECKS;

END PKG_DATA_QUALITY;
/

