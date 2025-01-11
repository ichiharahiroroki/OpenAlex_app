#uvicorn api_endpoint:app --reload
#uvicorn endpoint.api_endpoint:app --host 0.0.0.0 --port 8000 --reload --ws-ping-interval 20 --ws-ping-timeout 500
#ngrok http 8000
from fastapi import FastAPI, WebSocket, WebSocketDisconnect,HTTPException
from typing import List
from pydantic import BaseModel
from typing import Optional
from executables.execute_feach_japanese import execute
from services.create_author_id_list import CreateAuthorIdList
from utils.common_method import count_logical_cores
from executables.ws_execute_feach_japanese import  ws_execute
import asyncio
import time
import logging
from endpoint.connection_manager import ConnectionManager  # 修正後のインポート
import threading


app = FastAPI(title="Author Information API")

# WebSocket 接続を管理するクラス
manager = ConnectionManager()

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
    

# WebSocket エンドポイント
@app.websocket("/ws_feach_japanese/ws/")
#役割: クライアントとサーバー間でリアルタイムな双方向通信を確立し、進捗メッセージを送信します。
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # クライアントからのメッセージを受信（必要に応じて処理）
            data = await websocket.receive_text()
            # 必要であれば、受信したメッセージに基づいて応答
            await websocket.send_text(f"Received: {data}")
    
    except WebSocketDisconnect:
        print("WebSocketDisconnect接続が切れました。")
        manager.disconnect(websocket)
        

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
    
    
# エンドポイント: データを受け取って処理
@app.post("/feach_japanese/")
async def process_feach_japanese(request_data: RequestData):
    count_cores = count_logical_cores()
    max_works = count_cores*2
    print(max_works)
     
    start_time = time.time()  # 実行開始時間を記録
    result= execute(
            topic_ids=request_data.topic_id,
            primary=request_data.primary,  # 固定値
            threshold=request_data.citation_count,
            year_threshold=request_data.publication_year,
            title_and_abstract_search=request_data.title_and_abstract_search,
            max_works=max_works,
            di_calculation=request_data.di_calculation,
            output_sheet_name=request_data.output_sheet_name
            )
    
    end_time = time.time()  # 実行終了時間を記録
    elapsed_time = end_time - start_time  # 実行時間を計算
    
    if isinstance(result, dict):  # result が辞書の場合
        result['execution_time'] = elapsed_time  # 実行時間を追加
        return result
    else:
        result_dict={
            'execution_time':elapsed_time,
            'message':result
            }
        return result_dict

# エンドポイント: データを受け取って処理
@app.post("/ws_feach_japanese/")
async def ws_process_feach_japanese(request_data: RequestData):
    count_cores = count_logical_cores()
    max_works = count_cores*2
    print(max_works)
     
    start_time = time.time()  # 実行開始時間を記録
    result= await ws_execute(
            manager,
            topic_ids=request_data.topic_id,
            primary=request_data.primary,  # 固定値
            threshold=request_data.citation_count,
            year_threshold=request_data.publication_year,
            title_and_abstract_search=request_data.title_and_abstract_search,
            max_works=max_works,
            di_calculation=request_data.di_calculation,
            output_sheet_name=request_data.output_sheet_name
            )
    
    end_time = time.time()  # 実行終了時間を記録
    elapsed_time = end_time - start_time  # 実行時間を計算
    
    await manager.broadcast(f"処理にかかった時間:{elapsed_time}")
    #ここのWebSocketの接続解除を入れたい。
    await manager.broadcast("!*処理が完了しました*!")
    
    if isinstance(result, dict):  # result が辞書の場合
        result['execution_time'] = elapsed_time  # 実行時間を追加   
        return result
    else:
        result_dict={
            'execution_time':elapsed_time,
            'message':result
            }
        return result_dict
    
    
from executables.sk_execute_feach_japanese import sk_execute  # 追加
from endpoint.log_manager import add_log  # ログ管理モジュールをインポート

# 新しいエンドポイント: sk_execute を呼び出す
@app.post("/sk_fech_japanese/")
async def sk_process_feach_japanese(request_data: RequestData):
    count_cores = count_logical_cores()
    max_works = count_cores * 2
    max_works=4
    print(max_works)
     
    start_time = time.time()  # 実行開始時間を記録
    result = sk_execute(
            topic_ids=request_data.topic_id,
            primary=request_data.primary,  # 固定値
            threshold=request_data.citation_count,
            year_threshold=request_data.publication_year,
            title_and_abstract_search=request_data.title_and_abstract_search,
            max_works=max_works,
            di_calculation=request_data.di_calculation,
            output_sheet_name=request_data.output_sheet_name
            )
    
    end_time = time.time()  # 実行終了時間を記録
    elapsed_time = end_time - start_time  # 実行時間を計算
    
    add_log(f"処理にかかった時間: {elapsed_time}")
    add_log("!*処理が完了しました*!")
    
    if isinstance(result, dict):  # result が辞書の場合
        result['execution_time'] = elapsed_time  # 実行時間を追加   
        return result
    else:
        result_dict = {
            'execution_time': elapsed_time,
            'message': result
        }
        return result_dict  
    
    
    
from endpoint.log_manager import add_log, get_logs, clear_logs  # ここを変更

# スタックの中身を取得するエンドポイント
@app.get("/sk_get_logs/")
async def sk_get_logs():
    """
    log_managerに貯められたログを取得する
    """
    logs = get_logs()  # log_manager.py の get_logs() を呼ぶ
    if not logs:
        raise HTTPException(status_code=404, detail="スタックが空です")
    return {"logs": logs, "total_logs": len(logs)}

@app.post("/sk_clear_logs/")
async def sk_clear_logs_endpoint():
    """
    log_managerに貯められているログをクリアする
    """
    clear_logs()  # log_manager.py の clear_logs() を呼ぶ
    return {"message": "スタックがクリアされました", "current_stack_size": 0}


@app.get("/")
async def read_root():
    return {"message": "Welcome to the Author Information API"}  
    
if __name__ == "__main__":
    # 非同期関数を呼び出すためにイベントループを使用
    request_data = {
        "author_info_source": "work",
        "topic_id": ["T10966"],
        "primary": True,
        "citation_count": 15,
        "publication_year": 2015,
        "title_and_abstract_search": "count",
        "di_calculation": False,
        "output_sheet_name": "API動作確認"
    }

    async def main():
        # 非同期関数を直接実行
        result = await process_feach_japanese(RequestData(**request_data))
        print(result)

    # イベントループで実行
    asyncio.run(main())