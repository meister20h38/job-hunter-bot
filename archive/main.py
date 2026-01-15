# src/main.py
import time
from gmail_reader import fetch_recent_scouts
from analyze_url import fetch_job_text
from ai_client import analyze_job_description
from notification import send_discord_notify
from profile import MY_PROFILE
import db

# 通知を送るボーダーライン（70点以上なら通知）
SCORE_THRESHOLD = 70

def main():
    print("🤖 JobHunter-Bot 起動しました")
    
    # 1. Gmailからスカウト取得
    scouts = fetch_recent_scouts(limit=10) # テスト用に3件だけ
    
    if not scouts:
        print("💤 新着メールはありません。")
        return

    # 未処理のスカウトだけをフィルタリング
    new_scouts = [s for s in scouts if not db.is_processed(s['id'])]    

    if not new_scouts:
        print("💤 すべて処理済みです。")
        return

    print(f"📋 {len(scouts)} 件のスカウトを処理します...")

    for i, scout in enumerate(scouts):
        print(f"\n--- [ {i+1} / {len(new_scouts)} ] -----------------------")
        print(f"📧 件名: {scout['subject']}")
        print(f"🔗 URL: {scout['url']}")

        # 2. ブラウザで本文取得
        job_text = fetch_job_text(scout['url'], scout['subject'], scout.get('body_preview', ''))
        
        if not job_text:
            print("⚠️ 本文が取得できませんでした。スキップします。")
            continue

        # 3. AI判定
        print("🧠 AI分析中...")
        result = analyze_job_description(job_text, MY_PROFILE)
        
        score = result.get('score', 0)
        print(f"🎯 スコア: {score}点")
        print(f"📝 理由: {result.get('reason')}")

        # 4. 通知判定
        if score >= SCORE_THRESHOLD:
            print("🔔 高スコア！Discordに通知します。")
            send_discord_notify(scout, result)
        else:
            print("🗑️ スコア不足のため通知しません。")

        # 5. 処理済みとしてDBに記録
        db.save_job_record(scout['id'], scout['url'], score)
        
        # 連続アクセスを制限
        time.sleep(3)

    print("\n✅ すべての処理が完了しました。")

if __name__ == "__main__":
    main()
