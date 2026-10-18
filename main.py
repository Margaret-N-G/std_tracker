import os
import re

from flask_bcrypt import Bcrypt
from flask import Flask, render_template, request, session, redirect, url_for, flash
from database import get_students, get_courses, get_performance, insert_users, insert_students, insert_courses, insert_performance, check_user_exists
from functools import wraps
from flask_wtf.csrf import CSRFProtect


app = Flask(__name__)

bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)


app.secret_key = os.environ.get('SECRET_KEY', 'student_tracker_secret_key')
app.config['WTF_CSRF_TIME_LIMIT'] = 3600



@app.route('/')
def home():
    return render_template('index.html',)


def login_required(f):
    @wraps(f)
    def protected(*args, **kwargs):
        if 'email' not in session:
            flash("please log in first", 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return protected

EMAIL_REGEX = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


@app.route('/students')
@login_required
def students():
    students_data = get_students()
    return render_template('students.html', students=students_data)


@app.route('/add_students', methods=['POST'])
@login_required
def add_students():
    full_name = request.form.get('f_name', '').strip()
    class_n = request.form.get('class', '').strip()
    adm_number = request.form.get('adm_no', '').strip()

    if not full_name or not class_n or not adm_number:
        flash("All fields are required", 'danger')
        return redirect(url_for('students'))

    insert_students((full_name, class_n, adm_number))
    flash("Student added successfully", "success")
    return redirect(url_for('students'))



@app.route('/courses')
@login_required
def courses():
    courses_data = get_courses()
    return render_template('courses.html', courses=courses_data)


@app.route('/add_course', methods=['GET', 'POST'])
@login_required
def add_courses():
    course_name = request.form.get('c_name', '').strip()
    teacher_id = request.form.get('t_id', '').strip()

    if not course_name or not teacher_id:
        flash("All fields are required", 'danger')
        return redirect(url_for('courses'))

    insert_courses((course_name, teacher_id))
    flash("Course added successfully", "success")
    return redirect(url_for('courses'))


@app.route('/performance')
@login_required
def performance():
    performance_data = get_performance()
    students_data = get_students()
    courses_data = get_courses()
    return render_template('performance.html', performance=performance_data, courses_data=courses_data, students_data=students_data)


@app.route('/add_performance', methods=['POST'])
@login_required
def add_performance():
    student_id = request.form.get('s_id')
    course_id = request.form.get('c_id')
    attendance = request.form.get('attendance') or ''
    quiz_scores = request.form.get('q_scores')
    marks = request.form.get('marks') or ''
    semester = request.form.get('semester')

    try:
        attendance_f = float(attendance)
        marks_f = float(marks)
    except (TypeError, ValueError):
        attendance_f = marks_f = -1

    if not (0 <= attendance_f <= 100 and 0 <= marks_f <= 100):
        flash("Attendance and marks must be numbers between 0 and 100", 'danger')
        return redirect(url_for('performance'))

    insert_performance((student_id, course_id, attendance, quiz_scores, marks, semester))
    flash("Performance updated successfully", "success")
    return redirect(url_for('performance'))




@app.route('/dashboard')
@login_required
def dashboard():
    students_data = get_students()
    courses_data = get_courses()
    performance_data = get_performance()

    def to_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    marks = [to_float(p['marks']) for p in performance_data]
    attendance = [to_float(p['attendance']) for p in performance_data]
    semesters = [p['semester'] for p in performance_data]

    average_marks = round(sum(marks) / len(marks), 2) if marks else 0
    highest_mark = max(marks) if marks else 0

    pass_count = sum(1 for mark in marks if mark >= 50)
    fail_count = sum(1 for mark in marks if mark < 50)
    total = pass_count + fail_count
    pass_rate = round((pass_count / total) * 100, 1) if total > 0 else 0

    return render_template(
        'dashboard.html',
        students_data=students_data,
        courses_data=courses_data,
        performance_data=performance_data,
        marks=marks,
        attendance=attendance,
        semesters=semesters,
        average_marks=average_marks,
        highest_mark=highest_mark,
        pass_count=pass_count,
        fail_count=fail_count,
        pass_rate=pass_rate
    )
    


@app.route('/user', methods=['GET', 'POST'])
def users():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role = request.form.get('role', '')

        if not EMAIL_REGEX.match(email):
            flash("Please enter a valid email address", 'danger')
            return render_template('users.html')

        if len(password) < 8:
            flash("Password must be at least 8 characters", 'danger')
            return render_template('users.html')

        if check_user_exists(email):
            flash("User with this email already exists, please login", 'danger')
            return render_template('users.html')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        insert_users((full_name, email, hashed_password, role))
        flash("User registered successfully", 'success')
        return redirect(url_for('login'))

    return render_template('users.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'email' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        existing_user = check_user_exists(email)

        if existing_user and bcrypt.check_password_hash(existing_user['password'], password):
            session['email'] = email
            session.permanent = True
            flash("Login successful", 'success')
            return redirect(url_for('dashboard'))

        flash("Invalid email or password", 'danger')  # same message both ways — no user enumeration

    return render_template('login.html')


@app.route('/logout', methods=['POST'])
def logout():
    session.pop('email', None)
    flash("Logged out successfully", 'success')
    return redirect(url_for('login'))


# starts up
if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')