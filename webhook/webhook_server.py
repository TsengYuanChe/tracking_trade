# webhook/webhook_server.py
import os
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse

from utils.gcs_csv import read_csv_from_gcs, write_csv_to_gcs

from linebot.v3 import WebhookHandler
from linebot.v3.messaging import MessagingApi, ApiClient, Configuration
from linebot.v3.webhooks import MessageEvent, TextMessageContent

import pandas as pd
from datetime import datetime

app = FastAPI()

# ======================================
# Lazy-load LINE handler & config
# ======================================
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
CHANNEL_TOKEN = os.getenv("LINE_CHANNEL_TOKEN")

handler = None
config = None


def init_line_sdk():
    """避免 container 啟動時爆炸，首次 webhook 時才初始化"""
    global handler, config

    if handler is None:
        if not CHANNEL_SECRET:
            print("⚠️ Warning: LINE_CHANNEL_SECRET is missing")
        else:
            handler = WebhookHandler(CHANNEL_SECRET)

    if config is None:
        if not CHANNEL_TOKEN:
            print("⚠️ Warning: LINE_CHANNEL_TOKEN is missing")
        else:
            config = Configuration(access_token=CHANNEL_TOKEN)


# ======================================
# Health Check
# ======================================
@app.get("/")
def health():
    return {"ok": True}


# ======================================
# Webhook Endpoint
# ======================================
@app.post("/callback")
async def callback(request: Request):

    init_line_sdk()  # ⭐ 在這裡初始化（不會阻止 container 啟動）

    signature = request.headers.get("X-Line-Signature")
    if signature is None:
        raise HTTPException(status_code=400, detail="Missing signature")

    body = await request.body()
    body_str = body.decode("utf-8")

    if handler:
        try:
            handler.handle(body_str, signature)
        except Exception as e:
            print("Webhook Signature Error:", e)
            # ⚠️ LINE 官方建議仍須回傳 200，否則會停止推送
            return PlainTextResponse("Signature Error", status_code=200)

    return PlainTextResponse("OK")


# ======================================
# LINE Message Event
# ======================================
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):

    user_text = event.message.text.strip()
    reply_text = f"收到：{user_text}\n"

    try:
        df = read_csv_from_gcs()

        parts = [p.strip() for p in user_text.split(",")]

        if len(parts) != 4:
            reply_text += "\n⚠️ 格式錯誤，應為：日期, 代號, 動作, 價格"
            reply_message(event.reply_token, reply_text)
            return

        date, code, action, value = parts
        action = action.upper()

        try:
            datetime.strptime(date, "%Y/%m/%d")
        except:
            reply_text += "\n⚠️ 日期格式錯誤（應為 YYYY/MM/DD）"
            reply_message(event.reply_token, reply_text)
            return

        new_row = pd.DataFrame([{
            "date": date,
            "code": code,
            "action": action,
            "value": value
        }])

        df = pd.concat([df, new_row], ignore_index=True)
        write_csv_to_gcs(df)

        reply_text += "\n✔ 已成功寫入 trades.csv 到 GCS！"

    except Exception as e:
        reply_text += f"\n❌ 錯誤：{str(e)}"

    reply_message(event.reply_token, reply_text)


# ======================================
# Reply Helper
# ======================================
def reply_message(reply_token, text):
    init_line_sdk()
    if not config:
        print("⚠️ No LINE TOKEN, cannot reply.")
        return

    with ApiClient(config) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            reply_token=reply_token,
            messages=[{"type": "text", "text": text}]
        )


# ======================================
# Local Run
# ======================================
if __name__ == "__main__":
    uvicorn.run("webhook.webhook_server:app", host="0.0.0.0", port=8080)