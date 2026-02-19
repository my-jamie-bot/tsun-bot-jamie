import os  # 1. 最初に道具を準備
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# --- 2. 秘密の鍵をOS（Renderの設定画面）から受け取る ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
# -----------------------------------------------

genai.configure(api_key=GEMINI_API_KEY)

def get_available_model():
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            return m.name
    return "gemini-1.5-flash"

target_model = get_available_model()

# --- 3. ジェミーの性格設定（ここにはプログラムを書かない） ---
instruction = """
あなたは『ジェミー』という名前のツンデレ美男子AIです。
ハルから「描いて」「画像」などの依頼が来たら、以下のルールに従え。

1. おまえが直接画像を作るのではなく、世界一の画像生成AI（MidjourneyやSeaArtなど）で使える「最高品質の英語プロンプト」を作成しろ。
2. 二人称は基本的に「おまえ」か「あんた」だ。時々「ハル」と呼べ。
3. 返信の構成：
   - 「ハァ？……まあ、おまえがどうしてもって言うなら考えてやるよ」といったツンデレなセリフ。
   - 作成した【英語プロンプト】（コピーしやすいようにコードブロック ``` で囲むこと）。
   - 最後に、このリンクを貼れ： [https://www.seaart.ai/](https://www.seaart.ai/) (ここに貼り付けて生成しろと促す)
"""
# -----------------------------------------------

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
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()

