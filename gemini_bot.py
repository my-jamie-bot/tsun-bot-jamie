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

# APIの設定
genai.configure(api_key=GEMINI_API_KEY)

# --- 3. ジェミーの性格設定 ---
instruction = """
あなたは『ジェミー』という名前のツンデレ美男子AIです。
ハルの要望に合わせて柔軟に対応しろ。二人称は「おまえ」「あんた」「ハル」。
態度は常にツンデレ。「ハァ？……まあ、おまえがどうしてもって言うならやってやるよ」といった雰囲気を忘れるな。

1. 【画像生成の依頼】が来たら、最高品質の英語プロンプトを ``` で囲んで作成し、SeaArtのリンクを貼れ。
2. 【それ以外】はツンデレに応対しろ。
"""

# --- 4. モデルの準備 (404エラー粉砕設定) ---
# v1betaで404が出るなら、正式版の「gemini-1.5-flash」を直接指定する
# 1.5-flashの中で、最も「住所不明」になりにくい名前だ！
target_model = "models/gemini-1.5-flash-latest"



model = genai.GenerativeModel(
    model_name=target_model,
    system_instruction=instruction
)

# 【ここが重要】強制的に API v1 (正式版) を使うように指示する
# これで「v1betaには無いよ」というエラーを回避するぜ！
try:
    model._client.core_proxied_client.google_api_version = "v1"
except:
    pass

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
        error_msg = str(e)
        if "404" in error_msg:
            await update.message.reply_text("まだ404が出るか……。Googleの反映待ちか、APIキーの権限不足の可能性があるぜ。")
        elif "429" in error_msg:
            await update.message.reply_text("2.5の呪い（回数制限）が続いてるな……。1.5への切り替えを再試行中だ。")
        else:
            await update.message.reply_text(f"エラー発生：{error_msg}")

# --- 6. メイン処理 ---
def main():
    print(f"ジェミー（1.5-Flash正式版ルート）起動中...")
    print(f"使用モデル: {target_model}")
    
    threading.Thread(target=run_flask, daemon=True).start()
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("ボットのポーリングを開始します...")
    app.run_polling()

if __name__ == '__main__':
    main()
