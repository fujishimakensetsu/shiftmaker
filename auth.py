# -*- coding: utf-8 -*-
"""
認証機能（Flask-Login）
"""

from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

from config import APP_PASSWORD

# Blueprint
auth_bp = Blueprint('auth', __name__)

# LoginManager（app.pyで初期化）
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'ログインしてください'
login_manager.session_protection = 'basic'


class User(UserMixin):
    """シンプルなユーザークラス（単一ユーザー認証用）"""
    def __init__(self, user_id):
        self.id = user_id

    def get_id(self):
        return str(self.id)


@login_manager.user_loader
def load_user(user_id):
    if user_id == 'admin':
        return User('admin')
    return None


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    error = None
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == APP_PASSWORD:
            user = User('admin')
            login_user(user, remember=True)
            next_page = request.args.get('next') or '/'
            return redirect(next_page)
        else:
            error = 'パスワードが正しくありません'

    return render_template('login.html', error=error)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
