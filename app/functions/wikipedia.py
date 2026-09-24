import os
import wikipediaapi

from pathlib import Path
from dotenv import load_dotenv

# wikipediaの記事取得関数
def get_section_by_path(page, path):
    levels = path.split('/')
    current_search_area = page.sections
    target_section = None
    for level_title in levels:
        found = False
        for s in current_search_area:
            if s.title == level_title:
                target_section = s
                current_search_area = s.sections
                found = True
                break
        if not found:
            return None
    return target_section

def fetch_and_save_article(root_dir:Path, page_title="治承・寿永の乱", section_path="経緯/後期"):
    load_dotenv(root_dir/".env")
    """Wikiからテキストを取得し、ファイルに保存して内容を返す"""
    wiki_agent = os.getenv("WIKI_USER_AGENT")
    wiki = wikipediaapi.Wikipedia(user_agent=wiki_agent, language='ja')
    page = wiki.page(page_title)
    print("##", page_title, section_path, page)

    if not page.exists():
        return "ページが見つかりません"

    section = get_section_by_path(page, section_path)

    if section:
        text = section.full_text()
    else:
        text = "指定されたセクションが見つかりません。"

    # ファイルに保存
    path = root_dir/"app"/"data"/"article.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    
    return text