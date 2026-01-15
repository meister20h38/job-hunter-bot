# src/main.py
from paiza_crawler import run_crawler

def main():
    # 複雑なGmail連携やURL解析ロジックを廃止し、
    # 直接ブラウザを操作するクローラーを実行する
    run_crawler()

if __name__ == "__main__":
    main()
