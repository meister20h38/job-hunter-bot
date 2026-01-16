# src/paiza_crawler.py
import re
import time
from playwright.sync_api import sync_playwright
from ai_client import analyze_job_description
from notification import send_discord_notify
from profile import MY_PROFILE
import db

AUTH_FILE = "auth.json"
MAX_CHECK_LIMIT = 20 
SCORE_THRESHOLD = 70

def clean_text(text):
    return text.replace("\n", " ").strip()

def run_crawler():
    print("🤖 Paiza Direct Crawler (Final) 起動")
    
    with sync_playwright() as p:
        # headless=True でブラウザを開かない
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=AUTH_FILE)

        page_list = context.new_page()   # [タブA] 一覧用
        page_worker = context.new_page() # [タブB] 解析用

        try:
            # リストが確実に読み込まれるURLを指定
            start_url = "https://paiza.jp/messages?from=golden_scout"
            print(f"🚀 [List] {start_url} にアクセス中...")
            page_list.goto(start_url)
            
            # 正しいリストコンテナを指定
            sidebar_selector = ".p-messages-scout-messages"
            try:
                # まずコンテナが出るのを待つ
                page_list.wait_for_selector(sidebar_selector, state="visible", timeout=10000)
                
                # 「コンテナの中にリンク(aタグ)が表示される」のを明示的に待つ
                # 中身が空のうちは先に進ませない
                print("⏳ メッセージリストの描画を待機中...")
                # コンテナ内のaタグを探すセレクタ
                list_item_selector = f"{sidebar_selector} a"
                page_list.wait_for_selector(list_item_selector, state="attached", timeout=10000)
                
                # 念のため少し待機（アニメーション等の完了待ち）
                page_list.wait_for_timeout(2000)

            except Exception as e:
                print(f"❌ リストの読み込みに失敗しました: {e}")
                return

            print("🕵️ メッセージリストをスキャン中...")
            sidebar = page_list.locator(sidebar_selector)
            
            # スクロールして過去分も少し読み込む
            sidebar.hover()
            for _ in range(3):
                page_list.mouse.wheel(0, 1000)
                page_list.wait_for_timeout(500)
            
            # 一番上に戻す
            sidebar.evaluate("el => el.scrollTop = 0")
            page_list.wait_for_timeout(1000)

            # リンク取得
            message_links = sidebar.locator("a").all()
            print(f"📋 検出されたリンク総数: {len(message_links)} 件")

            processed_count = 0
            
            # 解析ループ
            target_count = min(len(message_links), MAX_CHECK_LIMIT)
            
            for i in range(target_count):
                link = message_links[i]
                try:
                    title_text = clean_text(link.inner_text())[:30]
                    
                    # 空のリンクや「もっと見る」ボタン等はスキップ
                    if not title_text or "もっと見る" in title_text: continue
                    
                    # [タブA] クリック
                    # リスト内の要素が隠れている場合のエラー回避
                    link.scroll_into_view_if_needed()
                    link.click(force=True)
                    page_list.wait_for_timeout(1500) # 詳細ロード待ち

                    # --- 右パネルの解析 ---
                    # job_offersを含むリンクを探す
                    job_links = page_list.locator("a[href*='/job_offers/']").all()
                    
                    if not job_links:
                        # 求人リンクがない場合はスキップ（ログをうるさくしないためコメントアウト可）
                        # print(f"  [{i}] ⏩ スキップ: 求人リンクなし (件名: {title_text})")
                        continue

                    job_url_suffix = job_links[0].get_attribute("href")
                    job_url = f"https://paiza.jp{job_url_suffix}" if not job_url_suffix.startswith("http") else job_url_suffix
                    
                    # ID抽出
                    match = re.search(r'/job_offers/(\d+)', job_url)
                    job_id = match.group(1) if match else job_url

                    # DBチェック (高速化の要)
                    if db.is_processed(job_id):
                        print(f"  [{i}] ♻️ 処理済み: {title_text}... (ID:{job_id})")
                        continue

                    # --- [タブB] 解析実行 ---
                    print(f"  [{i}] 🆕 解析開始: {title_text}... (ID:{job_id})")
                    
                    page_worker.goto(job_url)
                    page_worker.wait_for_load_state("domcontentloaded")
                    job_text = page_worker.locator("body").inner_text()[:6000]

                    print("    🧠 AI分析中...")
                    result = analyze_job_description(job_text, MY_PROFILE)
                    score = result.get('score', 0)
                    print(f"    🎯 スコア: {score}点")

                    if score >= SCORE_THRESHOLD:
                        print("    🔔 Discord通知送信")
                        dummy_scout = {'subject': f"【Web解析】{title_text}", 'url': job_url}
                        send_discord_notify(dummy_scout, result)
                    else:
                        print("    🗑️ スコア不足")

                    db.save_job_record(job_id, job_url, score)
                    processed_count += 1
                    time.sleep(2) # マナー待機

                except Exception as e:
                    # 個別のエラーは無視して次へ
                    continue

            print(f"✅ 完了: {processed_count} 件の新規スカウトを処理しました。")

        except Exception as e:
            print(f"❌ 全体エラー: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_crawler()
