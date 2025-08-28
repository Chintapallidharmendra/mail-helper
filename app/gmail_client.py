from __future__ import annotations
from typing import List, Dict, Optional
import os
from datetime import datetime, timezone

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from .config import settings

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

def get_credentials() -> Credentials:
    creds = None
    if os.path.exists(settings.GMAIL_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(settings.GMAIL_TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(settings.GMAIL_CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(settings.GMAIL_TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return creds

def get_service():
    creds = get_credentials()
    return build('gmail', 'v1', credentials=creds, cache_discovery=False)

def list_messages(max_results: int = 100) -> List[Dict]:
    service = get_service()
    results = service.users().messages().list(userId=settings.GMAIL_USER_ID, labelIds=['INBOX'], maxResults=max_results).execute()
    return results.get('messages', [])

def get_message(message_id: str) -> Dict:
    service = get_service()
    # format=full to get payload and headers
    return service.users().messages().get(userId=settings.GMAIL_USER_ID, id=message_id, format='full').execute()

def parse_headers(payload_headers: List[Dict]) -> Dict[str, str]:
    headers = {}
    for h in payload_headers:
        headers[h.get('name', '').lower()] = h.get('value', '')
    return headers

def extract_plain_text(payload: Dict) -> str:
    # Walk parts to find text/plain
    def walk(part):
        if part.get('mimeType') == 'text/plain' and 'data' in part.get('body', {}):
            import base64
            return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
        for p in part.get('parts', []) or []:
            txt = walk(p)
            if txt:
                return txt
        return ""
    return walk(payload) or ""

def get_labels_map() -> Dict[str, str]:
    service = get_service()
    res = service.users().labels().list(userId=settings.GMAIL_USER_ID).execute()
    return {lbl['name']: lbl['id'] for lbl in res.get('labels', [])}

def ensure_label(name: str) -> str:
    service = get_service()
    labels = get_labels_map()
    if name in labels:
        return labels[name]
    res = service.users().labels().create(userId=settings.GMAIL_USER_ID, body={"name": name, "labelListVisibility":"labelShow"}).execute()
    return res['id']

def modify_message(message_id: str, add_labels: Optional[list]=None, remove_labels: Optional[list]=None):
    service = get_service()
    body = {"addLabelIds": add_labels or [], "removeLabelIds": remove_labels or []}
    return service.users().messages().modify(userId=settings.GMAIL_USER_ID, id=message_id, body=body).execute()
