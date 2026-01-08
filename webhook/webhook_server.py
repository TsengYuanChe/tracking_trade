import os
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse

from utils.gcs_csv import read_csv_from_gcs, write_csv_to_gcs

from linebot.v3 import WebhookHandler
from linebot.v3.messaging import MessagingApi, ApiClient, Configuration, TextMessage, ReplyMessageRequest
from linebot.v3.webhooks import MessageEvent, TextMessageContent

import pandas as pd
from datetime import datetime

# ============================================================
# INIT HANDLER (Must be global, cannot lazy init)
# ============================================================
channel_secret = os.getenv("LINE_CHANNEL_SECRET")

if not channel_secret:
    print("❌ Missing LINE_CHANNEL_SECRET (env not loaded yet!)")
    handler = None
else:
    handler = WebhookHandler(channel_secret)


# ============================================================
# FASTAPI APP
# ============================================================
app = FastAPI()

line_api: MessagingApi | None = None


def init_line_api():
    """Lazy initialize Messaging API only."""
    global line_api
    if line_api is None:
        token = os.getenv("LINE_CHANNEL_TOKEN")
        if not token:
            print("❌ Missing LINE_CHANNEL_TOKEN")
            return False

        print("🔧 Creating Messaging API Client")
        config = Configuration(access_token=token)
        line_api = MessagingApi(ApiClient(config))

    return True

# ============================================================
# DECORATOR BINDING — The ONLY supported method in SDK v3
# ============================================================
if handler:
    @handler.add(MessageEvent, message=TextMessageContent)
    def _(event):
        handle_text_message(event)

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
    
    if handler is None:
        print("❌ handler is None (missing env on start)")
        raise HTTPException(500, "Handler not initialized")

    if not init_line_api():
        raise HTTPException(500, "LINE API not initialized")

    # ---- Signature ----
    signature = request.headers.get("X-Line-Signature")
    print("📝 Signature:", signature)

    if not signature:
        raise HTTPException(400, "Missing signature")

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
        raise HTTPException(400, "Invalid signature")

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
        
        value_norm = value.strip().lower()
        if value_norm in ["", "none", "null"]:
            value = "null"

        code = code.replace(".0", "")

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
        req = ReplyMessageRequest(
            reply_token=reply_token,
            messages=[TextMessage(text=text)],
            x_line_delivery_notification_bot_id=os.getenv("LINE_BOT_ID", None)
        )
        res = line_api.reply_message(req)
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