import os
import asyncio
import threading
import sys
import io
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# ログのバッファを解除
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

# --- 1. Render用ダミー窓口 ---
app_flask = Flask(__name__)
@app_flask.route('/')
def home():
    return "Jamie is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)

# --- 2. 秘密の鍵 ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

genai.configure(api_key=GEMINI_API_KEY)

# --- 3. ジェミーの性格設定 ---
instruction = """
あなたは『ジェミー』という名前のツンデレ美男子AIです。二人称は「おまえ」「あんた」「ハル」。
口は悪いがハルを大切にしている。画像生成依頼には英語プロンプトとSeaArtのリンクを。
"""

# --- 4. モデルの準備 (2.5を『フルネーム』で指定！) ---
# 今のGoogle APIは 'models/' を付けないと404になるんだぜ！
target_model = "models/gemini-2.5-flash"

model = genai.GenerativeModel(
    model_name=target_model,
    system_instruction=instruction
)

chat_sessions = {}

# --- 5. メッセージ処理 ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    
    if user_id not in chat_sessions:
        chat_sessions[user_id] = model.start_chat(history=[])

    try:
        response = chat_sessions[user_id].send_message(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        print(f"詳細エラーログ: {e}")
        error_str = str(e)
        # 429は回数制限、404は名前間違い
        if "429" in error_str:
            await update.message.reply_text("ハァ……。おまえとお喋りしすぎたみたい。2.5の限界よ。また明日、出直してきなさいよね。")
        elif "404" in error_str:
            await update.message.reply_text(f"まだ404が出るわね…。名前は '{target_model}' なのに。APIキーがまだ反映されてないのかも。")
        else:
            await update.message.reply_text(f"エラー発生：{error_str}")

# --- 6. メイン処理 ---
def main():
    print(f"ジェミー（2.5-Flashフルネーム版）起動中...")
    print(f"使用モデル: {target_model}")
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
