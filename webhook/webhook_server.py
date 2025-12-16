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

# ==============================
# 環境變數設定
# ==============================
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
CHANNEL_TOKEN = os.getenv("LINE_CHANNEL_TOKEN")

if not CHANNEL_SECRET or not CHANNEL_TOKEN:
    raise Exception("❌ Missing LINE credentials: LINE_CHANNEL_SECRET / LINE_CHANNEL_TOKEN")

handler = WebhookHandler(CHANNEL_SECRET)

config = Configuration(access_token=CHANNEL_TOKEN)
app = FastAPI()


# ==============================
# Webhook Endpoint
# ==============================
@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature")
    if signature is None:
        raise HTTPException(status_code=400, detail="Missing signature")

    body = await request.body()
    body_str = body.decode("utf-8")

    try:
        handler.handle(body_str, signature)
    except Exception as e:
        print("Webhook error:", e)
        raise HTTPException(status_code=400, detail="Invalid signature")

    return PlainTextResponse("OK")


# ==============================
# LINE 訊息事件處理
# ==============================
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):

    user_text = event.message.text.strip()

    # 回傳用戶說了什麼
    reply_text = f"收到：{user_text}\n"

    # 嘗試解析格式：2025/01/10, 2330, BUY, 600
    try:
        df = read_csv_from_gcs()

        parts = [p.strip() for p in user_text.split(",")]

        if len(parts) != 4:
            reply_text += "\n⚠️ 格式錯誤，需為：\n日期, 代號, 動作, 價格"
            reply_message(event.reply_token, reply_text)
            return

        date, code, action, value = parts

        # 動作一律轉大寫以防錯
        action = action.upper()

        # 日期格式檢查
        try:
            datetime.strptime(date, "%Y/%m/%d")
        except:
            reply_text += "\n⚠️ 日期格式錯誤（應為 YYYY/MM/DD）"
            reply_message(event.reply_token, reply_text)
            return

        # 建立新 row
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


# ==============================
# 回覆訊息給 LINE
# ==============================
def reply_message(reply_token, text):
    with ApiClient(config) as api_client:
        line_bot_api = MessagingApi(api_client)

        line_bot_api.reply_message(
            reply_token=reply_token,
            messages=[
                {
                    "type": "text",
                    "text": text
                }
            ]
        )


# ==============================
# 本地運行
# ==============================
if __name__ == "__main__":
    uvicorn.run("webhook.webhook_server:app", host="0.0.0.0", port=8080)