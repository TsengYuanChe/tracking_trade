import requests
import json
import os

def push_message(text: str):
    CHANNEL_TOKEN = os.getenv("LINE_CHANNEL_TOKEN")
    USER_ID = os.getenv("LINE_USER_ID")
    
    if not CHANNEL_TOKEN or not USER_ID:
        print("[ERROR] Missing LINE credentials.")
        return

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_TOKEN}"
    }
    body = {
        "to": USER_ID,
        "messages": [
            {"type": "text", "text": text}
        ]
    }

    response = requests.post(url, headers=headers, data=json.dumps(body))
    print("Push Response:", response.status_code, response.text)