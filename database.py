import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()   # ← reads .env file into the environment

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', 5432)),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD'),
    'dbname': os.environ.get('DB_NAME', 'student_tracker'),
}


def get_db():
    """Returns a (connection, cursor) pair. Caller must close both."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    return conn, cur


def check_user_exists(email):
    conn, cur = get_db()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user


def get_students():
    conn, cur = get_db()
    cur.execute("SELECT * FROM students")
    students = cur.fetchall()
    cur.close()
    conn.close()
    return students


def insert_students(student_values):
    conn, cur = get_db()
    cur.execute(
        "INSERT INTO students(name, class, adm_number) VALUES (%s, %s, %s)",
        student_values
    )
    conn.commit()
    cur.close()
    conn.close()


def get_courses():
    conn, cur = get_db()
    cur.execute("SELECT * FROM courses")
    courses = cur.fetchall()
    cur.close()
    conn.close()
    return courses


def insert_courses(course_values):
    conn, cur = get_db()
    cur.execute(
        "INSERT INTO courses(name, teacher_id) VALUES (%s, %s)",
        course_values
    )
    conn.commit()
    cur.close()
    conn.close()


def get_performance():
    conn, cur = get_db()
    cur.execute("SELECT * FROM performance")
    performance = cur.fetchall()
    cur.close()
    conn.close()
    return performance


def insert_performance(performance_values):
    conn, cur = get_db()
    cur.execute(
        """
        INSERT INTO performance(
            student_id, course_id, attendance, quiz_scores, marks, semester
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        performance_values
    )
    conn.commit()
    cur.close()
    conn.close()


def insert_users(user_values):
    conn, cur = get_db()
    cur.execute(
        "INSERT INTO users(name, email, password, role) VALUES (%s, %s, %s, %s)",
        user_values
    )
    conn.commit()
    cur.close()
    conn.close()