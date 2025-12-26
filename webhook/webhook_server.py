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


# ============================================================
# FASTAPI APP
# ============================================================
app = FastAPI()

# LINE lazy loaded objects
handler: WebhookHandler | None = None
line_api: MessagingApi | None = None


# ============================================================
# INIT LINE (Lazy)
# ============================================================
def init_line_bot():
    """
    Initialize LINE SDK after Cloud Run loads env vars.
    """
    global handler, line_api

    channel_secret = os.getenv("LINE_CHANNEL_SECRET")
    channel_token = os.getenv("LINE_CHANNEL_TOKEN")

    if not channel_secret or not channel_token:
        print("❌ Missing LINE credentials")
        return False

    if handler is None:
        print("🔧 Creating WebhookHandler")
        handler = WebhookHandler(channel_secret)
        # 正確綁定事件
        handler.add(MessageEvent, TextMessageContent, handle_text_message)
        
    if line_api is None:
        print("🔧 Creating Messaging API Client")
        config = Configuration(access_token=channel_token)
        line_api = MessagingApi(ApiClient(config))

    return True


# ============================================================
# HEALTH CHECK
# ============================================================
@app.get("/")
def health():
    return {"ok": True}


# ============================================================
# WEBHOOK ENDPOINT
# ============================================================
@app.post("/callback")
async def callback(request: Request):

    print("\n==============================")
    print("🔥 Received /callback")

    if not init_line_bot():
        raise HTTPException(status_code=500, detail="LINE init failed")

    # ---- Signature ----
    signature = request.headers.get("X-Line-Signature")
    print("📝 Signature:", signature)

    if not signature:
        print("❌ Missing signature")
        raise HTTPException(status_code=400, detail="Missing signature")

    # ---- Body ----
    body_bytes = await request.body()
    body_text = body_bytes.decode("utf-8")
    print("📩 Body:", body_text)

    # ---- Handle ----
    try:
        handler.handle(body_text, signature)
        print("✅ handler.handle finished")
    except Exception as e:
        print("❌ Webhook Error:", e)
        raise HTTPException(status_code=400, detail="Invalid signature")

    return PlainTextResponse("OK")


# ============================================================
# EVENT DISPATCHER
# ============================================================
def handle_text_message(event: MessageEvent):
    """
    Handle user text input.
    Format: YYYY/MM/DD, code, action, value
    """
    user_text = event.message.text.strip()
    print(f"💬 Received Text: {user_text}")

    reply_text = f"收到：{user_text}"

    # ---- Parse input ----
    try:
        df = read_csv_from_gcs()
        print("📄 Loaded trades.csv from GCS")

        parts = [p.strip() for p in user_text.split(",")]

        if len(parts) != 4:
            reply_message(event.reply_token,
                          reply_text + "\n⚠ 格式錯誤：需為\n日期, 代號, 動作, 價格")
            return

        date, code, action, value = parts
        action = action.upper()

        # ---- 日期檢查 ----
        try:
            datetime.strptime(date, "%Y/%m/%d")
        except:
            reply_message(event.reply_token,
                          reply_text + "\n⚠ 日期格式錯誤：YYYY/MM/DD")
            return

        # ---- 新增 Row ----
        new_row = pd.DataFrame([{
            "date": date,
            "code": code,
            "action": action,
            "value": value
        }])

        df = pd.concat([df, new_row], ignore_index=True)

        write_csv_to_gcs(df)
        print("💾 Successfully wrote to trades.csv")

        reply_message(event.reply_token,
                      reply_text + "\n✔ 已寫入 trades.csv！")

    except Exception as e:
        print("❌ Error handling message:", e)
        reply_message(event.reply_token,
                      reply_text + f"\n❌ 錯誤：{str(e)}")


# ============================================================
# REPLY MESSAGE
# ============================================================
def reply_message(reply_token, text):
    print("====================================")
    print("🔁 reply_message CALLED")
    print("🔁 reply_token:", reply_token)
    print("🔁 reply text:", text)
    print("====================================")

    if line_api is None:
        print("❌ Messaging API not initialized")
        return

    try:
        res = line_api.reply_message(
            reply_token=reply_token,
            messages=[{"type": "text", "text": text}],
        )
        print("✅ reply_message success:", res)
    except Exception as e:
        print("🔥 reply_message ERROR:", e)


# ============================================================
# LOCAL RUN
# ============================================================
if __name__ == "__main__":
    uvicorn.run("webhook.webhook_server:app",
                host="0.0.0.0",
                port=8080,
                reload=True)