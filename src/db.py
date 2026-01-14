# src/db.py
import sqlite3
import datetime

DB_PATH = "history.db"

def init_db():
    """データベースとテーブルの初期化"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # processed_jobs テーブルを作成
    # message_id: GmailのメッセージID (ユニークキー)
    # url: 求人URL
    # score: AIがつけたスコア
    # created_at: 処理日時
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_jobs (
            message_id TEXT PRIMARY KEY,
            url TEXT,
            score INTEGER,
            create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def is_processed(message_id):
    """指定されたメッセージIDが処理済みかチェック"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM processed_jobs WHERE message_id = ?", (message_id,))
    result = cursor.fetchone()

    conn.close()
    return result is not None

def save_job_record(message_id, url, score):
    """処理結果を保存"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO processed_jobs (message_id, url, score)
            VALUES (?, ?, ?)
        """, (message_id, url, score))
        conn.commit()
        print(f"💾 履歴に保存しました (ID: {message_id[-6:]}...)")
    except sqlite3.IntegrityError:
        print(f"⚠️ 既に保存済みです (ID: {message_id[-6:]}...)")
    finally:
        conn.close()

# モジュール読み込み時に自動で初期化
init_db()
