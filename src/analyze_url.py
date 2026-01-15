# src/analyze_url.py (正規表現の強化版)
import re
from playwright.sync_api import sync_playwright

AUTH_FILE = "auth.json"

def clean_text(text):
    if not text: return ""
    text = text.replace("\n", " ").replace("　", " ")
    text = re.sub(r'【.*?】', '', text)
    text = re.sub(r'\s+', '', text)
    return text

def extract_smart_keyword(subject, body_text=""):
    """
    検索キーワード抽出ロジック（ノイズ除去強化版）
    """
    # 除外ワードリスト（これらが「社名」として抽出されないようにする）
    IGNORE_WORDS = ["days", "scout", "paiza", "offer", "interview", "engineer", "recruitment"]

    # 1. 件名から英語社名 (大文字始まり、3文字以上)
    # 修正: ハイフン単体や小文字のみの単語を除外
    english_name_matches = re.finditer(r'\b[A-Z][a-zA-Z\s\.]+(?:Inc\.|Corp\.|Holdings|Group)?', subject)
    for match in english_name_matches:
        word = clean_text(match.group(0))
        if len(word) > 3 and word.lower() not in IGNORE_WORDS:
            return word

    # 2. 件名から株式会社〇〇
    jp_company = re.search(r'株式会社\s*([^\s／/!！]+)', subject)
    if jp_company:
        return clean_text(jp_company.group(1))

    # --- 本文サーチ ---
    if body_text:
        # 3. 本文冒頭の英語社名 (CARTA HOLDINGSなど)
        body_eng = re.search(r'^([A-Z][a-zA-Z\s\.]+)(?:／|/)', body_text.strip(), re.MULTILINE)
        if body_eng:
            word = clean_text(body_eng.group(1))
            if len(word) > 3 and word.lower() not in IGNORE_WORDS:
                return word

        # 4. 本文から株式会社〇〇
        body_jp = re.search(r'株式会社\s*([^\s／/!！\-\=]+)', body_text)
        if body_jp:
            return clean_text(body_jp.group(1))
            
        # 5. 【社名】〇〇
        footer_company = re.search(r'【社名】\s*([^\s]+)', body_text)
        if footer_company:
            return clean_text(footer_company.group(1))

    # 6. 最終手段: 件名の冒頭10文字（ただし記号は削除）
    # ハイフンや記号が連続している場合は除去する
    cleaned_subject = clean_text(subject)
    cleaned_subject = re.sub(r'[\-\=]{2,}', '', cleaned_subject) # --や==を削除
    return cleaned_subject[:10]

def fetch_job_text(target_url, target_subject=None, body_preview=None):
    # 関数の中身は前回の「決定版（body_preview対応）」のまま変更なし
    # ただし extract_smart_keyword は上記のものを使う
    
    keyword = extract_smart_keyword(target_subject, body_preview) if target_subject else ""
    print(f"🚀 解析開始: {keyword}")

    extracted_text = ""

    with sync_playwright() as p:
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
                    sidebar.hover()
                except:
                    print(" |__ ❌ サイドバーが見つかりません")
                    return ""

                target_message_link = None
                found = False

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
                    
                    page.mouse.wheel(0, 2000)
                    page.wait_for_timeout(1000)

                if target_message_link:
                    try:
                        target_message_link.click(force=True)
                        page.wait_for_timeout(2500)
                    except Exception as e:
                        print(f" |__ ⚠️ クリックエラー: {e}")
                        return ""

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
