import os

from pathlib import Path
from flask import Flask, render_template, request
from app.functions import gemini, wikipedia
from dotenv import load_dotenv

app = Flask(__name__)

# プロジェクトのルートディレクトリ
ROOT_DIR = Path(__file__).parent.parent.resolve()

ARTICLE_DATA_PATH= ROOT_DIR/"app"/"data"/"article.txt"

@app.route('/')
def index():
    # URLパラメータ取得
    force_refresh = request.args.get('refresh') == 'true' # ?refresh=true で強制再生成
    page_title = request.args.get('page_title', "治承・寿永の乱")
    section_path = request.args.get('section_path', "経緯/後期")

    # 1. 記事の準備
    if not os.path.exists(ARTICLE_DATA_PATH) or force_refresh:
        print("Fetching article from Wikipedia...")
        source_text = wikipedia.fetch_and_save_article(ROOT_DIR, page_title, section_path)
    else:
        # print("Reading article from local file...")
        with open(ARTICLE_DATA_PATH, "r", encoding="utf-8") as f:
            source_text = f.read()

    # 2. シーンデータの取得（ファイル読み込み or API生成）
    # 記事テキストが変わった場合などを考慮し、強制リフレッシュ時はここも再生成する
    scenes_data = gemini.get_scenes_data(source_text, ROOT_DIR, refresh=force_refresh)

    # 3. テンプレートにデータとmapboxアクセストークンを渡してレンダリング
    load_dotenv(ROOT_DIR/".env")
    mapbox_access_token = os.getenv("MAPBOX_ACCESS_TOKEN")
    return render_template("index.html", scenes=scenes_data, mapbox_token=mapbox_access_token)

if __name__ == '__main__':
    app.run(debug=True, port=5000)