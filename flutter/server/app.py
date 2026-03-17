from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import bcrypt

app = Flask(__name__)
CORS(app)

# ✅ DB 경로 통일 (절대 경로 사용 권장)
DB_PATH = os.path.join(os.path.dirname(__file__), 'mydatabase.db')

# ✅ DB 초기화 함수
def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 사용자 테이블 생성
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            )
        ''')

        # 메시지 테이블 생성
        cursor.execute('''
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('user', 'bot')),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')

        conn.commit()
        conn.close()

# ✅ 서버 시작 시 DB 초기화
init_db()

# ✅ 회원가입
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()

    required_fields = ['username', 'password', 'email']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400

    try:
        hashed_pw = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password, email)
            VALUES (?, ?, ?)
        ''', (data['username'], hashed_pw, data['email']))
        conn.commit()
        conn.close()
        return jsonify({'message': 'User registered successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username or email already exists'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ✅ 로그인
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    required_fields = ['username', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM users WHERE username = ?
        ''', (data['username'],))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.checkpw(data['password'].encode('utf-8'), user[2]):
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': user[0],
                    'username': user[1],
                    'email': user[3]
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid username or password'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ✅ 채팅 메시지 저장
@app.route('/chat/save', methods=['POST'])
def save_chat():
    data = request.get_json()
    required_fields = ['user_id', 'content', 'type']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (user_id, content, type)
            VALUES (?, ?, ?)
        ''', (data['user_id'], data['content'], data['type']))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Message saved'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ✅ Flask 서버 시작 (외부 접속 가능하게 포트 15180 지정)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=15180, debug=True)
