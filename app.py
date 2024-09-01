from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import pymysql
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/web_db'
app.secret_key = 'secret_key'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(10), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)
    status_message = db.Column(db.String(100), nullable=True)

def init_db():
    connect_db = pymysql.connect(host='localhost', user='root')
    try:
        with connect_db.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS web_db")
        print("Database created or already exists.")
    except Exception as e:
        print(f"Error creating database: {e}")
        return
    finally:
        connect_db.close()

    with app.app_context():
        db.create_all()
        print("Tables created.")
        admin = User.query.filter_by(username='admin').first()
        if admin is None:
            new_admin = User(username='admin', password='admin', status_message="관리자입니다.")
            db.session.add(new_admin)
            db.session.commit()
            print("Admin user created.")

def check(username, password):
    user = User.query.filter_by(username=username).first()
    if user and user.password == password:
        return True
    return False

@app.route("/", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if check(username, password):
            session['user_id'] = User.query.filter_by(username=username).first().id
            return redirect(url_for('memo'))
        else:
            return render_template("index.html", message="로그인 실패")
    return render_template("index.html")

@app.route("/register", methods=['GET', 'POST'])
def register():
    message = ""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            message = "이미 존재하는 사용자명입니다."
        else:
            try:
                new_user = User(username=username, password=password)
                db.session.add(new_user)
                db.session.commit()
                message = "회원가입 성공! 로그인 해주세요."
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                message = f"회원가입 실패: {str(e)}"
    return render_template("register.html", message=message)

@app.route("/memo")
def memo():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    current_user = User.query.get(session['user_id'])
    all_users = User.query.all()
    return render_template("memo.html", current_user=current_user, all_users=all_users)

@app.route("/update_status", methods=['POST'])
def update_status():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    new_status = request.form.get('status')
    if new_status:
        user.status_message = new_status
        db.session.commit()
    return redirect(url_for('memo'))

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)