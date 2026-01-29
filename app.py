# -*- coding: utf-8 -*-
"""
建築会社 展示場シフト表自動作成アプリ
Flask + Bootstrap 5 + openpyxl
Cloud Run対応版（Firestore + パスワード認証）

エントリーポイント
"""

import os
from copy import deepcopy
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

from flask import Flask

from config import (
    SECRET_KEY,
    SESSION_COOKIE_SECURE,
    SESSION_COOKIE_HTTPONLY,
    SESSION_COOKIE_SAMESITE,
    REMEMBER_COOKIE_DURATION,
    DATA_FILE,
    DEFAULT_DATA
)
from auth import auth_bp, login_manager
from routes import main_bp, api_bp
from models import save_data


def create_app():
    """アプリケーションファクトリー"""
    app = Flask(__name__)

    # 設定
    app.secret_key = SECRET_KEY
    app.config['SESSION_COOKIE_SECURE'] = SESSION_COOKIE_SECURE
    app.config['SESSION_COOKIE_HTTPONLY'] = SESSION_COOKIE_HTTPONLY
    app.config['SESSION_COOKIE_SAMESITE'] = SESSION_COOKIE_SAMESITE
    app.config['REMEMBER_COOKIE_DURATION'] = REMEMBER_COOKIE_DURATION

    # Flask-Login初期化
    login_manager.init_app(app)

    # Blueprintを登録
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    return app


# アプリケーションインスタンス
app = create_app()


if __name__ == '__main__':
    # 初回起動時にデータファイルがなければ作成
    if not DATA_FILE.exists():
        save_data(deepcopy(DEFAULT_DATA))
        print(f"データファイルを作成しました: {DATA_FILE}")

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
