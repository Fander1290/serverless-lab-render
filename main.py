from flask import Flask, request, jsonify
import os
import psycopg2
from urllib.parse import urlparse

app = Flask(__name__)

# Глобальная переменная для соединения с БД
db_conn = None

def get_db_connection():
    global db_conn
    if db_conn is None:
        try:
            DATABASE_URL = os.environ.get('DATABASE_URL')
            if DATABASE_URL:
                url = urlparse(DATABASE_URL)
                db_conn = psycopg2.connect(
                    database=url.path[1:],
                    user=url.username,
                    password=url.password,
                    host=url.hostname,
                    port=url.port
                )
                # Создаем таблицу если её нет
                with db_conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS messages (
                            id SERIAL PRIMARY KEY,
                            content TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT NOW()
                        )
                    """)
                    db_conn.commit()
        except Exception as e:
            print(f"Database error: {e}")
            db_conn = None
    return db_conn

@app.route('/')
def hello():
    return "Hello, Serverless! 🚀\n", 200, {'Content-Type': 'text/plain'}

@app.route('/echo', methods=['POST'])
def echo():
    data = request.get_json()
    return jsonify({
        "status": "received",
        "you_sent": data,
        "length": len(str(data)) if data else 0
    })

@app.route('/save', methods=['POST'])
def save_message():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB not connected"}), 500

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data"}), 400
            
        message = data.get('message', '')
        
        with conn.cursor() as cur:
            cur.execute("INSERT INTO messages (content) VALUES (%s)", (message,))
            conn.commit()
        
        return jsonify({"status": "saved", "message": message})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/messages')
def get_messages():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB not connected"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, content, created_at FROM messages ORDER BY id DESC LIMIT 10")
            rows = cur.fetchall()
        
        messages = [{"id": r[0], "text": r[1], "time": str(r[2])} for r in rows]
        return jsonify(messages)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)