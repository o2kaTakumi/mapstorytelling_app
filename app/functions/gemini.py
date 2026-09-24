import json, os

from pathlib import Path
from google import genai
from pydantic import BaseModel, Field
from typing import Literal, Optional, Union
from dotenv import load_dotenv

class MapStyle(BaseModel):
    type:Literal["point", "line", "polygon"]
    line_color: Optional[str] = Field(None, alias="line-color")
    line_width: Optional[float] = Field(None, alias="line-width")
    line_dasharray: Optional[list[int]] = Field(None, alias="line-dasharray")
    fill_color: Optional[str] = Field(None, alias="fill-color")
    fill_opacity: Optional[float] = Field(None, alias="fill-opacity")
    fill_outline_color: Optional[str] = Field(None, alias="fill-outline-color")
    circle_color: Optional[str] = Field(None, alias="circle-color")
    circle_radius: Optional[float] = Field(None, alias="circle-radius")

class FeatureProperty(BaseModel):
    name: str
    description: str
    style: MapStyle

class Geometry(BaseModel):
    type: Literal["Point", "LineString", "Polygon"]
    coordinates: Union[list[float], list[list[float]], list[list[list[float]]]] 

class GeoJSONFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: Geometry
    properties: FeatureProperty

class FeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[GeoJSONFeature]

class MapSource(BaseModel):
    type: str = "geojson"
    data: FeatureCollection

class MapData(BaseModel):
    bounds: list[float] = Field(description="[min_lon, min_lat, max_lon, max_lat] の順。小数点第4位まで。")
    source: MapSource

class Scene(BaseModel):
    name: str = Field(description="シーンのタイトル")
    narration: str = Field(description="ナレーション文章")
    map_data: MapData

def get_scenes_data(source_text, root_dir:Path, refresh=False):
    """
    シーンデータを取得する。
    mapdata.json が存在し、refreshがFalseならそこから読み込む。
    そうでなければGemini APIを叩いて生成し、mapdata.jsonに保存する。
    """
    load_dotenv(root_dir/".env")
    jsonfile_path = root_dir/"app"/"data"/"mapdata.json"

    # 1. ローカルファイルが存在し、再生成フラグが立っていない場合はファイルを読み込む
    if not refresh and os.path.exists(jsonfile_path):
        print(f"Loading scenes from json-file...")
        try:
            with open(jsonfile_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("JSON decode error. Regenerating...")

    print("Generating scenes with Gemini API...")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=gemini_api_key)
    
    # プロンプトの組み立て
    prompt = f"""
    以下の「元の文章」を元に、Mapbox Storytelling用の地図データ（シーンリスト）を作成してください。

    ## 注意事項:
    - 地図の範囲(bounds)は、主要地点が明確に識別できるよう適切に設定してください。
    - ナレーションを理解する助けとなるように，各シーンの地図に，必ずひとつ以上で，十分な数の地図情報（ポイント，ライン，ポリゴン，ラベル）を配置して下さい．
    - 特にポリゴンを多めにを多めに配置して下さい．
    - properties内のstyleは、Mapboxのpaintプロパティに対応させてください。
    - ナレーションと地図要素に矛盾がないよう、自己検閲した上で出力してください。

    元の文章:
    {source_text}
    """

# 座標は信頼できる地理情報を元に、正確な数値（[経度, 緯度]）を推測して入れてください。
    try:
        # 2. 指定されたモデル (gemini-3.6-flash) でコンテンツを生成
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite", 
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": list[Scene],
            },
        )
        
        if not response.parsed:
            print("Error: API returned empty or unparseable data.")
            return []

        # 3. Pydanticモデルを辞書型に変換
        # exclude_none=True により、Mapboxでエラーの原因となる null プロパティを完全に除外します
        scenes = [scene.model_dump(by_alias=True, exclude_none=True) for scene in response.parsed]
        
        # 4. JSONファイルとして保存
        with open(jsonfile_path, "w", encoding="utf-8") as f:
            json.dump(scenes, f, ensure_ascii=False, indent=2)
        print(f"Saved scenes to {jsonfile_path}")
            
        return scenes

    except Exception as e:
        # サーバー過負荷(503)などのエラーハンドリング
        print(f"!!! Gemini API Error Detail: {type(e).__name__} - {e}")
        return []