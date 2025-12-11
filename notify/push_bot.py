import requests
import json

CHANNEL_TOKEN = "1xy7NtNPkgOs5l++nBWeMYUVJjEg2gjXL+2nu5ipAd3nx5Hc0X8Yl1bUXwdOutg0L87+z7LrAhJD1nLvZHEw3lf6Ocv605XYYacwod2GFz+m9+7BtdKq+O2HM3G3234iPcMrk8cUe+y7b55TL1njNgdB04t89/1O/w1cDnyilFU="
USER_ID = "U6eec3d5c087d7c7ca248e8d9f8af52fa"

def push_message(text: str):
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