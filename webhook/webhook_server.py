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

# ---------------------------------------
# Lazy Initialization
# ---------------------------------------
handler: WebhookHandler | None = None
line_api: MessagingApi | None = None


def init_line_bot():
    """Initialize LINE SDK after Cloud Run loads environment variables"""
    global handler, line_api

    channel_secret = os.getenv("LINE_CHANNEL_SECRET")
    channel_token = os.getenv("LINE_CHANNEL_TOKEN")

    if not channel_secret or not channel_token:
        print("⚠️ Missing LINE credentials")
        return False

    if handler is None:
        print("🔧 Creating WebhookHandler")
        handler = WebhookHandler(channel_secret)

    if line_api is None:
        config = Configuration(access_token=channel_token)
        line_api = MessagingApi(ApiClient(config))

    return True


# ---------------------------------------
# Health Check
# ---------------------------------------
@app.get("/")
def health():
    return {"ok": True}


# ---------------------------------------
# Webhook Endpoint
# ---------------------------------------
@app.post("/callback")
async def callback(request: Request):

    if not init_line_bot():
        raise HTTPException(status_code=500, detail="LINE Bot not initialized")

    signature = request.headers.get("X-Line-Signature")
    if not signature:
        raise HTTPException(400, "Missing LINE Signature")

    body = await request.body()
    body_text = body.decode("utf-8")

    try:
        handler.handle(body_text, signature)
    except Exception as e:
        print("❌ Webhook Error:", e)
        raise HTTPException(400, "Invalid Signature")

    return PlainTextResponse("OK")


# ---------------------------------------
# Event Dispatcher
# ---------------------------------------
def handle_event(event):
    if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
        handle_text_message(event)


def handle_text_message(event: MessageEvent):

    user_text = event.message.text.strip()
    reply_text = f"收到：{user_text}"

    try:
        df = read_csv_from_gcs()
        parts = [p.strip() for p in user_text.split(",")]

        if len(parts) != 4:
            reply_message(event.reply_token, reply_text + "\n⚠ 格式錯誤：需為\n日期, 代號, 動作, 價格")
            return

        date, code, action, value = parts
        action = action.upper()

        # 日期檢查
        try:
            datetime.strptime(date, "%Y/%m/%d")
        except:
            reply_message(event.reply_token, reply_text + "\n⚠ 日期格式錯誤：YYYY/MM/DD")
            return

        # 寫入新資料
        new_row = pd.DataFrame([{
            "date": date,
            "code": code,
            "action": action,
            "value": value
        }])

        df = pd.concat([df, new_row], ignore_index=True)
        write_csv_to_gcs(df)

        reply_message(event.reply_token, reply_text + "\n✔ 已寫入 trades.csv！")

    except Exception as e:
        reply_message(event.reply_token, reply_text + f"\n❌ 錯誤：{str(e)}")


# ---------------------------------------
# Reply to LINE
# ---------------------------------------
def reply_message(reply_token, text):
    if line_api is None:
        print("❌ Messaging API not initialized")
        return

    line_api.reply_message(
        reply_token=reply_token,
        messages=[{"type": "text", "text": text}],
    )


# ---------------------------------------
# Bind event handler
# ---------------------------------------
def init_handler_dispatch():
    if handler:
        handler._handlers.clear()
        handler._handlers["default"] = handle_event


init_handler_dispatch()


# ---------------------------------------
# Local Test Mode
# ---------------------------------------
if __name__ == "__main__":
    uvicorn.run("webhook.webhook_server:app", host="0.0.0.0", port=8080)