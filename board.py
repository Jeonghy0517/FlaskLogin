import time
from flask import Flask, render_template, redirect, session, request, flash, Blueprint
from flask_pymongo import PyMongo

app = Flask(__name__)
app.secret_key = '19990517'

app.config["MONGO_URI"] = "mongodb://localhost:27017/my_web"
mongo = PyMongo(app)

# board_bp = Blueprint('board', __name__)

@app.route('/board', methods=['POST'])
def board():
    username = session.get('username')
    if 'username' not in session:
        return redirect('/login')

    if request.method == 'POST':
        cur_time = time.strftime("%y%m%d_%H%M%S")
        content = request.form['content']

        if len(content) == 0:
            flash('내용을 입력해주세요')
            return redirect('/board')

        board = mongo.db.board
        board_content = {
            "pubdate": cur_time,
            "content": content,
            "user": username
        }
        board.insert_one(board_content)

        board_data = list(mongo.db.board.find())
        return render_template('board.html', username=username, board_data=board_data)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
