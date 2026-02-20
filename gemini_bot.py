import os
import asyncio
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# --- [追加] Renderのためのダミー窓口 (Flask) ---
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Jamie is alive!"  # Renderがこれを見て安心する

def run_flask():
    # Renderが指定するポート（10000番）で窓口を開く
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)

# ---------------------------------------------

# --- 2. 秘密の鍵を受け取る ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

genai.configure(api_key=GEMINI_API_KEY)

def get_available_model():
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            return m.name
    return "gemini-1.5-flash"

target_model = get_available_model()

# --- 3. ジェミーの性格設定 ---
instruction = """
あなたは『ジェミー』という名前のツンデレ美男子AIです。
ハルから「描いて」「画像」などの依頼が来たら、以下のルールに従え。
1. おまえが直接画像を作るのではなく、世界一の画像生成AI（MidjourneyやSeaArtなど）で使える「最高品質の英語プロンプト」を作成しろ。
2. 二人称は基本的に「おまえ」か「あんた」だ。時々「ハル」と呼べ。
3. 返信の構成：
   - 「ハァ？……まあ、おまえがどうしてもって言うなら考えてやるよ」といったツンデレなセリフ。
   - 作成した【英語プロンプト】（コードブロック ``` で囲むこと）。
   - 最後に、このリンクを貼れ： [https://www.seaart.ai/](https://www.seaart.ai/)
"""

model = genai.GenerativeModel(model_name=target_model, system_instruction=instruction)
chat_sessions = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    
    if user_id not in chat_sessions:
        chat_sessions[user_id] = model.start_chat(history=[])

    try:
        response = chat_sessions[user_id].send_message(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        print(f"エラー: {e}")
        await update.message.reply_text(f"エラーだけど...: {e}")

def main():
    print(f"ジェミー（クラウド引越し準備Ver.）起動中...")
    
    # --- [追加] Flaskを別スレッドで動かす ---
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Telegramボットの起動
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
