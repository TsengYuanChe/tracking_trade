import os
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse

from utils.gcs_csv import read_csv_from_gcs, write_csv_to_gcs

from linebot.v3 import WebhookHandler
from linebot.v3.messaging import MessagingApi, ApiClient, Configuration
from linebot.v3.webhooks import MessageEvent, TextMessageContent, WebhookEvent

import pandas as pd
from datetime import datetime

app = FastAPI()

# ---------------------------------------
# Lazy 初始化（避免部署時就崩潰）
# ---------------------------------------
handler: WebhookHandler | None = None
line_api: MessagingApi | None = None


def init_line_bot():
    global handler, line_api

    channel_secret = os.getenv("LINE_CHANNEL_SECRET")
    channel_token = os.getenv("LINE_CHANNEL_TOKEN")

    if not channel_secret or not channel_token:
        print("⚠️ Warning: LINE credentials missing during init.")
        return False

    if handler is None:
        print("🔧 Initializing LINE WebhookHandler...")
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
# LINE Webhook Endpoint
# ---------------------------------------
@app.post("/callback")
async def callback(request: Request):

    # Lazy init（部署後 Cloud Run 才拿得到 Secret）
    if not init_line_bot():
        raise HTTPException(status_code=500, detail="LINE Bot未正確設定")

    signature = request.headers.get("X-Line-Signature")
    if not signature:
        raise HTTPException(400, "Missing LINE Signature")

    body = await request.body()
    body_text = body.decode("utf-8")

    try:
        handler.handle(body_text, signature)
    except Exception as e:
        print("❌ Webhook Error:", e)
        raise HTTPException(400, "Invalid Signature or Webhook Error")

    return PlainTextResponse("OK")


# ---------------------------------------
# 事件處理（改成手動註冊，而不是 decorator）
# ---------------------------------------
def handle_event(event: WebhookEvent):

    if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
        return handle_text_message(event)


def handle_text_message(event: MessageEvent):

    user_text = event.message.text.strip()
    reply_text = f"收到：{user_text}\n"

    try:
        df = read_csv_from_gcs()

        parts = [p.strip() for p in user_text.split(",")]
        if len(parts) != 4:
            reply_text += "\n⚠️ 格式錯誤：需為\n日期, 代號, 動作, 價格"
            reply_message(event.reply_token, reply_text)
            return

        date, code, action, value = parts
        action = action.upper()

        try:
            datetime.strptime(date, "%Y/%m/%d")
        except:
            reply_text += "\n⚠️ 日期格式錯誤：YYYY/MM/DD"
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

        reply_text += "\n✔ 已新增到 CSV（GCS）"

    except Exception as e:
        reply_text += f"\n❌ 錯誤：{str(e)}"

    reply_message(event.reply_token, reply_text)


# ---------------------------------------
# 回覆訊息
# ---------------------------------------
def reply_message(reply_token, text):
    if line_api is None:
        print("❌ MessagingApi 尚未初始化")
        return

    line_api.reply_message(
        reply_token=reply_token,
        messages=[
            {"type": "text", "text": text}
        ]
    )


# ---------------------------------------
# 將 LINE Handler 的事件派送導到我們的程式
# ---------------------------------------
def init_handler_dispatch():
    """替換 handler._handlers，讓他呼叫 handle_event()"""
    if handler:
        handler._handlers.clear()   # 清掉舊設定
        handler._handlers["default"] = handle_event


# Cloud Run 執行時會自動初始化一次
init_handler_dispatch()


if __name__ == "__main__":
    uvicorn.run("webhook.webhook_server:app", host="0.0.0.0", port=8080)