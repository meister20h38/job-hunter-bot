# src/ai_client.py
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# .envからURLを取得（なければローカルのデフォルト値）
OLLAMA_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
# 使用するモデル名（Ollamaに入っているものを指定）
MODEL_NAME = "qwen2.5:14b"


def analyze_job_description(job_text, user_profile):
    """
    求人テキストとプロフィールを受け取り、AIの判定結果を返す
    """

    # AIへの指示書（プロンプト）
    prompt = f"""
    あなたは優秀なキャリアアドバイザーです。
    以下の「求職者プロフィール」に基づき、「求人内容」を厳しく評価してください。

    # 求職者プロフィール
    {user_profile}

    # 求人内容
    {job_text}

    # 出力フォーマット
    以下のJSON形式のみを出力してください。余計な挨拶は不要です。
    {{
        "score": 0〜100の整数,
        "summary": "企業名と業務内容の簡潔な要約(50文字以内)",
        "pros": "この求職者にとってのメリット(1行)",
        "cons": "懸念点(1行)",
        "reason": "スコアの理由(辛口で)"
    }}
    """

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json",  # JSONモードを強制（モデルが対応している場合）
    }

    try:
        print(f"🤖 AI({MODEL_NAME})に問い合わせ中...")
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()

        result_json = response.json()
        ai_response_text = result_json.get("response", "")

        # JSON文字列をPython辞書に変換して返す
        return json.loads(ai_response_text)

    except Exception as e:
        print(f"❌ AI通信エラー: {e}")
        return {"score": 0, "reason": "エラーが発生しました"}
