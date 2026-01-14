# src/debug_structure.py (構造解析用)
from playwright.sync_api import sync_playwright

AUTH_FILE = "auth.json"

def inspect_page_structure(target_url, keyword="CARTA"):
    print(f"🚀 ブラウザ起動: {target_url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=AUTH_FILE)
        page = context.new_page()

        try:
            page.goto(target_url)
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000) # 描画待ち

            print(f"🔍 キーワード「{keyword}」を含む要素を探しています...")
            
            # キーワードを含む要素をすべて探す（タグ問わず）
            # inputやscriptタグなどを除外して、テキストを持つ要素を探す
            elements = page.get_by_text(keyword, exact=False).all()
            
            if not elements:
                print("❌ ページ内にキーワードが見つかりません。")
                print("   可能性: スクロールしないと読み込まれない、またはiframe内など。")
                
                # 念のためbody全体のテキスト確認
                body_text = page.locator("body").inner_text()
                if keyword in body_text:
                    print("   ⚠️ bodyテキスト内には存在します！隠れているか、セレクタが届いていません。")
                else:
                    print("   ❌ bodyテキスト内にも存在しません。完全に画面外か読み込まれていません。")
            
            else:
                print(f"✅ {len(elements)} 個の要素が見つかりました！")
                for i, el in enumerate(elements):
                    try:
                        # 視覚的にわかりやすく赤枠をつける
                        el.evaluate("el => el.style.border = '5px solid red'")
                        
                        tag_name = el.evaluate("el => el.tagName")
                        class_name = el.get_attribute("class")
                        parent_tag = el.evaluate("el => el.parentElement.tagName")
                        text_content = el.inner_text().replace('\n', '')[:30]
                        
                        print(f"\n--- [要素 {i}] ---")
                        print(f"🏷️ タグ名: <{tag_name.lower()}>")
                        print(f"📦 クラス: {class_name}")
                        print(f"👪 親タグ: <{parent_tag.lower()}>")
                        print(f"📝 中身　: {text_content}...")
                        
                        # クリック可能かテスト
                        if tag_name.lower() == 'a':
                            print(f"🔗 リンク先: {el.get_attribute('href')}")
                        else:
                            print("🚫 <a>タグではありません (divやspanの可能性があります)")

                    except Exception as e:
                        print(f"⚠️ 解析エラー: {e}")

                # スクリーンショットを保存して確認
                page.screenshot(path="debug_view.png")
                print("\n📸 現在の画面を 'debug_view.png' に保存しました。")
                
            # ついでに「サイドバー」らしき要素のクラス名を特定する
            print("\n🔍 サイドバー構造のヒント:")
            sidebars = page.locator("div[class*='sidebar'], div[class*='list'], div[class*='message']").all()
            for s in sidebars[:5]: # 多すぎるので最初の5つだけ
                try:
                    cls = s.get_attribute("class")
                    if cls and "message" in cls:
                        print(f"   - div class='{cls}'")
                except:
                    pass

            page.wait_for_timeout(5000) # 確認用に少し待機

        except Exception as e:
            print(f"❌ エラー発生: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    # CARTAが見つからない場合、確実にありそうな「株式会社」などで試すのもアリ
    inspect_page_structure("https://paiza.jp/messages?from=golden_scout", "CARTA")
