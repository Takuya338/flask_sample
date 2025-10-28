# Flask と MySQL の Docker 開発環境

このリポジトリは Flask と MySQL を組み合わせた開発用 Docker 環境です。  
以下のコンポーネントが含まれています。

- Python 3.11.4
- Flask 2.3.2
- MySQL 8.0
- Selenium Standalone Chrome（UI テスト用プロファイル）
- docker compose によるサービス編成

## プロジェクト構成

```
.
├── app/
│   ├── app.py         # メインの Flask アプリケーション
│   └── templates/     # HTML テンプレート
├── db/
│   └── init.sql       # MySQL 初期化用 SQL
├── tests/
│   └── ui/            # Selenium UI テスト
│       └── test_homepage.py
├── compose.yaml       # Docker Compose 設定
├── Dockerfile         # Flask アプリ用イメージのビルド設定
└── requirements.txt   # Python 依存パッケージ
```

## セットアップ

1. Docker / Docker Compose がインストールされていることを確認してください。
2. プロジェクトのルートディレクトリで次を実行します。

   ```bash
   docker compose up --build
   ```

3. Flask アプリは `http://localhost:5000` で確認できます。
4. データベース接続テストは `http://localhost:5000/db-test` で確認できます。

アプリケーションコンテナは `./app` ディレクトリをバインドマウントしているため、ホスト側でコードを編集すると即座に反映されます。

## 環境変数

`compose.yaml` 内で以下の環境変数を定義しています。必要に応じて変更してください。

| 変数名 | デフォルト値 | 用途 |
|--------|--------------|------|
| `MYSQL_DATABASE` | `mysql` | 接続先データベース名 |
| `MYSQL_USER`     | `mysql` | アプリケーションユーザー |
| `MYSQL_PASSWORD` | `mysql` | アプリケーションユーザーのパスワード |
| `MYSQL_HOST`     | `db`    | MySQL コンテナのホスト名 |
| `MYSQL_PORT`     | `3306`  | MySQL のポート番号 |

アプリケーション側では `python-dotenv` を使用しているため、必要であれば `app/.env` を作成して上記と同じキーを設定することもできます。

## MySQL の操作

### コンテナ内部から接続

```bash
docker compose exec db mysql -u mysql -pmysql mysql
```

`mysql` の部分は `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DATABASE` の値に合わせて変更してください。

### 初期化 SQL

`db/init.sql` はコンテナ起動時に自動実行され、`products` テーブルが作成されます。スキーマを変更したい場合はこのファイルを編集し、コンテナを再作成してください。

### ホストから接続

MySQL は `3306` 番ポートを公開しています。ホスト側に MySQL クライアントがある場合は次のように接続できます。

```bash
mysql -h 127.0.0.1 -P 3306 -u mysql -p
```

## テストや追加コマンドの実行

Flask コンテナ内でコマンドを実行する例:

```bash
docker compose exec app flask routes
```

依存パッケージを追加した場合は `requirements.txt` を更新し、改めて `docker compose up --build` を実行してください。

## UI テスト (Selenium)

UI テストは Selenium コンテナと専用サービス（`ui-tests`）をテスト用プロファイルで起動して実行します。

1. アプリと DB を起動
   ```bash
   docker compose up -d app db
   ```
2. Selenium を起動（テスト用プロファイルを有効化）
   ```bash
   docker compose --profile test up -d selenium
   ```
3. UI テストを実行
   ```bash
   docker compose --profile test run --rm ui-tests
   ```

テストは `tests/ui/test_homepage.py` に定義しており、`APP_URL` と `SELENIUM_REMOTE_URL` の環境変数で接続先を切り替えられます。  
コンテナ終了後に Selenium を停止する場合は `docker compose --profile test stop selenium` を実行してください。

## サービスの停止

```bash
docker compose down
```

永続ボリューム（MySQL データ）も削除したい場合は `-v` オプションを追加してください。

```bash
docker compose down -v
```
