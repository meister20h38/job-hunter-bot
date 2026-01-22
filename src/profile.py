# src/profile.py
import os

PROFILE_PATH = "user_profile.txt"


def load_profile():
    # ファイルが存在すれば読み込む
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            return f.read()

    # なければデフォルト（エラー避け）
    return "プロフィールファイル(user_profile.txt)が見つかりません。"


# 変数ではなく関数経由で取得するように変更
MY_PROFILE = load_profile()
