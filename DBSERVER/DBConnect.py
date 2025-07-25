root @ cb738c0e9ad4: ~  # ls
Android
JeGeun
development
ttottoProject
yelim
root @ cb738c0e9ad4: ~  # cd development/
root @ cb738c0e9ad4: ~ / development  # cd ..
root @ cb738c0e9ad4: ~  #
root @ cb738c0e9ad4: ~  # ls
Android
JeGeun
development
ttottoProject
yelim
root @ cb738c0e9ad4: ~  # cd ttottoProject/
root @ cb738c0e9ad4: ~ / ttottoProject  # ls
AiTest
DBconnect.py
__pycache__
flask_env
flutterTest
mydatabase.db
server.py
root @ cb738c0e9ad4: ~ / ttottoProject  # cat DBconnect.py
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import sqlite3
import bcrypt

# Flask 앱 생성 및 CORS 허용
app = Flask(__name__)
CORS(app)

# DB 경로 설정
DB_PATH = "mydatabase.db"


# DB 초기화 (테이블 없으면 생성)
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS users
                    (
                        id
                        INTEGER
                        PRIMARY
                        KEY
                        AUTOINCREMENT,
                        username
                        TEXT
                        UNIQUE
                        NOT
                        NULL,
                        password
                        TEXT
                        NOT
                        NULL,
                        name
                        TEXT,
                        email
                        TEXT
                        UNIQUE
                        NOT
                        NULL
                    )
                    """)
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS chat_messages
                    (
                        id
                        INTEGER
                        PRIMARY
                        KEY
                        AUTOINCREMENT,
                        user_id
                        INTEGER
                        NOT
                        NULL,
                        content
                        TEXT
                        NOT
                        NULL,
                        type
                        TEXT
                        CHECK (
                        type
                        IN
                    (
                        'user',
                        'bot'
                    )) NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY
                    (
                        user_id
                    ) REFERENCES users
                    (
                        id
                    )
                        )
                    """)
        conn.commit()


# 홈 라우트
@app.route("/")
def home():
    return "✅ Flask 서버가 작동 중입니다!"


# 로그인 라우트
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "아이디와 비밀번호를 모두 입력하세요."}), 400

        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, password FROM users WHERE username = ?", (username,))
            user = cur.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[1]):
            return jsonify({"message": "로그인 성공", "user_id": user[0]}), 200
        else:
            return jsonify({"error": "아이디 또는 비밀번호가 일치하지 않습니다."}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 회원가입 라우트 (CORS 처리 포함)
@app.route('/signup', methods=['POST', 'OPTIONS'])
def signup():
    if request.method == 'OPTIONS':
        # CORS preflight 요청 처리
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response

    try:
        data = request.get_json()

        # 필수 필드 확인
        required_fields = ['username', 'password', 'email']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} 필드가 누락되었습니다."}), 400

        # DB에 사용자 정보 저장
        hashed_pw = bcrypt.hashpw(data["password"].encode('utf-8'), bcrypt.gensalt())
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
                        INSERT INTO users (username, password, name, email)
                        VALUES (?, ?, ?, ?)
                        """, (
                            data["username"],
                            hashed_pw,
                            data.get("name", ""),  # name이 없어도 빈 문자열로 처리
                            data["email"]
                        ))
            conn.commit()
        return jsonify({"message": "회원가입 성공"}), 201

    except sqlite3.IntegrityError as e:
        return jsonify({"error": "이미 사용 중인 사용자 이름 또는 이메일입니다."}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 채팅 저장 라우트
@app.route('/chat', methods=['POST'])
def save_chat_message():
    try:
        data = request.get_json()

        required_fields = ['user_id', 'content', 'type']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} 필드가 누락되었습니다."}), 400

        if data["type"] not in ['user', 'bot']:
            return jsonify({"error": "type은 'user' 또는 'bot' 이어야 합니다."}), 400

        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
                        INSERT INTO chat_messages (user_id, content, type)
                        VALUES (?, ?, ?)
                        """, (
                            data["user_id"],
                            data["content"],
                            data["type"]
                        ))
            conn.commit()

        return jsonify({"message": "채팅 메시지 저장 성공"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get_history', methods=['GET'])
def get_history():
    user_id = request.args.get('user_id')
    # 한 번에 가져올 최근 메시지 수를 제한합니다 (예: 최근 10개).
    # Flutter 앱에서 limit 파라미터로 조절할 수 있게 합니다.
    limit = request.args.get('limit', default=10, type=int)

    if not user_id:
        return jsonify({"error": "user_id가 필요합니다."}), 400

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row  # 컬럼 이름으로 데이터 접근 가능하게 설정
            cur = conn.cursor()

            # 최근 메시지를 timestamp 기준으로 내림차순(최신순)으로 가져옵니다.
            cur.execute("""
                        SELECT content, type
                        FROM chat_messages
                        WHERE user_id = ?
                        ORDER BY timestamp DESC
                            LIMIT ?
                        """, (user_id, limit))

            rows = cur.fetchall()

            # LM Studio는 시간 순서대로(오래된 메시지 -> 최신 메시지 순) 대화 내용을 받기를 기대하므로,
            # 가져온 메시지 목록의 순서를 뒤집어줍니다.
            # 또한, DB에 저장된 'type' ('user', 'bot')을 LM Studio가 이해하는 'role' ('user', 'assistant')로 변경합니다.
            history_for_lm_studio = []
            for row in reversed(rows):  # reversed()를 사용하여 순서를 뒤집음 (오래된 메시지가 먼저 오도록)
                role_for_lm_studio = 'assistant' if row['type'] == 'bot' else 'user'
                history_for_lm_studio.append({
                    "role": role_for_lm_studio,
                    "content": row["content"]
                })

            return jsonify(history_for_lm_studio), 200

    except Exception as e:
        print(f"Error in /get_history: {e}")  # 서버 로그에 에러 출력
        return jsonify({"error": "이전 대화 내용을 가져오는 중 오류가 발생했습니다."}), 500


# 메인 함수
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=15180, debug=True)
root @ cb738c0e9ad4: ~ / ttottoProject  #