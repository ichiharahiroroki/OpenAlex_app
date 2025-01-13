#uvicorn endpoint.api_endpoint:app --reload
#uvicorn endpoint.api_endpoint:app --host 0.0.0.0 --port 8000 --reload --ws-ping-interval 20 --ws-ping-timeout 500
#ngrok http 8000
import os, sys; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
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
from utils.async_log_to_sheet import append_log_async
from endpoint.connection_manager import ConnectionManager  # 修正後のインポート
import threading
from config.get_env import get_instance_id,stop_this_instance


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
    try:
        await append_log_async(f"")  
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
        print(f"日本人論文数:{len(creater.all_results)},日本人研究者数:{len(creater.authors_id_list)}")
        await append_log_async(f"論文数:{len(creater.all_results)},日本人研究者数:{len(creater.authors_id_list)}")  
        print(f"処理を終了します。")
        await append_log_async(f"プログラムを処理を終了します。")  
        
        this_instance_id = get_instance_id()
        if this_instance_id =="i-0ef1507637db1e852":
            print(f"CORE8のインスタンスを停止する処理をします。インスタンスID:{this_instance_id}")
            await append_log_async(f"CORE8のインスタンスを停止する処理をします。インスタンスID:{this_instance_id}")  
        elif this_instance_id =="i-00c9116fa53632f53":
            print(f"テスト用インスタンスを停止する処理をします。インスタンスID:{this_instance_id}")
            await append_log_async(f"テスト用インスタンスを停止する処理をします。インスタンスID:{this_instance_id}")     
        elif this_instance_id =="local":
            print("ローカル環境で実行されたので、インスタンスの停止は不要です。")
            await append_log_async(f"ローカル環境で実行されたので、インスタンスの停止は不要です。")    
        else:
            print(f"現在のインスタンス環境が登録されていません。手動でインスタンスの停止が必要です。インスタンスID:{this_instance_id}")
            await append_log_async(f"現在のインスタンス環境が登録されていません。手動でインスタンスの停止が必要です。インスタンスID:{this_instance_id}")     
           
        stop_this_instance(this_instance_id)
        if this_instance_id !="local":
            time.sleep(4)
            await append_log_async(f"インスタンスの停止処理に失敗しました。手動で停止させてください。:{this_instance_id}") 
        
    except Exception as e:
        try:
            print(e)
            await append_log_async(f"{e}")  # ログの追加
            this_instance_id = get_instance_id()
            print(f"エラーが発生したため、処理が中断されました。インスタンスの停止処理をします。インスタンスID:{this_instance_id}")
            await append_log_async(f"エラーが発生したため、処理が中断されました。インスタンスの停止処理をします。インスタンスID:{this_instance_id}")
            stop_this_instance(this_instance_id)
            if this_instance_id !="local":
                time.sleep(4)
                await append_log_async(f"インスタンスの停止処理に失敗しました。手動で停止させてください。:{this_instance_id}") 
        except:
            print(f"インスタンスの停止処理に失敗しました。手動で停止させてください。:{this_instance_id}")
            await append_log_async(f"インスタンスの停止処理に失敗しました。手動で停止させてください。:{this_instance_id}") 
            

# エンドポイント: データを受け取って処理
@app.post("/feach_japanese/")
async def process_feach_japanese(request_data: RequestData):
    try:
        count_cores = count_logical_cores()
        max_works = count_cores*2
        print(max_works)
        
        start_time = time.time()  # 実行開始時間を記録
        result= await execute(
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
        # 時間、分、秒に変換
        hours = int(elapsed_time // 3600)
        minutes = int((elapsed_time % 3600) // 60)
        seconds = int(elapsed_time % 60)
        # フォーマット済みの文字列を作成
        formatted_time = f"{hours}時間{minutes}分{seconds}秒"
        print(f"プログラムが終了します。処理にかかった時間は{formatted_time}")
        
        await append_log_async(f"プログラムが終了します。処理にかかった時間:{formatted_time}")  # ログの追加
        
        this_instance_id = get_instance_id()
        if this_instance_id =="i-0ef1507637db1e852":
            print(f"CORE8のインスタンスを停止する処理をします。インスタンスID:{this_instance_id}")
            await append_log_async(f"CORE8のインスタンスを停止する処理をします。インスタンスID:{this_instance_id}")  
        elif this_instance_id =="i-00c9116fa53632f53":
            print(f"テスト用インスタンスを停止する処理をします。インスタンスID:{this_instance_id}")
            await append_log_async(f"テスト用インスタンスを停止する処理をします。インスタンスID:{this_instance_id}")     
        elif this_instance_id =="local":
            print("ローカル環境で実行されたので、インスタンスの停止は不要です。")
            await append_log_async(f"ローカル環境で実行されたので、インスタンスの停止は不要です。")    
        else:
            print(f"現在のインスタンス環境が登録されていません。手動でインスタンスの停止が必要です。インスタンスID:{this_instance_id}")
            await append_log_async(f"現在のインスタンス環境が登録されていません。手動でインスタンスの停止が必要です。インスタンスID:{this_instance_id}")     
            
        stop_this_instance(this_instance_id)
        if this_instance_id !="local":
            time.sleep(8)
            await append_log_async(f"インスタンスの停止処理に失敗しました。手動で停止させてください。:{this_instance_id}") 
        
    except Exception as e:
        try:
            print(e)
            await append_log_async(f"{e}")  # ログの追加
            this_instance_id = get_instance_id()
            print(f"エラーが発生したため、処理が中断されました。インスタンスの停止処理をします。インスタンスID:{this_instance_id}")
            await append_log_async(f"エラーが発生したため、処理が中断されました。インスタンスの停止処理をします。インスタンスID:{this_instance_id}")
        
            stop_this_instance(this_instance_id)
            if this_instance_id !="local":
                time.sleep(8)
                print(f"インスタンスの停止処理に失敗しました。手動で停止させてください。:{this_instance_id}")
                await append_log_async(f"インスタンスの停止処理に失敗しました。手動で停止させてください。:{this_instance_id}") 
        except:
            print(f"インスタンスの停止処理に失敗しました。手動で停止させてください。:{this_instance_id}")
            await append_log_async(f"インスタンスの停止処理に失敗しました。手動で停止させてください。:{this_instance_id}") 
            




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
        #process_count_japanese
        #process_feach_japanese
        await process_feach_japanese(RequestData(**request_data))
        

    # イベントループで実行
    asyncio.run(main())