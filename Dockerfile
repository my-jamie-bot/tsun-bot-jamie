# Pythonの軽量版をベースにする
FROM python:3.10-slim

# コンテナの中の作業場所を決める
WORKDIR /app

# 必要なファイルをコンテナの中にコピー
COPY gemini_bot.py .

# 必要なライブラリをインストール
RUN pip install --no-cache-dir python-telegram-bot google-generativeai

# ボットを実行！
CMD ["python", "gemini_bot.py"]
