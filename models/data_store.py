# -*- coding: utf-8 -*-
"""
データ管理（Firestore優先、ローカルJSONフォールバック）
"""

import json
from datetime import datetime
from copy import deepcopy

from pathlib import Path

from config import (
    DATA_DIR, DATA_FILE, SHIFTS_FILE,
    FIRESTORE_AVAILABLE, FIREBASE_KEY_FILE, DEFAULT_DATA,
    GOOGLE_CLOUD_PROJECT
)

if FIRESTORE_AVAILABLE:
    from google.cloud import firestore


def get_firestore_client():
    """Firestoreクライアントを取得"""
    if not FIRESTORE_AVAILABLE:
        return None
    try:
        # サービスアカウントキーファイルがあれば使用
        key_path = Path(FIREBASE_KEY_FILE)
        if key_path.exists():
            return firestore.Client.from_service_account_json(str(key_path))
        # プロジェクトIDを明示的に指定（ADC使用時）
        if GOOGLE_CLOUD_PROJECT:
            return firestore.Client(project=GOOGLE_CLOUD_PROJECT)
        return firestore.Client()
    except Exception as e:
        print(f"Firestore接続エラー: {e}")
        return None


def ensure_data_dir():
    """データディレクトリを作成"""
    DATA_DIR.mkdir(exist_ok=True)


# =============================================================================
# 設定データ管理
# =============================================================================

def load_data():
    """データを読み込む（Firestore優先、ローカルフォールバック）"""
    db = get_firestore_client()
    if db:
        try:
            doc = db.collection('settings').document('main').get()
            if doc.exists:
                return doc.to_dict()
        except Exception as e:
            print(f"Firestore読み込みエラー: {e}")

    # ローカルファイルにフォールバック
    ensure_data_dir()
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return deepcopy(DEFAULT_DATA)


def save_data(data):
    """データを保存（Firestoreとローカル両方）"""
    db = get_firestore_client()
    if db:
        try:
            db.collection('settings').document('main').set(data)
        except Exception as e:
            print(f"Firestore保存エラー: {e}")

    # ローカルにも保存（バックアップ）
    ensure_data_dir()
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_locations():
    data = load_data()
    return data.get('locations', [])


def set_locations(locations):
    data = load_data()
    data['locations'] = locations
    save_data(data)


def get_staff():
    data = load_data()
    return data.get('staff', [])


def set_staff(staff):
    data = load_data()
    data['staff'] = staff
    save_data(data)


def get_ng_days():
    data = load_data()
    return data.get('ng_days', {})


def set_ng_days(ng_days):
    data = load_data()
    data['ng_days'] = ng_days
    save_data(data)


def get_exceptions():
    data = load_data()
    return data.get('exceptions', {})


def set_exceptions(exceptions):
    data = load_data()
    data['exceptions'] = exceptions
    save_data(data)


# =============================================================================
# シフトデータ管理
# =============================================================================

def save_shift(year, month, shift_data, staff_counts, ng_days_data, exceptions_data):
    """シフトを保存"""
    db = get_firestore_client()
    doc_id = f"{year}-{month:02d}"

    shift_doc = {
        "year": year,
        "month": month,
        "shift_data": shift_data,
        "staff_counts": staff_counts,
        "ng_days": ng_days_data,
        "exceptions": exceptions_data,
        "created_at": firestore.SERVER_TIMESTAMP if db else datetime.now().isoformat(),
        "updated_at": firestore.SERVER_TIMESTAMP if db else datetime.now().isoformat()
    }

    if db:
        try:
            db.collection('shifts').document(doc_id).set(shift_doc)
            return True
        except Exception as e:
            print(f"シフト保存エラー: {e}")
            return False

    # ローカルフォールバック
    ensure_data_dir()
    shifts = {}
    if SHIFTS_FILE.exists():
        try:
            with open(SHIFTS_FILE, 'r', encoding='utf-8') as f:
                shifts = json.load(f)
        except:
            pass

    shift_doc['created_at'] = datetime.now().isoformat()
    shift_doc['updated_at'] = datetime.now().isoformat()
    shifts[doc_id] = shift_doc

    with open(SHIFTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(shifts, f, ensure_ascii=False, indent=2)
    return True


def load_shift(year, month):
    """シフトを読み込み"""
    db = get_firestore_client()
    doc_id = f"{year}-{month:02d}"

    if db:
        try:
            doc = db.collection('shifts').document(doc_id).get()
            if doc.exists:
                data = doc.to_dict()
                if data.get('created_at') and hasattr(data['created_at'], 'isoformat'):
                    data['created_at'] = data['created_at'].isoformat()
                if data.get('updated_at') and hasattr(data['updated_at'], 'isoformat'):
                    data['updated_at'] = data['updated_at'].isoformat()
                return data
        except Exception as e:
            print(f"シフト読み込みエラー: {e}")

    # ローカルフォールバック
    if SHIFTS_FILE.exists():
        try:
            with open(SHIFTS_FILE, 'r', encoding='utf-8') as f:
                shifts = json.load(f)
                return shifts.get(doc_id)
        except:
            pass
    return None


def delete_shift(year, month):
    """シフトを削除"""
    db = get_firestore_client()
    doc_id = f"{year}-{month:02d}"

    if db:
        try:
            db.collection('shifts').document(doc_id).delete()
            return True
        except Exception as e:
            print(f"シフト削除エラー: {e}")
            return False

    # ローカルフォールバック
    if SHIFTS_FILE.exists():
        try:
            with open(SHIFTS_FILE, 'r', encoding='utf-8') as f:
                shifts = json.load(f)
            if doc_id in shifts:
                del shifts[doc_id]
                with open(SHIFTS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(shifts, f, ensure_ascii=False, indent=2)
                return True
        except:
            pass
    return False


def list_shifts():
    """保存済みシフト一覧を取得"""
    db = get_firestore_client()
    shifts_list = []

    if db:
        try:
            docs = db.collection('shifts').order_by(
                'year', direction=firestore.Query.DESCENDING
            ).order_by(
                'month', direction=firestore.Query.DESCENDING
            ).stream()
            for doc in docs:
                data = doc.to_dict()
                shifts_list.append({
                    "id": doc.id,
                    "year": data.get('year'),
                    "month": data.get('month'),
                    "updated_at": data.get('updated_at').isoformat() if hasattr(data.get('updated_at'), 'isoformat') else data.get('updated_at')
                })
            return shifts_list
        except Exception as e:
            print(f"シフト一覧取得エラー: {e}")

    # ローカルフォールバック
    if SHIFTS_FILE.exists():
        try:
            with open(SHIFTS_FILE, 'r', encoding='utf-8') as f:
                shifts = json.load(f)
            for doc_id, data in shifts.items():
                shifts_list.append({
                    "id": doc_id,
                    "year": data.get('year'),
                    "month": data.get('month'),
                    "updated_at": data.get('updated_at')
                })
            shifts_list.sort(key=lambda x: (x['year'], x['month']), reverse=True)
        except:
            pass
    return shifts_list
