import re
from playwright.sync_api import sync_playwright

AUTH_FILE = "auth.json"

def clean_text(text):
    """テキスト整形用"""
    if not text: return ""
    text = text.replace("\n", " ").replace("　", " ")
    text = re.sub(r'【.*?】', '', text)
    text = re.sub(r'\s+', '', text)
    return text

def extract_smart_keyword(subject):
    """件名から検索キーワード（会社名優先）を抽出"""
    # 1. 英語の会社名 (例: CARTA HOLDINGS)
    english_name = re.search(r'[a-zA-Z][a-zA-Z\s\.]+(?:Inc\.|Corp\.|Holdings|Group)?', subject, re.IGNORECASE)
    if english_name and len(english_name.group(0).strip()) > 3:
        return clean_text(english_name.group(0))

    # 2. 株式会社〇〇
    jp_company = re.search(r'株式会社\s*(\S+)', subject)
    if jp_company:
        return clean_text(jp_company.group(1))

    # 3. なければ件名の冒頭10文字
    return clean_text(subject)[:10]

def fetch_job_text(target_url, target_subject=None):
    """
    URLを開き、件名に一致するスカウトを探して求人詳細テキストを返す
    見つからない場合は空文字を返す
    """
    keyword = extract_smart_keyword(target_subject) if target_subject else ""
    print(f"🚀 解析開始: {keyword}")

    extracted_text = ""

    with sync_playwright() as p:
        # 本番運用時は headless=True にしてもOKですが、動きが見たい場合はFalseで
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=AUTH_FILE)
        page = context.new_page()

        try:
            page.goto(target_url)
            page.wait_for_load_state("domcontentloaded")
            
            job_url_found = None
            
            if "messages" in page.url:
                print(" |__ 🕵️ メッセージ一覧から対象を検索中...")
                
                sidebar_selector = ".p-messages-scout-messages"
                try:
                    sidebar = page.locator(sidebar_selector)
                    sidebar.wait_for(state="visible", timeout=5000)
                    sidebar.hover() # フォーカス
                except:
                    print(" |__ ❌ サイドバーが見つかりません")
                    return ""

                target_message_link = None
                found = False

                # スクロール探索ループ
                for i in range(10):
                    current_links = sidebar.locator("a").all()
                    for link in current_links:
                        text = clean_text(link.inner_text())
                        if keyword and keyword.lower() in text.lower():
                            print(f" |__ ✨ 発見: {text[:20]}...")
                            target_message_link = link
                            found = True
                            break
                    if found: break
                    
                    # 物理スクロール
                    page.mouse.wheel(0, 2000)
                    page.wait_for_timeout(1000)

                if target_message_link:
                    # クリック処理
                    try:
                        target_message_link.click(force=True)
                        page.wait_for_timeout(2500) # 詳細ロード待ち
                    except Exception as e:
                        print(f" |__ ⚠️ クリックエラー: {e}")
                        return ""

                    # 詳細パネルから求人ID取得
                    detail_links = page.locator("a[href*='/job_offers/']").all()
                    if detail_links:
                        job_url_found = detail_links[0].get_attribute("href")
                        print(f" |__ ✅ 求人ページ特定: {job_url_found}")
                    else:
                        print(" |__ ❌ 詳細パネル内に求人リンクなし")
                        return ""
                else:
                    print(" |__ ❌ リスト内に該当なし(期限切れの可能性)")
                    return ""

            # 求人詳細ページへ移動
            if job_url_found:
                if not job_url_found.startswith("http"):
                    job_url_found = "https://paiza.jp" + job_url_found
                    
                page.goto(job_url_found)
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(2000)
                extracted_text = page.locator("body").inner_text()

        except Exception as e:
            print(f"❌ エラー: {e}")
        finally:
            browser.close()

    return extracted_text[:5000]
