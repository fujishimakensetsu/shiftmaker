# Python 3.11をベースイメージとして使用
FROM python:3.11-slim

# 環境変数設定
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

# 作業ディレクトリ設定
WORKDIR /app

# システム依存パッケージのインストール（日本語フォント含む）
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-ipaexfont \
    fontconfig \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -fv

# Pythonパッケージのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# データディレクトリを作成
RUN mkdir -p /app/data

# 非rootユーザーで実行（セキュリティ）
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# ポート公開
EXPOSE 8080

# アプリケーション起動
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "0", "app:app"]
