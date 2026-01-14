# src/gmail_reader.py
import os
import re
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# スコープ: メールの読み取り専用（書き込み権限を与えない＝最小権限の原則）
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def get_gmail_service():
    """Gmail APIへの接続を確立し、serviceオブジェクトを返す"""
    creds = None
    # すでに認証済みならトークンを読み込む
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # 認証切れ、または初回実行時
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # ブラウザを立ち上げて認証画面を出す
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # 次回のためにトークンを保存
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def extract_paiza_url(text):
    """
    テキストからPaizaのゴールデンスカウトURLを正規表現で抽出する
    """
    pattern = r"https://paiza\.jp/student/golden_scouts/\d+"
    match = re.search(pattern, text)
    if match:
        return match.group(0)

    inbox_pattern = r"https://paiza\.jp/messages\?from=golden_scout"
    match = re.search(inbox_pattern, text)
    if match:
        return match.group(0)

    return None

def fetch_recent_scouts(limit=5):
    """
    最近の未読スカウトメールを探してリストで返す
    """
    service = get_gmail_service()
    
    # Paizaからのメールで、件名に「スカウト」を含み、かつ未読のもの
    query = 'from:paiza.jp subject:スカウト is:unread'
    
    results = service.users().messages().list(userId='me', q=query, maxResults=limit).execute()
    messages = results.get('messages', [])
    
    scout_list = []

    if not messages:
        print("📭 新着のスカウトメールはありません。")
        return []

    print(f"📬 {len(messages)} 件のメールが見つかりました。解析中...")

    for msg in messages:
        # メールの詳細を取得
        full_msg = service.users().messages().get(userId='me', id=msg['id']).execute()
        payload = full_msg['payload']
        headers = payload['headers']
        
        # 件名を取得
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "無題")
        
        # 本文のデコード（Gmail APIはbase64エンコードしてくる）
        body = ""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        body += base64.urlsafe_b64decode(data).decode('utf-8')
        elif 'body' in payload:
            data = payload['body'].get('data')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8')

        print(f"\n🔍 件名: {subject}")
        print(f"📄 本文(先頭300文字): {body[:300]}")  # これで中身が見える！
        
        # URL抽出
        url = extract_paiza_url(body)
        
        if url:
            scout_list.append({
                "subject": subject,
                "url": url,
                "id": msg['id'] # あとで既読にするために使う
            })
    
    return scout_list

# テスト実行用
if __name__ == "__main__":
    scouts = fetch_recent_scouts()
    for s in scouts:
        print(f"Title: {s['subject']}")
        print(f"URL: {s['url']}")
        print("-" * 30)
