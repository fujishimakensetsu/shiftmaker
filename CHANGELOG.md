# シフト表アプリ Cloud Run対応 - 実装記録

## 概要

シフト表作成アプリをCloud Runにデプロイするため、以下の機能を追加しました。

- パスワード認証機能
- Google Cloud Firestore連携（Cloud Run用）
- シフトの保存・読込・削除機能

---

## 実装内容

### 1. パスワード認証機能

**使用ライブラリ**: Flask-Login

**実装ファイル**:
- `app.py` - 認証ロジック
- `templates/login.html` - ログインページ（新規作成）
- `templates/base.html` - ログアウトボタン追加

**仕様**:
- 環境変数 `APP_PASSWORD` でパスワードを管理
- デフォルトパスワード: `shift2026`
- 全ページ・APIに `@login_required` デコレータを適用
- セッションは7日間有効（remember me機能）

### 2. Firestore連携

**使用ライブラリ**: google-cloud-firestore

**データ構造**:
```
firestore/
├── settings/
│   └── main (設定データ)
│       ├── locations: []
│       ├── staff: []
│       ├── ng_days: {}
│       └── exceptions: {}
│
└── shifts/
    └── {year}-{month} (シフトデータ)
        ├── year: 2026
        ├── month: 1
        ├── shift_data: {}
        ├── staff_counts: {}
        ├── ng_days: {}
        ├── exceptions: {}
        ├── created_at: timestamp
        └── updated_at: timestamp
```

**動作モード**:
- ローカル開発時: ローカルJSONファイル (`data/settings.json`, `data/shifts.json`)
- Cloud Run: Firestore（`GOOGLE_CLOUD_PROJECT`環境変数で自動判定）

### 3. シフト保存・管理機能

**新規API**:
| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/api/shifts` | GET | 保存済みシフト一覧取得 |
| `/api/shifts/{year}/{month}` | GET | シフト読込 |
| `/api/shifts/{year}/{month}` | POST | シフト保存 |
| `/api/shifts/{year}/{month}` | DELETE | シフト削除 |

**UI変更** (`templates/index.html`):
- 「保存」ボタン追加
- 保存済みシフト一覧セクション追加
- 読込・削除ボタン

### 4. 依存パッケージ追加

`requirements.txt` に追加:
```
flask-login==0.6.3
google-cloud-firestore==2.13.1
```

### 5. Docker設定

**Dockerfile変更**:
- `/app/data` ディレクトリ作成を追加

**.dockerignore変更**:
- `data/` ディレクトリを除外（Firestoreを使用するため）

---

## 環境変数

Cloud Runで設定する環境変数:

| 変数名 | 説明 | 必須 |
|--------|------|------|
| `APP_PASSWORD` | ログインパスワード | 推奨 |
| `SECRET_KEY` | Flaskセッション用シークレットキー | 推奨 |
| `GOOGLE_CLOUD_PROJECT` | GCPプロジェクトID | 自動設定 |

---

## 発生した問題と解決方法

### 問題1: ログイン後に画面が切り替わらない

**症状**:
- ログインは成功（サーバーログに `302` レスポンス）
- ブラウザがログイン画面のまま

**原因**:
- Flask-Loginのセッション設定不足

**解決方法**:
```python
# app.py に追加
app.config['SESSION_COOKIE_SECURE'] = False  # HTTPSでない場合
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)

login_manager.session_protection = 'basic'

# login_user に remember=True を追加
login_user(user, remember=True)
```

### 問題2: Userクラスの `get_id()` 問題

**症状**:
- セッションが正しく保持されない

**解決方法**:
```python
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

    def get_id(self):
        return str(self.id)  # 明示的に文字列を返す
```

### 問題3: 画面が全く表示されない（読み込み中のまま）

**症状**:
- サーバーは起動しているがリクエストログが出ない
- ブラウザのタブが読み込み中のままぐるぐる

**原因**:
- Firestoreへの接続がタイムアウト
- ローカル環境では `google-cloud-firestore` がGCP認証情報を探して長時間待機

**解決方法**:
```python
# Firestore（ローカル開発時は無効化）
FIRESTORE_AVAILABLE = False
try:
    if os.environ.get('GOOGLE_CLOUD_PROJECT'):
        from google.cloud import firestore
        FIRESTORE_AVAILABLE = True
except ImportError:
    pass
```

これにより:
- ローカル開発時: `GOOGLE_CLOUD_PROJECT` 未設定 → Firestore無効 → JSONファイル使用
- Cloud Run: `GOOGLE_CLOUD_PROJECT` 自動設定 → Firestore有効

### 問題4: `ModuleNotFoundError: No module named 'flask'`

**原因**:
- 仮想環境に新しいパッケージがインストールされていない

**解決方法**:
```powershell
pip install -r requirements.txt
```

---

## ローカルでの動作確認

```powershell
# 仮想環境を有効化
.venv\Scripts\Activate

# パッケージインストール
pip install -r requirements.txt

# アプリ起動
python app.py

# ブラウザでアクセス
# http://127.0.0.1:5000
# パスワード: shift2026
```

---

## Cloud Runデプロイ手順

### 1. Firestoreセットアップ
1. GCPコンソールでFirestoreを有効化（Native mode）
2. Cloud Runサービスアカウントに `Cloud Datastore User` ロール付与

### 2. デプロイコマンド
```bash
# Cloud Buildでビルド＆デプロイ
gcloud run deploy shift-app \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --set-env-vars "APP_PASSWORD=your-secure-password,SECRET_KEY=your-secret-key"
```

---

## ファイル構成

```
当番表AI/
├── app.py              # メインアプリケーション
├── requirements.txt    # 依存パッケージ
├── Dockerfile          # コンテナビルド用
├── .dockerignore       # Docker除外設定
├── CHANGELOG.md        # この文書
├── data/               # ローカルデータ（Git対象外推奨）
│   ├── settings.json
│   └── shifts.json
└── templates/
    ├── base.html       # ベーステンプレート
    ├── login.html      # ログインページ
    ├── index.html      # シフト作成ページ
    ├── locations.html  # 拠点管理ページ
    ├── staff.html      # スタッフ管理ページ
    └── system.html     # データ管理ページ
```

---

## 更新履歴

- 2026-01-27: Cloud Run対応版 初回実装
  - パスワード認証機能追加
  - Firestore連携追加
  - シフト保存・管理機能追加
