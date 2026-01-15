#src/gmail_reader.py
import os
import re
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def get_gmail_service():
    """Gmail APIへの接続"""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def extract_paiza_url(text):
    """URL抽出ロジック"""
    pattern = r"https://paiza\.jp/student/golden_scouts/\d+"
    match = re.search(pattern, text)
    if match: return match.group(0)

    inbox_pattern = r"https://paiza\.jp/messages\?from=golden_scout"
    match = re.search(inbox_pattern, text)
    if match: return match.group(0)

    return None

def fetch_recent_scouts(limit=5):
    """スカウトメールを取得し、件名・URL・本文プレビューを返す"""
    service = get_gmail_service()
    
    # query変更なし
    #query = 'from:paiza.jp subject:スカウト'
    query = 'from:paiza.jp newer_than:3d'
    results = service.users().messages().list(userId='me', q=query, maxResults=limit).execute()
    messages = results.get('messages', [])
    scout_list = []

    if not messages:
        print("📭 直近3日間の新着メールはありません。")
        return []

    print(f"📬 {len(messages)} 件のメールを解析中...")

    for msg in messages:
        full_msg = service.users().messages().get(userId='me', id=msg['id']).execute()
        payload = full_msg['payload']
        headers = payload['headers']

        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "無題")
        date_str = next((h['value'] for h in headers if h['name'] == 'Date'), "不明")
        # 本文デコード
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
        
        url = extract_paiza_url(body)

        if url:
            scout_list.append({
                "subject": subject,
                "url": url,
                "id": msg['id'],
                "body_preview": body[:500] # ★追加: 本文の先頭500文字を保存
            })

    return scout_list
