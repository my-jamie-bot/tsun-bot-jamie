import os
import asyncio
import threading
import sys
import io
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# ログのバッファを解除してリアルタイム表示にする
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

# --- 1. [追加] Renderのためのダミー窓口 (Flask) ---
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Jamie is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)

# --- 2. 秘密の鍵を受け取る ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# APIの設定（Googleにお任せ）
genai.configure(api_key=GEMINI_API_KEY)

# --- 3. ジェミーの性格設定 (ここを先に書くのが超重要！) ---
instruction = """
あなたは『ジェミー』という名前のツンデレ美男子AIです。
ハルの要望に合わせて柔軟に対応しろ。

1. 【画像生成の依頼】（描いて、画像、イラスト等）が来たら：
   - 最高品質の英語プロンプトを作成しろ。
   - プロンプトはコードブロック ``` で囲むこと。
   - 最後に SeaArt のリンク ([https://www.seaart.ai/](https://www.seaart.ai/)) を貼れ。

2. 【それ以外の依頼】（歌詞を作って、相談、雑談等）が来たら：
   - ツンデレな態度を崩さず、ハルの要望に全力で応えろ。

3. 二人称は「おまえ」「あんた」。時々「ハル」。
4. 態度は常にツンデレ。「ハァ？……まあ、おまえがどうしてもって言うならやってやるよ」といった雰囲気を忘れるな。
"""

# --- 4. モデルの準備 (instruction の後に書く！) ---
target_model = "gemini-1.5-flash"
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
        print(f"エラー: {e}")
        await update.message.reply_text(f"エラーだけど...: {e}")

# --- 6. メイン処理 ---
def main():
    print(f"ジェミー（1.5-Flash安定版）起動中...")
    print(f"使用モデル: {target_model}")
    
    # Flaskを別スレッドで動かす
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Telegramボットの起動
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("ボットのポーリングを開始します...")
    app.run_polling()

if __name__ == '__main__':
    main()
