import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from utils.outputer import sort_dict_list_by_key,adjust_indicators, dict_list_to_string_rows, output_to_sheet, truncate_and_report_long_cells
from utils.common_method import count_logical_cores
from services.create_author_id_list import CreateAuthorIdList
from services.gather_authors_data import GatherAuthorData
from concurrent.futures import ThreadPoolExecutor, as_completed
from api.spreadsheet_manager import SpreadsheetManager
from config.secret_manager import SecretManager
from utils.async_log_to_sheet import append_log_async
import asyncio
import time
secret = SecretManager()

#条件を指定して研究者リスト作成する
async def execute(topic_ids,primary=True,threshold=15,year_threshold=2015,title_and_abstract_search='',di_calculation=False,output_sheet_name="API動作確認",use_API_key = False):
    
    start_time = time.time()  # 実行開始時間を記録
    try:
        await append_log_async(f"") 
        await append_log_async(f"処理を開始します。") 
        
        file_name = os.getenv('FIXED_SPREADSHEET_NAME')
        sheet_manager = SpreadsheetManager(file_name, output_sheet_name)
        sheet_manager.clear_rows_from_second()

        
        count_cores = count_logical_cores()
        if use_API_key:
            max_works = count_cores*20
        else:
            max_works = count_cores*10
        
        await append_log_async(f"論理コア数:{count_cores},max_works:{max_works},論文の検索を始めます。")  # ログの追加
        
        creater = CreateAuthorIdList(topic_ids=topic_ids,primary=primary,threshold=threshold,year_threshold=year_threshold,title_and_abstract_search=title_and_abstract_search,max_works=max_works,use_API_key=use_API_key)
        creater.run_get_works()
        creater.extract_authors(only_japanese=True)
        await append_log_async(f"論文数:{len(creater.all_results)},日本人著者数:{len(creater.authors_id_list)}")  #ログの追加
        
        person_num = 8 if use_API_key else 4
        max_workers=max_works//person_num
        
        def process_author(author_id): 
            """
            個々のauthor_idに対して処理を実行する関数
            """
            try:
                print(author_id, "の調査")
                author = GatherAuthorData(author_id=author_id,max_workers=max_workers,use_API_key=use_API_key)
                author.run_fetch_works()
                
                if not author.article_dict_list:
                    return {}
                    
                if di_calculation:
                    author.di_calculation()
                
                profile_dict = author.gathering_author_data()
                works_data_dict = author.get_top_three_article()
                top_searched_article = creater.get_top_article(author_id)
                profile_dict.update(top_searched_article)
                profile_dict.update(works_data_dict)
                
                return profile_dict
            
            except Exception as e:
                raise Exception(f"process_author内でエラー発生 (author_id: {author_id}): {e}") # エラーを再スローして上位で処理
            
        # 並列処理
        results_list = []
        length = 5
        with ThreadPoolExecutor(max_workers=person_num) as executor:  # max_workersは並列スレッド数
            futures = {executor.submit(process_author, author_id): author_id for author_id in creater.authors_id_list}
            for future in as_completed(futures):
                author_id = futures[future]
                try:
                    result = future.result()  # 処理結果を取得
                    results_list.append(result)
                    
                    if len(results_list) >= length:  
                        await append_log_async(f"著者{length}人の処理が完了しました。")  #ログの追加
                        length+=5
                        
                    # イベントループに制御を戻す
                    await asyncio.sleep(0)
                
                except Exception as e: 
                    # メインスレッドでのエラーハンドリング
                    await append_log_async(f"{author_id} の処理中にエラーが発生しました: {e}") #ログの追加
                    # イベントループに制御を戻す
                    await asyncio.sleep(0)

        
        end_time = time.time()  # 実行終了時間を記録
        elapsed_time = end_time - start_time  # 実行時間を計算
        # 時間、分、秒に変換
        hours = int(elapsed_time // 3600)
        minutes = int((elapsed_time % 3600) // 60)
        seconds = int(elapsed_time % 60)
        # フォーマット済みの文字列を作成
        formatted_time = f"{hours}時間{minutes}分{seconds}秒"
        await append_log_async(f"処理が終了しました。処理にかかった時間:{formatted_time}")  # ログの追加

        await append_log_async(f"スプレットシートに追加します。") 
        
        header,results_list = adjust_indicators(results_list)
        
        results_list = sort_dict_list_by_key(results_list,"total_works_citations")
        
        rows = dict_list_to_string_rows(results_list)
        rows = truncate_and_report_long_cells(rows) #スプレットシートでは、１セル当たり5万文字までなので、長い文字列を削除
        
        await output_to_sheet(sheet_manager,header,rows) #スプレットシートに追加。
        
        return {"count_authors":len(results_list)}
    
    except ValueError as e:
        await append_log_async(f"エラーにより処理が中断しました。:{e}") 
        return e
    except Exception as e:
        await append_log_async(f"予期しないエラーにより処理が中断しました。:{e}") 
        return e
