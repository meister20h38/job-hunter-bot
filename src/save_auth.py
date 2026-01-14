import time
from playwright.sync_api import sync_playwright

AUTH_FILE = "auth.json"

TARGET_URL = "https://paiza.jp/sign_in"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("アクセス中: {TARGET_URL}")
        page.goto(TARGET_URL)

        print("\n" + "="*50)
        print("【手動操作のお願い】")
        print("ブラウザを開きました。画面上でログインしてください。")
        print("ログインが完了したら、コンソールに戻りEnterを押してください。")
        print("\n" + "="*50)

        input("ログインが完了したらEnterを押してください >> ")

        context.storage_state(path=AUTH_FILE)
        print(f"\n認証情報を'{AUTH_FILE}'に保存しました。")
        print("このファイルを用いて次回以降は自動でアクセスできます。")

        browser.close()

if __name__ == '__main__':
    main()
