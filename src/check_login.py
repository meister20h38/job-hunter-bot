from playwright.sync_api import sync_playwright

AUTH_FILE = "auth.json"

TARGET_URL = "https://paiza.jp/messages"

def main():
    print("ロボットによるアクセステストを開始します…")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        context = browser.new_context(storage_state=AUTH_FILE)
        page = context.new_page()

        print(f"URLへ移動中: {TARGET_URL}")
        page.goto(TARGET_URL)

        page.wait_for_load_state("networkidle")

        page_title = page.title()
        print(f"ページタイトル{page_title}")

        if "ログイン" in page_title or "Sign In" in page_title:
            print("✖　失敗: ログインページに飛ばされました。auth.jsonの期限切れか、保存ミスの可能性があります。")
        else:
            print("✅　成功: ログイン状態でアクセスできました！")

        page.wait_for_timeout(3000)
        browser.close()

if __name__ == '__main__':
    main()
