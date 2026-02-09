# Procler

[English](README.md)

<p align="center">
  <img src="procler.png" alt="Procler logo" width="160" height="160" />
</p>

[![PyPI version](https://img.shields.io/pypi/v/procler.svg)](https://pypi.org/project/procler/)
[![Python versions](https://img.shields.io/pypi/pyversions/procler.svg)](https://pypi.org/project/procler/)
[![CI](https://github.com/gabu-quest/procler/actions/workflows/ci.yml/badge.svg)](https://github.com/gabu-quest/procler/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

**Claude Codeをファーストクラスシチズンとして設計されたプロセスマネージャー**

Proclerは、開発者（およびAIコーディングアシスタント）に、ローカルシェル、Dockerコンテナ、さまざまな実行コンテキストにまたがるモダンな開発環境の複雑さを一元管理するための統合インターフェースを提供します。

## 特徴

- **LLMファーストCLI** - Claude Code連携のために設計されたJSON出力コマンド
- **Webダッシュボード** - サイバーパンクデザインのVue 3ダッシュボード、リアルタイム更新
- **デュアルインターフェースの一貫性** - CLIとWeb UIは同じProcessManagerコアを共有
- **コンテキスト抽象化** - ローカルプロセスとDockerコンテナを統一的に管理
- **グループ＆レシピ** - 依存関係を持つマルチプロセスワークフローをオーケストレーション
- **ヘルスチェック** - HTTP/TCP/コマンドプローブによるプロセス監視
- **スニペット** - 再利用可能なコマンドをタグ付きで保存
- **リアルタイム更新** - WebSocketによるライブステータスとログストリーミング
- **設定変数** - config.yamlで`vars`を定義し、`${VAR}`で参照
- **プロセスレプリカ** - `replicas: N`で複数インスタンスを自動生成
- **名前空間** - プロセスのグルーピングとフィルタリング
- **スケジュール実行** - cron式による定期実行
- **メモリ閾値** - RSS超過時の自動再起動
- **エクスポート** - systemdユニット/Docker Compose形式に出力
- **インポート** - Procfileからの移行サポート
- **ターミナルUI** - Textualベースの対話型TUI

## 比較表

| 機能 | Procler | Process Compose | PM2 | Supervisord | Foreman |
|------|:-------:|:---------------:|:---:|:-----------:|:-------:|
| LLMファーストJSON CLI | ✅ | - | - | - | - |
| Webダッシュボード（無料） | ✅ | - | 有料 | - | - |
| Dockerコンテナ実行 | ✅ | - | 拡張 | - | - |
| ヘルスチェック | ✅ | ✅ | - | - | - |
| 依存関係付き起動 | ✅ | ✅ | - | - | - |
| `log_ready`条件 | ✅ | ✅ | - | - | - |
| マルチステップレシピ | ✅ | - | - | - | - |
| スニペット（コマンドライブラリ） | ✅ | - | - | - | - |
| 監査証跡 | ✅ | - | - | - | - |
| WebSocketリアルタイム | ✅ | - | - | - | - |
| 設定説明（LLM） | ✅ | - | - | - | - |
| メモリ閾値再起動 | ✅ | - | ✅ | - | - |
| HTTP/TCPレディネスプローブ | ✅ | ✅ | - | - | - |
| systemdエクスポート | ✅ | - | - | - | ✅ |
| cron/スケジュール実行 | ✅ | ✅ | - | - | - |
| プロセスレプリカ | ✅ | ✅ | ✅ | - | - |
| Procfileインポート | ✅ | - | - | - | ✅ |
| TUIモード | ✅ | ✅ | - | - | - |
| 言語非依存 | ✅ | ✅ | Node.js | Python | Ruby |

## インストール

```bash
# 推奨: グローバルツールとしてインストール
uv tool install procler

# TUIサポート付き（ターミナルUI）
uv tool install procler[tui]

# またはpip経由
pip install procler
pip install procler[tui]  # TUI付き
```

ソースからインストール:

```bash
git clone https://github.com/gabu-quest/procler.git
cd procler
uv sync --all-extras
```

> **注意:** フロントエンドはビルド済みで同梱されています。別途ビルドは不要です！

## クイックスタート

### 設定の初期化

```bash
# .procler/ 設定ディレクトリを作成
procler config init

# 設定を検証
procler config validate

# 設定の説明を取得（LLMフレンドリー）
procler config explain
```

### プロセス管理

```bash
# プロセスを定義
procler define --name my-api --command "uvicorn main:app --port 8000"

# 起動
procler start my-api

# ステータス確認（JSON出力）
procler status my-api

# ログを表示
procler logs my-api --tail 50 --since 5m

# 停止
procler stop my-api

# 再起動（ログクリアオプション付き）
procler restart my-api --clear-logs
```

### Dockerプロセス

```bash
# Dockerコンテナ内で実行するプロセスを定義
procler define \
  --name db-migrate \
  --command "alembic upgrade head" \
  --context docker \
  --container api-container

# コンテナ内で任意のコマンドを実行
procler exec "pip list" --context docker --container api-container
```

### グループ＆レシピ

```bash
# グループ内のすべてのプロセスを起動（順序と依存関係を考慮）
procler group start backend

# 逆順で停止
procler group stop backend

# レシピを実行前にプレビュー
procler recipe run deploy --dry-run

# レシピを実行
procler recipe run deploy
```

### 変数置換

`.procler/config.yaml`で変数を定義し、コマンドやコンテナ名で参照:

```yaml
vars:
  SIM_CONTAINER: my-sim-container
  SIM_USER: "1000"
  SIM_WORKDIR: /opt/sim

processes:
  simulator:
    command: "${SIM_WORKDIR}/bin/simulator"
    context: docker
    container: "${SIM_CONTAINER}"
```

### スニペット（再利用可能なコマンド）

```bash
# スニペットを保存
procler snippet save \
  --name rebuild-api \
  --command "docker compose build api" \
  --tags docker,build

# スニペット一覧（タグフィルター付き）
procler snippet list --tag docker

# スニペットを実行
procler snippet run rebuild-api
```

### エクスポート

```bash
# systemdユニットファイルとしてエクスポート
procler export systemd my-api

# 全ローカルプロセスをsystemdユニットとしてエクスポート
procler export systemd --all

# docker-compose.ymlとしてエクスポート
procler export compose
```

### インポート

```bash
# Procfileからインポート
procler import procfile Procfile

# プレビューのみ（書き込みなし）
procler import procfile Procfile --dry-run

# 既存設定にマージ
procler import procfile Procfile --merge
```

### ターミナルUI

```bash
# 対話型TUIを起動（procler[tui]が必要）
procler tui
```

### Webサーバー

```bash
# APIサーバーを起動
procler serve --host 0.0.0.0 --port 8000

# ホットリロードで開発
procler serve --reload
```

## CLIリファレンス

すべてのCLIコマンドは、スクリプトやLLMで簡単にパースできる構造化JSONを返します。

### 検出・設定コマンド

| コマンド | 説明 |
|---------|------|
| `procler capabilities` | 全コマンドのJSONスキーマを返す（LLM検出用） |
| `procler help-llm` | LLM向けの包括的な使用方法を出力 |
| `procler config init [--force]` | `.procler/`設定ディレクトリをテンプレートで初期化 |
| `procler config validate` | config.yamlの構文と参照を検証 |
| `procler config path` | 解決済みの設定ディレクトリパスを表示 |
| `procler config explain` | 設定を平易な言葉で説明（LLMフレンドリー） |

### プロセスコマンド

| コマンド | 説明 |
|---------|------|
| `procler define --name NAME --command CMD [オプション]` | 新しいプロセスを定義 |
| `procler start NAME` | プロセスを起動（冪等） |
| `procler stop NAME` | プロセスを停止（冪等） |
| `procler restart NAME [--clear-logs]` | プロセスを再起動 |
| `procler status [NAME]` | ステータスを表示（全体または単一） |
| `procler list [--resolve] [--namespace NS]` | 全プロセス定義を一覧表示 |
| `procler remove NAME` | プロセス定義を削除 |
| `procler logs NAME [--tail N] [--since TIME] [-f]` | ログを取得/フォロー |
| `procler exec "CMD" [--context TYPE] [--container NAME]` | 単発コマンドを実行 |

### グループコマンド

| コマンド | 説明 |
|---------|------|
| `procler group list` | 設定で定義された全グループを一覧表示 |
| `procler group start NAME` | 全プロセスを順番に起動 |
| `procler group stop NAME` | 全プロセスを逆順/カスタム順で停止 |
| `procler group status NAME` | グループ内全プロセスのステータスを取得 |

### レシピコマンド

| コマンド | 説明 |
|---------|------|
| `procler recipe list` | 設定で定義された全レシピを一覧表示 |
| `procler recipe show NAME` | レシピの詳細とステップを表示 |
| `procler recipe run NAME [--dry-run] [--continue-on-error]` | レシピを実行 |

### スニペットコマンド

| コマンド | 説明 |
|---------|------|
| `procler snippet list [--tag TAG]` | 全スニペットを一覧表示 |
| `procler snippet show NAME` | スニペットの詳細を表示 |
| `procler snippet save --name NAME --command CMD [オプション]` | 新しいスニペットを保存 |
| `procler snippet run NAME` | 保存済みスニペットを実行 |
| `procler snippet remove NAME` | スニペットを削除 |

### エクスポートコマンド

| コマンド | 説明 |
|---------|------|
| `procler export systemd NAME` | systemd .serviceユニットファイルとしてエクスポート |
| `procler export systemd --all` | 全ローカルプロセスをsystemdユニットとしてエクスポート |
| `procler export compose` | docker-compose.ymlとしてエクスポート |

### インポートコマンド

| コマンド | 説明 |
|---------|------|
| `procler import procfile PATH [--dry-run] [--merge]` | Procfileからプロセスをインポート |

### TUIコマンド

| コマンド | 説明 |
|---------|------|
| `procler tui` | 対話型ターミナルUIを起動（`procler[tui]`が必要） |

### サーバーコマンド

| コマンド | 説明 |
|---------|------|
| `procler serve [--host HOST] [--port PORT] [--reload]` | Webサーバーを起動 |

## 設定

Proclerはプロジェクトごとに`.procler/`ディレクトリを使用します:

```
.procler/
├── config.yaml    # 定義（gitにコミット）
├── changelog.log  # 監査証跡（gitにコミット）
└── state.db       # ランタイム状態（自動gitignore）
```

**検出順序:** `$PROCLER_CONFIG_DIR` → `.procler.env` → `.procler/` → gitルート → `~/.procler/`

### 設定例

```yaml
version: 1

vars:
  API_PORT: "8000"
  DB_CONTAINER: postgres-dev

processes:
  api:
    command: uvicorn main:app --reload --port ${API_PORT}
    context: local
    cwd: /path/to/project
    tags: [backend, api]
    description: "APIサーバー"
    namespace: backend                    # 名前空間による分離
    ready_log_line: "Uvicorn running on"  # log_ready条件用の正規表現
    max_memory: 512M                      # RSS超過時に自動再起動
    healthcheck:
      http_get: "http://localhost:${API_PORT}/health"  # HTTPプローブ（curl不要）
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s

  worker:
    command: celery worker -A tasks
    context: local
    namespace: backend
    replicas: 3                           # 3インスタンス起動（worker-1, worker-2, worker-3）
    depends_on:
      - redis
      - name: api
        condition: log_ready              # ready_log_lineのマッチを待機
      - name: db
        condition: healthy                # ヘルスチェック合格を待機

  db:
    command: postgres
    healthcheck:
      tcp_socket: "localhost:5432"        # TCPプローブ
      interval: 5s
      timeout: 3s

  cleanup:
    command: python scripts/cleanup.py
    schedule: "0 */6 * * *"              # cron: 6時間ごと

  db-migrate:
    command: alembic upgrade head
    context: docker
    container: ${DB_CONTAINER}

groups:
  backend:
    description: "フルバックエンドスタック"
    processes: [redis, db, api, worker]
    stop_order: [worker, api, db, redis]  # カスタム停止順序（オプション）

recipes:
  deploy:
    description: "グレースフルデプロイ"
    on_error: stop  # または continue
    steps:
      - stop: worker
      - stop: api
      - wait: 2s
      - exec: "alembic upgrade head"
        context: docker
        container: ${DB_CONTAINER}
      - start: api
      - start: worker

snippets:
  rebuild:
    command: docker compose build
    description: "コンテナを再ビルド"
    tags: [docker]
```

### 新しい設定機能

#### 依存関係条件

```yaml
depends_on:
  - redis                        # condition: started（デフォルト）
  - name: api
    condition: healthy            # ヘルスチェック合格を待機
  - name: db
    condition: log_ready          # ready_log_lineの正規表現マッチを待機
```

#### ヘルスチェックプローブ

3種類のプローブ（healthcheckごとに1つ使用）:

```yaml
healthcheck:
  test: "curl -f http://localhost:8000/health"  # コマンドプローブ
  # または
  http_get: "http://localhost:8000/health"      # HTTP GETプローブ（組み込み）
  # または
  tcp_socket: "localhost:5432"                  # TCPソケットプローブ（組み込み）
  interval: 10s
  timeout: 5s
  retries: 3
```

#### プロセスレプリカ

```yaml
processes:
  worker:
    command: celery worker
    replicas: 3  # worker-1, worker-2, worker-3を作成
    # 各レプリカにPROCLER_REPLICA_INDEX環境変数が設定される（1, 2, 3）
```

#### メモリ閾値

```yaml
processes:
  api:
    command: uvicorn main:app
    max_memory: 512M  # RSS超過時に自動再起動（K, M, Gサポート）
```

#### スケジュール実行

```yaml
processes:
  cleanup:
    command: python cleanup.py
    schedule: "0 */6 * * *"  # cron式
```

#### 名前空間

```yaml
processes:
  api:
    command: uvicorn main:app
    namespace: project-a  # デフォルト: "default"
```

名前空間でフィルタリング: `procler list --namespace project-a`

## CLI出力フォーマット

すべてのCLIコマンドは構造化JSONを返します:

### 成功レスポンス

```json
{
  "success": true,
  "data": {
    "processes": [
      {
        "name": "my-api",
        "status": "running",
        "pid": 12345,
        "uptime_seconds": 3600
      }
    ]
  }
}
```

### エラーレスポンス

```json
{
  "success": false,
  "error": "Container 'db-postgres' not found",
  "error_code": "container_not_found",
  "suggestion": "Run 'docker ps -a' to list available containers"
}
```

## REST API

ベースURL: `http://localhost:8000/api`

| エンドポイント | メソッド | 説明 |
|--------------|--------|------|
| `/api/processes` | GET | 全プロセス一覧 |
| `/api/processes` | POST | プロセス作成 |
| `/api/processes/{name}` | GET | プロセス取得 |
| `/api/processes/{name}` | DELETE | プロセス削除 |
| `/api/processes/{name}/start` | POST | プロセス起動 |
| `/api/processes/{name}/stop` | POST | プロセス停止 |
| `/api/processes/{name}/restart` | POST | プロセス再起動 |
| `/api/logs/{name}` | GET | ログ取得 (?tail=100&since=5m) |
| `/api/groups` | GET | 全グループ一覧 |
| `/api/groups/{name}/start` | POST | グループ起動 |
| `/api/groups/{name}/stop` | POST | グループ停止 |
| `/api/groups/{name}/status` | GET | グループステータス |
| `/api/recipes` | GET | 全レシピ一覧 |
| `/api/recipes/{name}/run` | POST | レシピ実行 |
| `/api/snippets` | GET | スニペット一覧 (?tag=filter) |
| `/api/snippets` | POST | スニペット作成 |
| `/api/snippets/{name}` | GET | スニペット取得 |
| `/api/snippets/{name}` | DELETE | スニペット削除 |
| `/api/snippets/{name}/run` | POST | スニペット実行 |
| `/api/config` | GET | 設定ステータス |
| `/api/config/reload` | POST | 設定リロード |
| `/api/config/export/{format}` | GET | 設定エクスポート（systemd, compose） |
| `/api/health` | GET | ヘルスチェック |

## WebSocket

リアルタイム更新用に `ws://localhost:8000/api/ws` に接続します。

```javascript
// プロセスのログを購読
ws.send(JSON.stringify({action: "subscribe_logs", process_id: 1}));

// ステータス更新を購読（全プロセス）
ws.send(JSON.stringify({action: "subscribe_status"}));

// 更新を受信
// {"type": "log", "process_id": 1, "data": {"line": "...", "stream": "stdout"}}
// {"type": "status", "process_id": 1, "data": {"status": "running", "pid": 123}}
```

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| バックエンド | Python 3.12+, FastAPI |
| データベース | SQLite ([sqler](https://pypi.org/project/sqler/)経由) |
| フロントエンド | Vue 3, Vite, Pinia, Naive UI |
| CLI | Click |
| Docker | docker-py SDK |
| リアルタイム | WebSockets |

## 開発

```bash
# 開発依存関係をインストール
uv sync --all-extras

# テスト実行（320+テスト）
uv run pytest -v

# 開発でCLIを実行
uv run procler --help

# ホットリロードでサーバーを実行
uv run procler serve --reload

# フロントエンドを再ビルド（Vueコードを変更した場合のみ）
bash scripts/build_frontend.sh
```

### Pre-commitフック

このプロジェクトはコード品質のためにpre-commitフックを使用しています:

```bash
pre-commit install
```

フックはコミットごとにruffでリンティングとフォーマットを実行します。

## Webダッシュボード

Vue 3フロントエンドは、プロセスとスニペットを管理するためのビジュアルインターフェースを提供します:

- **ダッシュボード** - リアルタイムステータスで全プロセスを概観
- **プロセス一覧** - 全定義済みプロセスを表示、起動/停止/再起動コントロール、アクション別ローディング状態
- **プロセス詳細** - WebSocketによるライブログストリーミング、検索/フィルター、ストリームフィルタリング
- **グループ** - ワンクリックで全起動/停止できるカードベースビュー
- **レシピ** - ステッププレビュー、ドライラン、実行進捗
- **スニペット** - 再利用可能なコマンドの保存、管理、実行（確認付き）
- **設定** - ステータス、統計、変数表示、変更履歴ビューア

### キーボードショートカット

`?`を押すと全ショートカットを表示。クイックナビゲーション:
- `g d` - ダッシュボード
- `g p` - プロセス
- `g g` - グループ
- `g r` - レシピ
- `g s` - スニペット
- `g c` - 設定
- `g a` - About

### UX機能

- **接続ステータス** - ヘッダーのWebSocketインジケーターで接続/接続中/エラー状態を表示
- **トースト通知** - プロセスのステータス変化時に自動通知
- **ログ検索** - テキスト（マッチハイライト付き）またはストリーム（stdout/stderr）でフィルター
- **パンくずリスト** - 詳細ページでのナビゲーションコンテキスト
- **確認ダイアログ** - 破壊的な操作は確認が必要

### ダッシュボードの実行

```bash
# サーバーを起動（APIとWeb UIの両方を提供）
uv run procler serve --port 8000
```

http://localhost:8000 を開いてダッシュボードにアクセス。

> **フロントエンド開発:** Vue開発では `cd frontend && npm run dev`（ポート5173でdevサーバー）を実行し、`bash scripts/build_frontend.sh` で再ビルド

## Claude Code連携

ProclerはAIアシスタントとのシームレスな連携のために設計されています:

```
Human: "auth-apiが遅いようです。最近のログを確認して、エラーがあれば再起動してください"

Claude Code:
1. procler logs auth-api --tail 100
2. [JSONログ出力を分析]
3. procler restart auth-api
4. procler status auth-api
5. 結果を報告
```

## 環境変数

| 変数 | デフォルト | 説明 |
|-----|----------|------|
| `PROCLER_LOG_LEVEL` | `INFO` | ログレベル (DEBUG, INFO, WARNING, ERROR) |
| `PROCLER_LOG_FILE` | - | ログファイルパス（自動ローテーション） |
| `PROCLER_CONFIG_DIR` | `.procler/` | 設定ディレクトリ |
| `PROCLER_DB_PATH` | `.procler/state.db` | データベースパス |
| `PROCLER_CORS_ORIGINS` | `localhost` | 許可されたオリジン（カンマ区切り） |
| `PROCLER_DEBUG` | - | 詳細なエラーメッセージを有効化 |

## ライセンス

MIT
