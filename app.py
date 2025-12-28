from flask import Flask, render_template, request, redirect, url_for, jsonify
import pymysql

app = Flask(__name__)

def get_db():
    return pymysql.connect(
        host='localhost',
        user='root',          # 根据你的 MySQL 配置修改
        password='@Zjl100118',
        database='student_course_db',
        cursorclass=pymysql.cursors.DictCursor
    )

# 主页
@app.route('/')
def index():
    return render_template('index.html')

# ================== 学生管理 ==================
@app.route('/students')
def students():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM students")
        data = cursor.fetchall()
    db.close()
    return render_template('students.html', students=data)

@app.route('/add_student', methods=['POST'])
def add_student():
    name = request.form['name']
    gender = request.form['gender']
    age = request.form['age']
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("INSERT INTO students (name, gender, age) VALUES (%s, %s, %s)",
                       (name, gender, age))
        db.commit()
    db.close()
    return redirect(url_for('students'))

@app.route('/delete_student/<int:sid>')
def delete_student(sid):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM students WHERE student_id = %s", (sid,))
        db.commit()
    db.close()
    return redirect(url_for('students'))

@app.route('/edit_student/<int:sid>', methods=['GET', 'POST'])
def edit_student(sid):
    if request.method == 'POST':
        name = request.form['name']
        gender = request.form['gender']
        age = request.form['age']
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("UPDATE students SET name=%s, gender=%s, age=%s WHERE student_id=%s",
                           (name, gender, age, sid))
            db.commit()
        db.close()
        return redirect(url_for('students'))
    else:
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM students WHERE student_id = %s", (sid,))
            student = cursor.fetchone()
        db.close()
        return render_template('edit_student.html', student=student)

# ================== 课程管理 ==================
@app.route('/courses')
def courses():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM courses")
        data = cursor.fetchall()
    db.close()
    return render_template('courses.html', courses=data)

@app.route('/add_course', methods=['POST'])
def add_course():
    title = request.form['title']
    credit = request.form['credit']
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("INSERT INTO courses (title, credit) VALUES (%s, %s)",
                       (title, credit))
        db.commit()
    db.close()
    return redirect(url_for('courses'))

@app.route('/delete_course/<int:cid>')
def delete_course(cid):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM courses WHERE course_id = %s", (cid,))
        db.commit()
    db.close()
    return redirect(url_for('courses'))

# ================== 选课功能 ==================
@app.route('/enroll')
def enroll():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM students")
        students = cursor.fetchall()
        cursor.execute("SELECT * FROM courses")
        courses = cursor.fetchall()
    db.close()
    return render_template('enroll.html', students=students, courses=courses)

@app.route('/do_enroll', methods=['POST'])
def do_enroll():
    sid = request.form['student_id']
    cid = request.form['course_id']
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("INSERT INTO enrollments (student_id, course_id) VALUES (%s, %s)",
                           (sid, cid))
            db.commit()
    except pymysql.IntegrityError:
        pass  # 已选过，忽略
    db.close()
    return redirect(url_for('enroll'))

# ================== 查看已选课程（复杂查询） ==================
@app.route('/my_courses')
def my_courses():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT s.name AS student_name, c.title AS course_title, c.credit
            FROM enrollments e
            JOIN students s ON e.student_id = s.student_id
            JOIN courses c ON e.course_id = c.course_id
            ORDER BY s.name
        """)
        results = cursor.fetchall()
    db.close()
    return render_template('my_courses.html', records=results)

# ================== 可选课程预览 ==================
@app.route('/available_courses/<int:student_id>')
def available_courses(student_id):
    db = get_db()
    with db.cursor() as cursor:
        # 获取学生姓名
        cursor.execute("SELECT name FROM students WHERE student_id = %s", (student_id,))
        student = cursor.fetchone()
        if not student:
            return "学生不存在", 404
        student_name = student['name']

        # 查询该学生尚未选择的课程（使用 NOT IN）
        cursor.execute("""
            SELECT c.course_id, c.title, c.credit
            FROM courses c
            WHERE c.course_id NOT IN (
                SELECT e.course_id
                FROM enrollments e
                WHERE e.student_id = %s
            )
            ORDER BY c.course_id
        """, (student_id,))
        available = cursor.fetchall()
    db.close()
    return render_template(
        'available_courses.html',
        student_id=student_id,
        student_name=student_name,
        available_courses=available
    )

# ================== 执行单门课程选择 ==================
@app.route('/select_course/<int:student_id>/<int:course_id>', methods=['POST'])
def select_course(student_id, course_id):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("INSERT INTO enrollments (student_id, course_id) VALUES (%s, %s)",
                           (student_id, course_id))
            db.commit()
    except pymysql.IntegrityError:
        pass  # 已存在，忽略
    db.close()
    # 选完后自动刷新可选课程页面
    return redirect(url_for('available_courses', student_id=student_id))

if __name__ == '__main__':
    app.run(debug=True)