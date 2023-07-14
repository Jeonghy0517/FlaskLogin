from flask import Flask, render_template, request, redirect, session, flash, url_for
from email_validator import validate_email, EmailNotValidError
import pymysql
import os
import json

CONFIG_DIR = "./config"
config_file = os.path.join (CONFIG_DIR, "db.json")

app = Flask(__name__)

with open(config_file) as f:
    db_config = json.loads(f.read())

def get_conf(set, conf=db_config):
    try:
        return conf[set]
    except KeyError:
        err_msg = f"set the {set} enviroment variable"
        raise print(err_msg)

db_host = get_conf("host")
db_user = get_conf("user")
db_passwd = get_conf("passwd")
db_schema = get_conf("schema")
db_port = get_conf("port")

def db_connect():
    conn = pymysql.connect(host=db_host,
                    port=int(db_port),
                    user=db_user,
                    passwd=db_passwd,
                    db=db_schema,
                    charset='utf8'
    )
    return conn

@app.route('/')
def index():
    if 'username' in session:
        return redirect('/main')
    else:
        return redirect('/login')

@app.route('/main')
def main():
    return render_template('main.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/signup_proc', methods=['GET','POST'])
def signup_proc():
    id_receive = request.form['id']
    pwd_receive = request.form['pwd']
    email_receive = request.form['email']

    values = [
        id_receive,
        pwd_receive,
        email_receive
    ]

    if len(id_receive) == 0 or len(pwd_receive) == 0 or len(email_receive) == 0:
        flash("회원 정보를 입력하세요")
        return redirect('/signup')

    try:
        validate_email(email_receive)
    except EmailNotValidError as e:
        flash('올바른 이메일 형식이 아닙니다.')
        return redirect('/signup')

    db = db_connect()
    try:
        with db.cursor() as cursor:
            sql = 'SELECT userid FROM member WHERE userid = %s'
            cursor.execute(sql, id_receive)
            result = cursor.fetchone()

            if result is not None:
                flash('중복된 아이디 입니다.')
                return redirect('/signup')

            sql = """
                INSERT INTO member(userid, userpwd, usermail)
                VALUES (%s, %s, %s)
                """
            cursor.execute(sql, values)
            db.commit()

            flash('회원가입이 완료되었습니다.')
            return redirect('/login')
    finally:
        db.close()

@app.route('/login_proc', methods=['GET', 'POST'])
def login_proc():
    if request.method == 'POST':
        username = request.form['id']
        password = request.form['pwd']
        if len(username) == 0 or len(password) == 0:
            flash("ID 또는 PASSWORD를 입력하세요")
            return redirect('/login')
        else:
            db = db_connect()

            try:
                with db.cursor() as cursor:
                    sql = """
                    SELECT idx, userid, userpwd, usermail
                    FROM member
                    WHERE userid = %s
                    """
                    cursor.execute(sql, username)
                    rows = cursor.fetchall()

                    for rs in rows:
                        if username == rs[1] and password == rs[2]:
                            session['logFlag'] = True
                            session['idx'] = rs[0]
                            session['username'] = username
                            session['email'] = rs[3]
                            return redirect('/main')
                        else:
                            flash("PASSWORD 정보가 틀렸습니다.")
                            return redirect('/login')
            finally:
                db.close()
    else:
        flash("잘못된 접근 입니다.")
        return redirect(url_for('login'))

    flash("존재하지 않는 회원입니다.")
    return redirect(url_for('login'))

@app.route('/user_info_edit/<int:edit_idx>', methods=['GET'])
def getuser(edit_idx):
    if session.get('logFlag') != True:
        return redirect('/login')
    db = db_connect()
    try:
        with db.cursor() as cursor:
            sql = """
            SELECT usermail
            FROM member
            WHERE idx = %s
            """
            cursor.execute(sql, edit_idx)
            row = cursor.fetchone()
            edit_email = row[0]
    finally:
        cursor.close()
        db.close()
    return render_template('info.html', edit_idx=edit_idx, edit_email=edit_email)

@app.route('/info_edit_proc', methods=['POST'])
def user_info_edit_proc():
    idx = request.form['idx']
    password = request.form['pwd']
    email = request.form['email']

    values = [
        password,
        email,
        idx
    ]

    if len(idx) == 0 or len(password) == 0 or len(email) == 0:
        flash('값을 입력해주세요')
        return redirect('user_info_edit/1')

    db = db_connect()
    try:
        with db.cursor() as cursor:
            # 기존 값 조회
            sql = """
            SELECT userpwd, usermail
            FROM member
            WHERE idx = %s
            """
            cursor.execute(sql, idx)
            row = cursor.fetchone()
            original_password, original_email = row[0], row[1]

            if password == original_password and email == original_email:
                flash('변경된 정보가 없습니다.')
                return redirect('user_info_edit/1')
            elif password != original_password or email != original_email:
                try:
                    sql = """
                        UPDATE member
                        SET userpwd = %s, usermail = %s
                        WHERE idx = %s
                        """
                    cursor.execute(sql, values)
                    db.commit()

                    session.clear()
                    redirect('login')
                    flash('재로그인이 필요합니다.')
                except Exception as e:
                    flash('업데이트 중 오류가 발생했습니다.')
                    print(str(e))
                    return redirect('user_info_edit/1')
    finally:
        cursor.close()
        db.close()

    return redirect('main')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('main')

if __name__ == '__main__':
    app.secret_key = '19990517'
    app.run(debug=True)