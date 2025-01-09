#uvicorn api_endpoint:app --reload
#ngrok http 8000
from fastapi import FastAPI, Query
from typing import List
from pydantic import BaseModel
from typing import Optional
from services.create_author_id_list import CreateAuthorIdList
from utils.common_method import count_logical_cores

app = FastAPI(title="Author Information API")

# リクエストデータのモデル
class RequestData(BaseModel):
    author_info_source: str  # 著者情報の取得先
    topic_id: List[str] =[] # トピックID（リスト）
    primary: bool
    citation_count: int =-1 # 引用数（整数）
    publication_year: int =-1 # 出版年（整数）
    title_and_abstract_search: str =""
    di_calculation: bool =False # DI計算（真偽値）
    output_sheet_name: str =""  # 出力シート名
    

# エンドポイント: データを受け取って処理
@app.post("/count_japanese/")
async def process_count_japanese(request_data: RequestData):
    count_cores = count_logical_cores()
    max_works = count_cores*2
    print(max_works)
    creater = CreateAuthorIdList(
        topic_ids=request_data.topic_id,
        primary=request_data.primary,  # 固定値
        threshold=request_data.citation_count,
        year_threshold=request_data.publication_year,
        title_and_abstract_search=request_data.title_and_abstract_search,
        max_works = max_works
    )

    creater.run_get_works()
    creater.extract_authors(only_japanese=True)
    
    return {
        "count_works": len(creater.all_results),
        "count_japanese_auhtors": len(creater.authors_id_list)
    }
    
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Author Information API"}
    