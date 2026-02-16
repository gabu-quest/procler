# Procler

**[English](README.md) | 日本語**

<p align="center">
  <img src="procler.png" alt="Procler logo" width="160" height="160" />
</p>

[![PyPI version](https://img.shields.io/pypi/v/procler.svg)](https://pypi.org/project/procler/)
[![Python versions](https://img.shields.io/pypi/pyversions/procler.svg)](https://pypi.org/project/procler/)
[![CI](https://github.com/gabu-quest/procler/actions/workflows/ci.yml/badge.svg)](https://github.com/gabu-quest/procler/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

**Claude Codeをファーストクラスシチズンとして設計されたプロセスマネージャー**

すべてのコマンドが構造化JSONを返します。すべてのエラーに機械可読なコードと修正提案が含まれます。AIアシスタントが開発環境を管理するワークフローのために設計されています。

## クイックスタート

```bash
uv tool install procler

procler define --name api --command "uvicorn main:app --port 8000"
procler start api
procler status api       # JSON: pid, uptime, linux_state
procler logs api --tail 20
procler stop api
```

## なぜProcler？

モダンな開発環境では、ローカルサーバー、Dockerコンテナ、バックグラウンドワーカー、データベースマイグレーションを同時に管理する必要があります。Proclerは、それらすべてを一つのツールで管理します — LLMがパースできるJSON出力、依存サービスをブロックするヘルスチェック、マルチステップワークフローを自動化するレシピを備えています。

## 特徴

**コア** — ローカルとDockerの実行コンテキストによるプロセスライフサイクル管理、ログキャプチャ、PIDトラッキング、Linuxカーネルステート検出（`/proc`統合）。

**オーケストレーション** — 依存関係付き起動順序のグループ（`depends_on`で`healthy`/`log_ready`条件）、ドライランプレビュー付きマルチステップレシピ、cronスケジュール実行、プロセスレプリカ。

**モニタリング** — HTTP/TCP/コマンドヘルスプローブ、メモリ閾値自動再起動、`ready_log_line`正規表現マッチング、リアルタイムWebSocketステータスとログストリーミング。

**開発者体験** — JSON出力CLI、`error_code` + `suggestion`付き構造化エラー、設定変数置換（`${VAR}`）、Procfileインポート、systemd/Composeエクスポート、コマンドスニペット、Vue 3 Webダッシュボード、Textual TUI。

## いつProclerを使うべきか

**適している場合:**
- マルチサービス開発環境（API + ワーカー + DB + キャッシュ）
- ローカル + Docker混在ワークフロー
- AI支援開発（Claude Code、Cursorなど）
- 開発プロセスをコードで管理したいチーム

**代替ツールを検討すべき場合:**
- 単一プロセスの監視のみ — OSのプロセスマネージャーを使用
- Kubernetesクラスター — Helm/ArgoCDを使用
- 複数マシンのオーケストレーション — NomadまたはDocker Swarmを使用
- 本番デプロイのみ — systemdを直接使用（Proclerからエクスポート可能）

## 比較表

| 機能 | Procler | Process Compose | PM2 | Supervisord | Foreman |
|------|:-------:|:---------------:|:---:|:-----------:|:-------:|
| LLMファーストJSON CLI | **yes** | - | - | - | - |
| Webダッシュボード（無料） | **yes** | - | 有料 | - | - |
| Dockerコンテナ実行 | **yes** | - | 拡張 | - | - |
| ヘルスチェック（HTTP/TCP/cmd） | **yes** | **yes** | - | - | - |
| 依存関係付き起動 | **yes** | **yes** | - | - | - |
| `log_ready`条件 | **yes** | **yes** | - | - | - |
| マルチステップレシピ | **yes** | - | - | - | - |
| コマンドスニペット | **yes** | - | - | - | - |
| cronスケジュール | **yes** | **yes** | - | - | - |
| プロセスレプリカ | **yes** | **yes** | **yes** | - | - |
| メモリ閾値再起動 | **yes** | - | **yes** | - | - |
| systemd/Composeエクスポート | **yes** | - | - | - | **yes** |
| Procfileインポート | **yes** | - | - | - | **yes** |
| TUIモード | **yes** | **yes** | - | - | - |
| 監査証跡 | **yes** | - | - | - | - |
| 言語非依存 | **yes** | **yes** | Node.js | Python | Ruby |

## ショーケース

### [C01] 基本的なプロセスライフサイクル

```bash
$ procler define --name my-api --command "sleep 60"
{
  "success": true,
  "data": {"action": "created", "process": {"name": "my-api", ...}}
}

$ procler start my-api
{
  "success": true,
  "data": {"status": "started", "process": {"status": "running", "pid": 12345}}
}

$ procler status my-api
{
  "success": true,
  "data": {"process": {"name": "my-api", "status": "running", "pid": 12345, "uptime_seconds": 5}}
}

$ procler stop my-api
{"success": true, "data": {"status": "stopped"}}
```

### [C02] JSONレスポンス規約

すべてのCLIコマンドはこのエンベロープを返します:

```json
{"success": true, "data": {"..."}}
```

### [C03] エラーレスポンス規約

すべてのエラーに `error_code` と `suggestion` が含まれます:

```json
{
  "success": false,
  "error": "Process 'api' not found",
  "error_code": "process_not_found",
  "suggestion": "Run 'procler list' to see available processes"
}
```

### [C15] 冪等操作

```bash
$ procler start my-api       # 実行中 → 何もしない
{"success": true, "data": {"status": "already_running", "process": {"pid": 12345}}}

$ procler stop my-api        # 停止済み → 何もしない
{"success": true, "data": {"status": "already_stopped"}}
```

### [C04] グループオーケストレーション

```bash
$ procler group start backend  # redis → db → api → worker の順で起動
$ procler group status backend # グループ内全プロセスのステータス
$ procler group stop backend   # 逆順で停止
```

### [C05] レシピのドライラン

```bash
$ procler recipe run deploy --dry-run   # 実行せずにプレビュー
$ procler recipe run deploy             # マルチステップレシピを実行
```

### [C06] スニペットライフサイクル

```bash
$ procler snippet save --name rebuild --command "docker compose build" --tags docker
$ procler snippet list --tag docker
$ procler snippet run rebuild
$ procler snippet remove rebuild
```

## インストール

```bash
# 推奨
uv tool install procler

# TUIサポート付き
uv tool install procler[tui]

# またはpip経由
pip install procler
```

ソースからインストール:

```bash
git clone https://github.com/gabu-quest/procler.git
cd procler && uv sync --all-extras
```

> フロントエンドはビルド済みで同梱されています。別途ビルドは不要です。

## 設定

プロジェクトごとに`.procler/`ディレクトリを使用。検出順序: `$PROCLER_CONFIG_DIR` > `.procler.env` > `.procler/` > gitルート > `~/.procler/`

```bash
procler config init       # [C07] .procler/をテンプレートで作成
procler config validate   # [C08] 構文と参照を検証
procler config explain    # 平易な言葉で設定を説明（LLMフレンドリー）
```

### [C09] 包括的な設定例

```yaml
version: 1

vars:
  API_PORT: "8000"
  DB_CONTAINER: postgres-dev

processes:
  api:
    command: uvicorn main:app --reload --port ${API_PORT}     # 変数置換
    context: local
    cwd: /path/to/project
    tags: [backend, api]
    description: "APIサーバー"
    namespace: backend                                         # 名前空間による分離
    ready_log_line: "Uvicorn running on"                      # log_ready条件
    max_memory: 512M                                          # RSS超過時に自動再起動
    healthcheck:
      http_get: "http://localhost:${API_PORT}/health"         # HTTPプローブ（組み込み）
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s

  worker:
    command: celery worker -A tasks
    replicas: 3                                               # worker-1, -2, -3を作成
    depends_on:
      - redis                                                 # started待機（デフォルト）
      - name: api
        condition: log_ready                                  # ready_log_line待機
      - name: db
        condition: healthy                                    # ヘルスチェック合格待機

  db:
    command: postgres
    healthcheck:
      tcp_socket: "localhost:5432"                            # TCPプローブ（組み込み）
      interval: 5s
      timeout: 3s

  cleanup:
    command: python scripts/cleanup.py
    schedule: "0 */6 * * *"                                   # cron: 6時間ごと

  db-migrate:
    command: alembic upgrade head
    context: docker
    container: ${DB_CONTAINER}                                # Docker実行

groups:
  backend:
    description: "フルバックエンドスタック"
    processes: [redis, db, api, worker]
    stop_order: [worker, api, db, redis]                      # カスタム停止順序

recipes:
  deploy:
    description: "グレースフルデプロイ"
    on_error: stop
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

## CLIリファレンス

すべてのコマンドは構造化JSONを返します。`procler capabilities`で完全な機械可読スキーマを取得できます。

| コマンド | 説明 |
|---------|------|
| **検出** | |
| `procler capabilities` | 全コマンドのJSONスキーマ（LLM検出用） |
| `procler help-llm` | LLM向け包括的使用ガイド |
| **プロセス管理** | |
| `procler define --name NAME --command CMD [オプション]` | プロセスを定義 |
| `procler start NAME` | 起動（冪等） |
| `procler stop NAME` | 停止（冪等） |
| `procler restart NAME [--clear-logs]` | 再起動 |
| `procler status [NAME]` | ステータス（全体または単一） |
| `procler list [--resolve] [--namespace NS]` | 定義一覧 |
| `procler remove NAME` | 定義を削除 |
| `procler logs NAME [--tail N] [--since TIME] [-f]` | ログ |
| `procler exec "CMD" [--context TYPE] [--container NAME]` | 単発コマンド |
| **グループ** | |
| `procler group list` | グループ一覧 |
| `procler group start\|stop\|status NAME` | グループ操作 |
| **レシピ** | |
| `procler recipe list` | レシピ一覧 |
| `procler recipe show NAME` | レシピ詳細 |
| `procler recipe run NAME [--dry-run] [--continue-on-error]` | レシピ実行 |
| **スニペット** | |
| `procler snippet list [--tag TAG]` | スニペット一覧 |
| `procler snippet show\|save\|run\|remove NAME` | スニペットCRUD |
| **設定** | |
| `procler config init [--force]` | .procler/を初期化 |
| `procler config validate` | 設定を検証 |
| `procler config path` | 設定パスを表示 |
| `procler config explain` | 平易な言葉で説明 |
| **エクスポート/インポート** | |
| `procler export systemd NAME\|--all` | [C10] systemdユニットをエクスポート |
| `procler export compose` | [C11] docker-compose.ymlをエクスポート |
| `procler import procfile PATH [--dry-run] [--merge]` | [C12] Procfileをインポート |
| **その他** | |
| `procler tui` | ターミナルUI（`procler[tui]`が必要） |
| `procler serve [--host H] [--port P] [--reload]` | Webサーバー |

### Defineオプション

| オプション | 説明 |
|-----------|------|
| `--name` | プロセス名（必須） |
| `--command` | 実行コマンド（必須） |
| `--context` | `local`または`docker`（デフォルト: local） |
| `--container` | Dockerコンテナ名（docker時に必須） |
| `--cwd` | 作業ディレクトリ |
| `--display-name` | 表示名 |
| `--tags` | カンマ区切りタグ |
| `--daemon-mode` | デーモンモード有効化 |
| `--daemon-pattern` | デーモン検出パターン |
| `--daemon-pidfile` | デーモンPIDファイルパス |
| `--daemon-container` | デーモン検出用コンテナ名 |
| `--adopt-existing` | 既存デーモンを引き取り（`--daemon-mode`が必要） |
| `--force` | 既存定義を上書き |

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
| `/api/logs/{name}` | GET | ログ取得（`?tail=100&since=5m`） |
| `/api/groups` | GET | グループ一覧 |
| `/api/groups/{name}/start` | POST | グループ起動 |
| `/api/groups/{name}/stop` | POST | グループ停止 |
| `/api/groups/{name}/status` | GET | グループステータス |
| `/api/recipes` | GET | レシピ一覧 |
| `/api/recipes/{name}` | GET | レシピ詳細 |
| `/api/recipes/{name}/run` | POST | レシピ実行 |
| `/api/recipes/{name}/dry-run` | POST | レシピドライラン |
| `/api/snippets` | GET | スニペット一覧（`?tag=filter`） |
| `/api/snippets` | POST | スニペット作成 |
| `/api/snippets/{name}` | GET | スニペット取得 |
| `/api/snippets/{name}` | DELETE | スニペット削除 |
| `/api/snippets/{name}/run` | POST | スニペット実行 |
| `/api/config` | GET | 設定ステータス |
| `/api/config/processes` | GET | 設定プロセス定義 |
| `/api/config/reload` | POST | 設定リロード |
| `/api/config/changelog` | GET | 変更履歴 |
| `/api/config/export/{format}` | GET | エクスポート（systemd, compose） |
| `/api/config/explain` | GET | 平易な言葉で設定説明 |
| `/api/health` | GET | ヘルスチェック |
| `/api/ws` | WS | リアルタイム更新 |

## Webダッシュボード

サイバーパンクデザインのVue 3フロントエンド。`procler serve`で起動し、http://localhost:8000 を開きます。

- **ダッシュボード** — リアルタイムステータスでプロセス概観
- **プロセス詳細** — WebSocketによるライブログストリーミング、検索/フィルター
- **グループ** — カードベースビュー、ワンクリック全起動/停止
- **レシピ** — ステッププレビュー、ドライラン、実行進捗
- **スニペット** — 再利用可能なコマンドの保存、管理、実行
- **設定** — 統計、変数、変更履歴ビューア

キーボードショートカット: `?`で全表示。クイックナビ: `g d` ダッシュボード、`g p` プロセス、`g g` グループ、`g r` レシピ、`g s` スニペット。

> **フロントエンド開発:** `cd frontend && npm run dev`（ポート5173）、`bash scripts/build_frontend.sh`で再ビルド

## 既知の制限事項

- **単一マシンのみ** — Proclerは1ホスト上のプロセスを管理します。複数マシンにはNomadまたはDocker Swarmを使用。
- **SQLiteステート** — ランタイム状態はローカルSQLite。クラスターデプロイには不向き。
- **ローカルログのみ** — ログキャプチャはファイルシステムベース。リモートログシンク（Splunk、Datadogなど）は非対応。
- **プロジェクトごとに1設定** — 複数設定の管理には`$PROCLER_CONFIG_DIR`を使用。
- **Windows非対応** — LinuxとmacOSのみ（プロセスステートの`/proc`統合）。

## 環境変数

| 変数 | デフォルト | 説明 |
|-----|----------|------|
| `PROCLER_LOG_LEVEL` | `INFO` | ログレベル（DEBUG, INFO, WARNING, ERROR） |
| `PROCLER_LOG_FILE` | - | ログファイルパス（自動ローテーション） |
| `PROCLER_CONFIG_DIR` | `.procler/` | 設定ディレクトリの上書き |
| `PROCLER_DB_PATH` | `.procler/state.db` | データベースパス |
| `PROCLER_CORS_ORIGINS` | `localhost` | 許可されたオリジン（カンマ区切り） |
| `PROCLER_DEBUG` | - | 詳細なエラーメッセージを有効化 |

## 開発

```bash
uv sync --all-extras        # 全依存関係をインストール
uv run pytest -v            # テスト実行（320+）
uv run procler serve --reload  # ホットリロードで開発サーバー
```

## ライセンス

MIT
