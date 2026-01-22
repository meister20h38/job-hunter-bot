# src/notification.py
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def send_discord_notify(job_data, ai_result):
    """
    AIの判定結果をDiscordに送信する
    """
    if not WEBHOOK_URL:
        print("⚠️ Discord Webhook URLが設定されていません。通知をスキップします。")
        return

    score = ai_result.get("score", 0)

    # スコアに応じて色を変える (緑:高, 黄:中, 赤:低)
    if score >= 80:
        color = 0x00FF00  # Green
        title = f"★ 激アツ求人発見！ (スコア: {score})"
    elif score >= 60:
        color = 0xFFFF00  # Yellow
        title = f"● 検討圏内の求人 (スコア: {score})"
    else:
        color = 0xFF0000  # Red
        title = f"× イマイチな求人 (スコア: {score})"

    # Discordの埋め込みメッセージ(Embed)を作成
    embed = {
        "title": title,
        "description": f"**概要:** {ai_result.get('summary')}\n\n[求人ページを開く]({job_data['url']})",
        "color": color,
        "fields": [
            {
                "name": "👍 メリット",
                "value": ai_result.get("pros", "なし"),
                "inline": False,
            },
            {
                "name": "👎 懸念点",
                "value": ai_result.get("cons", "なし"),
                "inline": False,
            },
            {
                "name": "📝 AIコメント",
                "value": ai_result.get("reason", "なし"),
                "inline": False,
            },
        ],
        "footer": {"text": f"JobHunter-Bot | {job_data['subject']}"},
    }

    payload = {"username": "AI就活コンシェルジュ", "embeds": [embed]}

    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("🔔 Discordに通知を送りました。")
    except Exception as e:
        print(f"❌ Discord通知エラー: {e}")
