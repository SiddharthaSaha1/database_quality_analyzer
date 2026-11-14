"""
Mock Data Generator for College Student Database
Generates:
1. Clean baseline dataset (~800 records).
2. Controlled corrupted dataset containing known injected anomalies (both SQL violations & ML anomalies).
3. Produces SQL INSERT scripts and companion CSVs with ground-truth labels for evaluation.
"""

import os
import random
import csv
from datetime import datetime, timedelta

# Set seed for reproducible synthetic data generation
random.seed(42)

DEPARTMENTS = ["Computer Science", "Information Technology", "Electrical Eng", "Mechanical Eng", "Data Science"]
COURSES_DATA = [
    ("CS101", "Introduction to Programming", "Computer Science", 4),
    ("CS201", "Data Structures & Algorithms", "Computer Science", 4),
    ("DS301", "Machine Learning Fundamentals", "Data Science", 3),
    ("DS302", "Big Data Analytics", "Data Science", 3),
    ("IT205", "Database Management Systems", "Information Technology", 4),
    ("IT301", "Web Technologies & Cloud", "Information Technology", 3),
    ("EE101", "Circuit Analysis", "Electrical Eng", 4),
    ("EE202", "Digital Signal Processing", "Electrical Eng", 3),
    ("ME101", "Engineering Mechanics", "Mechanical Eng", 4),
    ("ME203", "Thermodynamics", "Mechanical Eng", 3)
]

FIRST_NAMES = [
    "Aarav", "Aditi", "Rohan", "Ananya", "Rahul", "Priya", "Vikram", "Sneha", "Karan", "Pooja",
    "Arjun", "Diya", "Siddharth", "Ishita", "Amit", "Neha", "Manish", "Divya", "Suresh", "Ritu",
    "Varun", "Tanvi", "Naveen", "Swati", "Gaurav", "Meera", "Rajesh", "Kavita", "Sanjay", "Anjali",
    "Deepak", "Shweta", "Alok", "Simran", "Sunil", "Preeti", "Harsh", "Komal", "Mayank", "Nidhi"
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Malhotra", "Mehta", "Patel", "Reddy", "Nair", "Iyer", "Chakraborty",
    "Banerjee", "Singh", "Kumar", "Bhatia", "Joshi", "Saxena", "Deshmukh", "Choudhury", "Menon", "Kapoor"
]

def generate_datasets(num_students=800, output_dir=None):
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))
    
    clean_dir = os.path.join(output_dir, "..", "data", "clean")
    corrupt_dir = os.path.join(output_dir, "..", "data", "corrupted")
    os.makedirs(clean_dir, exist_ok=True)
    os.makedirs(corrupt_dir, exist_ok=True)

    # -------------------------------------------------------------
    # 1. GENERATE CLEAN BASELINE DATASET
    # -------------------------------------------------------------
    clean_students = []
    clean_attendance = []
    clean_exam_results = []

    used_emails = set()
    used_phones = set()

    att_id_counter = 1
    res_id_counter = 1

    for i in range(1, num_students + 1):
        s_id = f"STU{1000 + i}"
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        gender = random.choice(["Male", "Female"])
        year = random.choices([1, 2, 3, 4], weights=[0.28, 0.26, 0.24, 0.22])[0]
        # Realistic age linked to year of study
        base_age = 18 + year
        age = random.choice([base_age - 1, base_age, base_age + 1])
        dept = random.choice(DEPARTMENTS)
        
        email_prefix = f"{first.lower()}.{last.lower()}{random.randint(10, 999)}"
        email = f"{email_prefix}@university.edu"
        while email in used_emails:
            email = f"{first.lower()}.{last.lower()}{random.randint(1000, 9999)}@university.edu"
        used_emails.add(email)

        phone = f"+91-{random.randint(7000000000, 9999999999)}"
        used_phones.add(phone)

        clean_students.append({
            "STUDENT_ID": s_id,
            "STUDENT_NAME": name,
            "AGE": age,
            "GENDER": gender,
            "DEPARTMENT": dept,
            "YEAR_OF_STUDY": year,
            "EMAIL": email,
            "PHONE_NUMBER": phone,
            "IS_ANOMALOUS": 0,
            "ANOMALY_REASON": "CLEAN"
        })

        # Enroll in 2 courses matching department or open elective
        dept_courses = [c for c in COURSES_DATA if c[2] == dept or c[2] in ["Computer Science", "Data Science"]]
        assigned_courses = random.sample(dept_courses, k=min(2, len(dept_courses)))

        for c in assigned_courses:
            c_id = c[0]
            # Clean Attendance
            total_classes = random.randint(40, 60)
            # Typically 65% - 95% attendance
            att_ratio = round(random.uniform(0.65, 0.98), 2)
            attended = int(round(total_classes * att_ratio))
            att_pct = round((attended / total_classes) * 100, 2)

            clean_attendance.append({
                "ATTENDANCE_ID": f"ATT{10000 + att_id_counter}",
                "STUDENT_ID": s_id,
                "COURSE_ID": c_id,
                "ATTENDANCE_PERCENTAGE": att_pct,
                "TOTAL_CLASSES": total_classes,
                "ATTENDED_CLASSES": attended,
                "IS_ANOMALOUS": 0,
                "ANOMALY_REASON": "CLEAN"
            })
            att_id_counter += 1

            # Clean Exam Result (Marks correlate positively with attendance in clean baseline)
            max_marks = 100
            # score centered around attendance percentage with some gaussian noise
            expected_score = 35 + (att_ratio * 55) + random.gauss(0, 5)
            marks = round(max(30.0, min(99.0, expected_score)), 2)
            exam_date = (datetime(2026, 4, 15) + timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")

            clean_exam_results.append({
                "RESULT_ID": f"RES{10000 + res_id_counter}",
                "STUDENT_ID": s_id,
                "COURSE_ID": c_id,
                "MARKS": marks,
                "MAX_MARKS": max_marks,
                "EXAM_DATE": exam_date,
                "IS_ANOMALOUS": 0,
                "ANOMALY_REASON": "CLEAN"
            })
            res_id_counter += 1

    # -------------------------------------------------------------
    # 2. GENERATE CONTROLLED CORRUPTED DATASET
    # -------------------------------------------------------------
    corrupt_students = [dict(s) for s in clean_students]
    corrupt_attendance = [dict(a) for a in clean_attendance]
    corrupt_exam_results = [dict(r) for r in clean_exam_results]

    # Injections tracking
    injected_count = 0

    # 2.1 NULL / MISSING VALUES
    # Student name NULL
    for idx in [15, 42, 105]:
        corrupt_students[idx]["STUDENT_NAME"] = None
        corrupt_students[idx]["IS_ANOMALOUS"] = 1
        corrupt_students[idx]["ANOMALY_REASON"] = "NULL_STUDENT_NAME"
        injected_count += 1
    # Student Age NULL
    for idx in [28, 88]:
        corrupt_students[idx]["AGE"] = None
        corrupt_students[idx]["IS_ANOMALOUS"] = 1
        corrupt_students[idx]["ANOMALY_REASON"] = "NULL_AGE"
        injected_count += 1
    # Student Email NULL
    for idx in [50, 160]:
        corrupt_students[idx]["EMAIL"] = None
        corrupt_students[idx]["IS_ANOMALOUS"] = 1
        corrupt_students[idx]["ANOMALY_REASON"] = "NULL_EMAIL"
        injected_count += 1
    # Attendance Percentage NULL
    for idx in [20, 75]:
        corrupt_attendance[idx]["ATTENDANCE_PERCENTAGE"] = None
        corrupt_attendance[idx]["IS_ANOMALOUS"] = 1
        corrupt_attendance[idx]["ANOMALY_REASON"] = "NULL_ATTENDANCE_PCT"
        injected_count += 1
    # Exam Marks NULL
    for idx in [35, 90]:
        corrupt_exam_results[idx]["MARKS"] = None
        corrupt_exam_results[idx]["IS_ANOMALOUS"] = 1
        corrupt_exam_results[idx]["ANOMALY_REASON"] = "NULL_MARKS"
        injected_count += 1

    # 2.2 DUPLICATE RECORDS
    # Duplicate email addresses
    corrupt_students[12]["EMAIL"] = corrupt_students[11]["EMAIL"]
    corrupt_students[12]["IS_ANOMALOUS"] = 1
    corrupt_students[12]["ANOMALY_REASON"] = "DUPLICATE_EMAIL"
    corrupt_students[11]["IS_ANOMALOUS"] = 1
    corrupt_students[11]["ANOMALY_REASON"] = "DUPLICATE_EMAIL"

    corrupt_students[65]["EMAIL"] = corrupt_students[64]["EMAIL"]
    corrupt_students[65]["IS_ANOMALOUS"] = 1
    corrupt_students[65]["ANOMALY_REASON"] = "DUPLICATE_EMAIL"
    corrupt_students[64]["IS_ANOMALOUS"] = 1
    corrupt_students[64]["ANOMALY_REASON"] = "DUPLICATE_EMAIL"

    # Duplicate attendance record (same student and same course)
    corrupt_attendance[30]["STUDENT_ID"] = corrupt_attendance[29]["STUDENT_ID"]
    corrupt_attendance[30]["COURSE_ID"] = corrupt_attendance[29]["COURSE_ID"]
    corrupt_attendance[30]["IS_ANOMALOUS"] = 1
    corrupt_attendance[30]["ANOMALY_REASON"] = "DUPLICATE_COURSE_ENROLLMENT"

    # Duplicate exam result
    corrupt_exam_results[45]["STUDENT_ID"] = corrupt_exam_results[44]["STUDENT_ID"]
    corrupt_exam_results[45]["COURSE_ID"] = corrupt_exam_results[44]["COURSE_ID"]
    corrupt_exam_results[45]["IS_ANOMALOUS"] = 1
    corrupt_exam_results[45]["ANOMALY_REASON"] = "DUPLICATE_EXAM_SUBMISSION"

    # 2.3 INVALID RANGES
    # Invalid Student Ages (negative, infant, or elderly)
    corrupt_students[5]["AGE"] = -2
    corrupt_students[5]["IS_ANOMALOUS"] = 1
    corrupt_students[5]["ANOMALY_REASON"] = "NEGATIVE_AGE"

    corrupt_students[18]["AGE"] = 142
    corrupt_students[18]["IS_ANOMALOUS"] = 1
    corrupt_students[18]["ANOMALY_REASON"] = "EXTREME_HIGH_AGE"

    corrupt_students[70]["AGE"] = 9
    corrupt_students[70]["IS_ANOMALOUS"] = 1
    corrupt_students[70]["ANOMALY_REASON"] = "UNDERAGE_STUDENT"

    # Attendance > 100% or negative
    corrupt_attendance[12]["ATTENDANCE_PERCENTAGE"] = 148.5
    corrupt_attendance[12]["IS_ANOMALOUS"] = 1
    corrupt_attendance[12]["ANOMALY_REASON"] = "ATTENDANCE_OVER_100"

    corrupt_attendance[82]["ATTENDANCE_PERCENTAGE"] = -15.0
    corrupt_attendance[82]["IS_ANOMALOUS"] = 1
    corrupt_attendance[82]["ANOMALY_REASON"] = "NEGATIVE_ATTENDANCE"

    # Marks negative or > max_marks
    corrupt_exam_results[10]["MARKS"] = -12.5
    corrupt_exam_results[10]["IS_ANOMALOUS"] = 1
    corrupt_exam_results[10]["ANOMALY_REASON"] = "NEGATIVE_MARKS"

    corrupt_exam_results[60]["MARKS"] = 135.0
    corrupt_exam_results[60]["MAX_MARKS"] = 100.0
    corrupt_exam_results[60]["IS_ANOMALOUS"] = 1
    corrupt_exam_results[60]["ANOMALY_REASON"] = "MARKS_EXCEED_MAX"

    # 2.4 INCONSISTENT RECORDS
    # Attended classes > Total classes
    corrupt_attendance[15]["TOTAL_CLASSES"] = 50
    corrupt_attendance[15]["ATTENDED_CLASSES"] = 62
    corrupt_attendance[15]["ATTENDANCE_PERCENTAGE"] = 80.0
    corrupt_attendance[15]["IS_ANOMALOUS"] = 1
    corrupt_attendance[15]["ANOMALY_REASON"] = "ATTENDED_GT_TOTAL_CLASSES"

    # Attendance pct completely disjoint from attended/total
    corrupt_attendance[40]["TOTAL_CLASSES"] = 50
    corrupt_attendance[40]["ATTENDED_CLASSES"] = 10  # true is 20%
    corrupt_attendance[40]["ATTENDANCE_PERCENTAGE"] = 95.0 # fabricated
    corrupt_attendance[40]["IS_ANOMALOUS"] = 1
    corrupt_attendance[40]["ANOMALY_REASON"] = "PERCENTAGE_COUNT_MISMATCH"

    # 2.5 FORMAT DEFECTS
    # Bad emails
    corrupt_students[8]["EMAIL"] = "plainaddress"
    corrupt_students[8]["IS_ANOMALOUS"] = 1
    corrupt_students[8]["ANOMALY_REASON"] = "MALFORMED_EMAIL"

    corrupt_students[22]["EMAIL"] = "john.doe@not-a-valid-domain"
    corrupt_students[22]["IS_ANOMALOUS"] = 1
    corrupt_students[22]["ANOMALY_REASON"] = "MALFORMED_EMAIL"

    corrupt_students[33]["EMAIL"] = "missing_at_symbol.com"
    corrupt_students[33]["IS_ANOMALOUS"] = 1
    corrupt_students[33]["ANOMALY_REASON"] = "MALFORMED_EMAIL"

    # Bad phone numbers
    corrupt_students[14]["PHONE_NUMBER"] = "12345"
    corrupt_students[14]["IS_ANOMALOUS"] = 1
    corrupt_students[14]["ANOMALY_REASON"] = "INVALID_PHONE_SHORT"

    corrupt_students[55]["PHONE_NUMBER"] = "CALL-ME-NOW"
    corrupt_students[55]["IS_ANOMALOUS"] = 1
    corrupt_students[55]["ANOMALY_REASON"] = "INVALID_PHONE_ALPHA"

    # 2.6 STATISTICAL ML ANOMALIES (Technically valid by SQL rules, but severe multivariate outliers)
    # E.g., Student has 98% attendance, but scored 3% on exam despite 4th year CS student.
    # E.g., Student attended 2% of classes (1 class out of 50) but scored 99.5% marks.
    # E.g., Highly unusual age vs year of study cluster.
    ml_outlier_indices = [110, 125, 140, 175, 190, 210, 230, 250]
    for idx in ml_outlier_indices:
        if idx < len(corrupt_attendance) and idx < len(corrupt_exam_results):
            s_id = corrupt_attendance[idx]["STUDENT_ID"]
            # 99% attendance, 4% marks (or vice versa)
            if idx % 2 == 0:
                corrupt_attendance[idx]["TOTAL_CLASSES"] = 50
                corrupt_attendance[idx]["ATTENDED_CLASSES"] = 49
                corrupt_attendance[idx]["ATTENDANCE_PERCENTAGE"] = 98.0
                corrupt_exam_results[idx]["MARKS"] = 5.0
                corrupt_attendance[idx]["IS_ANOMALOUS"] = 1
                corrupt_attendance[idx]["ANOMALY_REASON"] = "ML_MULTIVARIATE_OUTLIER_HIGH_ATT_ZERO_MARKS"
                corrupt_exam_results[idx]["IS_ANOMALOUS"] = 1
                corrupt_exam_results[idx]["ANOMALY_REASON"] = "ML_MULTIVARIATE_OUTLIER_HIGH_ATT_ZERO_MARKS"
            else:
                corrupt_attendance[idx]["TOTAL_CLASSES"] = 50
                corrupt_attendance[idx]["ATTENDED_CLASSES"] = 2
                corrupt_attendance[idx]["ATTENDANCE_PERCENTAGE"] = 4.0
                corrupt_exam_results[idx]["MARKS"] = 98.5
                corrupt_attendance[idx]["IS_ANOMALOUS"] = 1
                corrupt_attendance[idx]["ANOMALY_REASON"] = "ML_MULTIVARIATE_OUTLIER_ZERO_ATT_PERFECT_MARKS"
                corrupt_exam_results[idx]["IS_ANOMALOUS"] = 1
                corrupt_exam_results[idx]["ANOMALY_REASON"] = "ML_MULTIVARIATE_OUTLIER_ZERO_ATT_PERFECT_MARKS"

    # -------------------------------------------------------------
    # 3. EXPORT CSVs
    # -------------------------------------------------------------
    def save_csv(data, filepath):
        if not data:
            return
        keys = list(data[0].keys())
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)

    save_csv(clean_students, os.path.join(clean_dir, "students.csv"))
    save_csv(clean_attendance, os.path.join(clean_dir, "attendance.csv"))
    save_csv(clean_exam_results, os.path.join(clean_dir, "exam_results.csv"))

    save_csv(corrupt_students, os.path.join(corrupt_dir, "students.csv"))
    save_csv(corrupt_attendance, os.path.join(corrupt_dir, "attendance.csv"))
    save_csv(corrupt_exam_results, os.path.join(corrupt_dir, "exam_results.csv"))

    # Save course catalog CSV in both
    courses_rows = [
        {"COURSE_ID": c[0], "COURSE_NAME": c[1], "DEPARTMENT": c[2], "CREDITS": c[3]}
        for c in COURSES_DATA
    ]
    save_csv(courses_rows, os.path.join(clean_dir, "courses.csv"))
    save_csv(courses_rows, os.path.join(corrupt_dir, "courses.csv"))

    # -------------------------------------------------------------
    # 4. EXPORT ORACLE SQL SCRIPTS
    # -------------------------------------------------------------
    def format_sql_val(val):
        if val is None:
            return "NULL"
        if isinstance(val, (int, float)):
            return str(val)
        # Escape single quotes in strings
        s = str(val).replace("'", "''")
        return f"'{s}'"

    # Clean SQL Script
    sample_sql_path = os.path.join(output_dir, "sample_data.sql")
    with open(sample_sql_path, "w", encoding="utf-8") as f:
        f.write("-- ==============================================================================\n")
        f.write("-- AI-Based Database Data-Quality Analyzer\n")
        f.write("-- CLEAN BASELINE DATASET INSERT SCRIPT\n")
        f.write("-- ==============================================================================\n\n")
        f.write("SET DEFINE OFF;\n\n")
        
        # Courses
        f.write("-- COURSES\n")
        for c in COURSES_DATA:
            f.write(f"INSERT INTO COURSE (COURSE_ID, COURSE_NAME, DEPARTMENT, CREDITS) VALUES ('{c[0]}', '{c[1]}', '{c[2]}', {c[3]});\n")
        f.write("COMMIT;\n\n")

        # Students
        f.write("-- STUDENTS (Clean Baseline: 800 Records)\n")
        for s in clean_students:
            f.write(f"INSERT INTO STUDENT (STUDENT_ID, STUDENT_NAME, AGE, GENDER, DEPARTMENT, YEAR_OF_STUDY, EMAIL, PHONE_NUMBER) "
                    f"VALUES ({format_sql_val(s['STUDENT_ID'])}, {format_sql_val(s['STUDENT_NAME'])}, {format_sql_val(s['AGE'])}, "
                    f"{format_sql_val(s['GENDER'])}, {format_sql_val(s['DEPARTMENT'])}, {format_sql_val(s['YEAR_OF_STUDY'])}, "
                    f"{format_sql_val(s['EMAIL'])}, {format_sql_val(s['PHONE_NUMBER'])});\n")
        f.write("COMMIT;\n\n")

        # Attendance
        f.write("-- ATTENDANCE (Clean Baseline)\n")
        for a in clean_attendance:
            f.write(f"INSERT INTO ATTENDANCE (ATTENDANCE_ID, STUDENT_ID, COURSE_ID, ATTENDANCE_PERCENTAGE, TOTAL_CLASSES, ATTENDED_CLASSES) "
                    f"VALUES ({format_sql_val(a['ATTENDANCE_ID'])}, {format_sql_val(a['STUDENT_ID'])}, {format_sql_val(a['COURSE_ID'])}, "
                    f"{format_sql_val(a['ATTENDANCE_PERCENTAGE'])}, {format_sql_val(a['TOTAL_CLASSES'])}, {format_sql_val(a['ATTENDED_CLASSES'])});\n")
        f.write("COMMIT;\n\n")

        # Exam Results
        f.write("-- EXAM RESULTS (Clean Baseline)\n")
        for r in clean_exam_results:
            f.write(f"INSERT INTO EXAM_RESULT (RESULT_ID, STUDENT_ID, COURSE_ID, MARKS, MAX_MARKS, EXAM_DATE) "
                    f"VALUES ({format_sql_val(r['RESULT_ID'])}, {format_sql_val(r['STUDENT_ID'])}, {format_sql_val(r['COURSE_ID'])}, "
                    f"{format_sql_val(r['MARKS'])}, {format_sql_val(r['MAX_MARKS'])}, TO_DATE({format_sql_val(r['EXAM_DATE'])}, 'YYYY-MM-DD'));\n")
        f.write("COMMIT;\n")

    # Corrupted SQL Script
    corrupted_sql_path = os.path.join(output_dir, "corrupted_data.sql")
    with open(corrupted_sql_path, "w", encoding="utf-8") as f:
        f.write("-- ==============================================================================\n")
        f.write("-- AI-Based Database Data-Quality Analyzer\n")
        f.write("-- CONTROLLED CORRUPTED STAGING DATASET INSERT SCRIPT\n")
        f.write("-- ==============================================================================\n\n")
        f.write("SET DEFINE OFF;\n\n")
        
        # Courses
        f.write("-- COURSES\n")
        for c in COURSES_DATA:
            f.write(f"INSERT INTO COURSE (COURSE_ID, COURSE_NAME, DEPARTMENT, CREDITS) VALUES ('{c[0]}', '{c[1]}', '{c[2]}', {c[3]});\n")
        f.write("COMMIT;\n\n")

        # Students
        f.write("-- STUDENTS (Controlled Corrupted Ingestion)\n")
        for s in corrupt_students:
            f.write(f"INSERT INTO STUDENT (STUDENT_ID, STUDENT_NAME, AGE, GENDER, DEPARTMENT, YEAR_OF_STUDY, EMAIL, PHONE_NUMBER) "
                    f"VALUES ({format_sql_val(s['STUDENT_ID'])}, {format_sql_val(s['STUDENT_NAME'])}, {format_sql_val(s['AGE'])}, "
                    f"{format_sql_val(s['GENDER'])}, {format_sql_val(s['DEPARTMENT'])}, {format_sql_val(s['YEAR_OF_STUDY'])}, "
                    f"{format_sql_val(s['EMAIL'])}, {format_sql_val(s['PHONE_NUMBER'])});\n")
        f.write("COMMIT;\n\n")

        # Attendance
        f.write("-- ATTENDANCE (Controlled Corrupted Ingestion)\n")
        for a in corrupt_attendance:
            f.write(f"INSERT INTO ATTENDANCE (ATTENDANCE_ID, STUDENT_ID, COURSE_ID, ATTENDANCE_PERCENTAGE, TOTAL_CLASSES, ATTENDED_CLASSES) "
                    f"VALUES ({format_sql_val(a['ATTENDANCE_ID'])}, {format_sql_val(a['STUDENT_ID'])}, {format_sql_val(a['COURSE_ID'])}, "
                    f"{format_sql_val(a['ATTENDANCE_PERCENTAGE'])}, {format_sql_val(a['TOTAL_CLASSES'])}, {format_sql_val(a['ATTENDED_CLASSES'])});\n")
        f.write("COMMIT;\n\n")

        # Exam Results
        f.write("-- EXAM RESULTS (Controlled Corrupted Ingestion)\n")
        for r in corrupt_exam_results:
            f.write(f"INSERT INTO EXAM_RESULT (RESULT_ID, STUDENT_ID, COURSE_ID, MARKS, MAX_MARKS, EXAM_DATE) "
                    f"VALUES ({format_sql_val(r['RESULT_ID'])}, {format_sql_val(r['STUDENT_ID'])}, {format_sql_val(r['COURSE_ID'])}, "
                    f"{format_sql_val(r['MARKS'])}, {format_sql_val(r['MAX_MARKS'])}, TO_DATE({format_sql_val(r['EXAM_DATE'])}, 'YYYY-MM-DD'));\n")
        f.write("COMMIT;\n")

    print(f"Generated datasets successfully:\n - Students: {len(clean_students)}\n - Attendance: {len(clean_attendance)}\n - Exam Results: {len(clean_exam_results)}")
    print(f"SQL scripts saved to:\n - {sample_sql_path}\n - {corrupted_sql_path}")

if __name__ == "__main__":
    generate_datasets()

