from flask import Flask, request, jsonify
import os
import psycopg2
from datetime import datetime, timedelta

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS sospesi (
                id SERIAL PRIMARY KEY,
                nome TEXT,
                prodotto TEXT,
                stato TEXT,
                updated_at TIMESTAMP
            )
            """)

def cleanup():
    limit = datetime.now() - timedelta(days=7)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM sospesi WHERE stato='ritirati' AND updated_at < %s", (limit,))

@app.route("/")
def home():
    return open("index.html").read()

@app.route("/api/list")
def list_items():
    cleanup()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM sospesi")
            rows = cur.fetchall()
    return jsonify([{
        "id": r[0],
        "nome": r[1],
        "prodotto": r[2],
        "stato": r[3]
    } for r in rows])

@app.route("/api/new", methods=["POST"])
def new():
    data = request.json
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO sospesi (nome, prodotto, stato, updated_at) VALUES (%s,%s,'ordinati',%s)",
                (data["nome"], data["prodotto"], datetime.now())
            )
    return "ok"

@app.route("/api/move", methods=["POST"])
def move():
    data = request.json
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE sospesi SET stato=%s, updated_at=%s WHERE id=%s",
                (data["stato"], datetime.now(), data["id"])
            )
    return "ok"

@app.route("/api/delete", methods=["POST"])
def delete():
    data = request.json
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM sospesi WHERE id=%s", (data["id"],))
    return "ok"

if __name__ == "__main__":
    init_db()
    app.run()