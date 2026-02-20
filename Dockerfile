# Pythonの軽量版をベースにする
FROM python:3.10-slim

# コンテナの中の作業場所を決める
WORKDIR /app

# 1. 最初に requirements.txt だけコピー（効率化のため）
COPY requirements.txt .

# 2. requirements.txt に書いてある道具（flask, telegram, ai）を全部インストール！
RUN pip install --no-cache-dir -r requirements.txt

# 3. プログラム本体をコピー
COPY . .

# ボットを実行！
CMD ["python", "gemini_bot.py"]
