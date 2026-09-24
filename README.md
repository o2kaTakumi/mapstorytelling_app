# MapStoryTelling

## 環境
- uv 0.11.21 (5aa65dd7a 2026-06-11 aarch64-apple-darwin)
- Python 3.14.6 (uv仮想環境)

## 環境構築
1. 下のサイトに従ってuvをインストール
   - [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)

2. `.env.example`をコピーして`.env`ファイルを作成
3. `.env`ファイルに個人で取得した各APIキーやメールアドレスを入力
4. ターミナルで`uv run main.py`を実行し，表示されるURLにアクセス
   - データを強制的に再生成させたい場合はURLの末尾に`?refresh=true`を追加してアクセスするとできます

