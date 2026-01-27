# -*- coding: utf-8 -*-
"""
アプリケーション設定
"""

import os
from datetime import timedelta
from pathlib import Path

# 基本設定
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
DATA_FILE = DATA_DIR / 'settings.json'
SHIFTS_FILE = DATA_DIR / 'shifts.json'

# Flask設定
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# セッション設定
SESSION_COOKIE_SECURE = False  # HTTPSでない場合はFalse
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
REMEMBER_COOKIE_DURATION = timedelta(days=7)

# 認証設定
APP_PASSWORD = os.environ.get('APP_PASSWORD', 'shift2026')

# Firestore設定
FIRESTORE_AVAILABLE = False
try:
    if os.environ.get('GOOGLE_CLOUD_PROJECT'):
        from google.cloud import firestore
        FIRESTORE_AVAILABLE = True
except ImportError:
    pass

# デフォルトデータ
DEFAULT_DATA = {
    "locations": [
        {
            "id": 1,
            "name": "FIP",
            "working_days": [0, 1, 2, 3, 4, 5, 6],
            "closed_days": [2, 3],
            "work_on_holidays": True,
            "min_staff": 1,
            "max_staff": 2,
            "part_time_priority": False,
            "flexible_staffing": False
        },
        {
            "id": 2,
            "name": "大宮",
            "working_days": [5, 6],
            "closed_days": [2, 3],
            "work_on_holidays": True,
            "min_staff": 1,
            "max_staff": 2,
            "part_time_priority": True,
            "flexible_staffing": True
        },
        {
            "id": 3,
            "name": "根岸",
            "working_days": [5, 6],
            "closed_days": [2, 3],
            "work_on_holidays": True,
            "min_staff": 1,
            "max_staff": 2,
            "part_time_priority": False,
            "flexible_staffing": False
        }
    ],
    "staff": [
        {"id": 1, "name": "田中太郎", "type": "社員", "max_days": 31, "assigned_locations": []},
        {"id": 2, "name": "鈴木花子", "type": "パート", "max_days": 12, "assigned_locations": [2]},
        {"id": 3, "name": "佐藤次郎", "type": "社員", "max_days": 31, "assigned_locations": []},
        {"id": 4, "name": "山田美咲", "type": "パート", "max_days": 10, "assigned_locations": [2]},
    ],
    "ng_days": {},
    "exceptions": {}
}
