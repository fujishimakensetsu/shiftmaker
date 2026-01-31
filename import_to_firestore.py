# -*- coding: utf-8 -*-
"""
ローカルJSONデータをFirestoreにインポートするスクリプト
"""

import json
import sys
from pathlib import Path

# .envを読み込み
from dotenv import load_dotenv
load_dotenv()

from google.cloud import firestore

# 設定
PROJECT_ID = 'shiftmakerai'
DATA_FILE = Path(__file__).parent / 'data' / 'settings.json'


def import_settings():
    """settings.jsonをFirestoreにインポート"""
    if not DATA_FILE.exists():
        print(f"エラー: {DATA_FILE} が見つかりません")
        return False

    # JSONデータを読み込み
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"読み込んだデータ:")
    print(f"  - 拠点数: {len(data.get('locations', []))}")
    print(f"  - スタッフ数: {len(data.get('staff', []))}")
    print(f"  - NG日設定: {len(data.get('ng_days', {}))}")
    print(f"  - 例外日設定: {len(data.get('exceptions', {}))}")

    # Firestoreクライアントを作成
    try:
        db = firestore.Client(project=PROJECT_ID)
        print(f"\nFirestore接続成功: プロジェクト={PROJECT_ID}")
    except Exception as e:
        print(f"Firestore接続エラー: {e}")
        return False

    # 既存データを確認
    doc_ref = db.collection('settings').document('main')
    existing_doc = doc_ref.get()

    if existing_doc.exists:
        print("\n既存のデータが見つかりました:")
        existing_data = existing_doc.to_dict()
        print(f"  - 拠点数: {len(existing_data.get('locations', []))}")
        print(f"  - スタッフ数: {len(existing_data.get('staff', []))}")

        response = input("\n既存データを上書きしますか？ (y/n): ")
        if response.lower() != 'y':
            print("インポートをキャンセルしました")
            return False

    # Firestoreに保存
    try:
        doc_ref.set(data)
        print("\nFirestoreへのインポートが完了しました！")
        return True
    except Exception as e:
        print(f"保存エラー: {e}")
        return False


def verify_import():
    """インポートされたデータを確認"""
    try:
        db = firestore.Client(project=PROJECT_ID)
        doc = db.collection('settings').document('main').get()

        if doc.exists:
            data = doc.to_dict()
            print("\n=== Firestoreのデータ確認 ===")
            print(f"拠点:")
            for loc in data.get('locations', []):
                print(f"  - {loc['name']} (ID: {loc['id']})")
            print(f"\nスタッフ:")
            for staff in data.get('staff', []):
                print(f"  - {staff['name']} ({staff['type']})")
            return True
        else:
            print("Firestoreにデータが見つかりません")
            return False
    except Exception as e:
        print(f"確認エラー: {e}")
        return False


if __name__ == '__main__':
    print("=== Firestore データインポートツール ===\n")

    if len(sys.argv) > 1 and sys.argv[1] == '--verify':
        verify_import()
    else:
        if import_settings():
            verify_import()
