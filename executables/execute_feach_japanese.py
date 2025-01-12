import os, sys; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from utils.common_method import count_logical_cores
from services.create_author_id_list import CreateAuthorIdList
from services.gather_authors_data import GatherAuthorData
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from api.spreadsheet_manager import SpreadsheetManager
from config.secret_manager import SecretManager
import time
from utils.async_log_to_sheet import append_log_async
import asyncio

secret = SecretManager()

#条件を指定して研究者リスト作成する
async def execute(topic_ids,primary=True,threshold=15,year_threshold=2015,title_and_abstract_search='',max_works=16,di_calculation=False,output_sheet_name="API動作確認"):
    
    try:
        await append_log_async(f"") 
        await append_log_async(f"処理を開始します。") 
        
        sheet_manager = SpreadsheetManager("アプリケーション", output_sheet_name)
        sheet_manager.clear_rows_from_second()
        headers = ["研究者ID", "名前", "名前2", "最新の国", "最新の所属", "過去の所属","detail of affiliation", "所属タイプ", "education以外の所属機関数", "国別所属数","海外にいる期間", "キャリア年数", "works数", "全てのworksの被引用数","H-Index", "過去5年H-index", "過去10年H-index", "2yr Mean Citedness","I10_index", "年次の被引用数", "年次の被引用数の伸び率", "Topics detail","キーワードの数(非引用数が20以上)", "キーワードの詳細", "共著者数","各共著者との共著回数", "共著者の所属機関タイプの内訳", "first論文数","対応論文数", "DI0.8以上のworks数", "cited_by_other_field","impact指数の合計", "type_crossref", "type", "論文ID", "name","所属", "Country Codes", "責任著者", "ポジション", "責任著者名","引用数", "被引用数", "D-index", "impact_index", "Primary Topic","Topics", "Publication Year", "Publication Date", "Landing Page URL","Authors", "Keywords", "Grants","論文ID", "name", "所属", "Country Codes", "責任著者", "ポジション","責任著者名", "引用数", "被引用数", "D-index", "impact_index","Primary Topic", "Topics", "Publication Year", "Publication Date","Landing Page URL", "Authors", "Keywords", "Grants","論文ID", "name", "所属", "Country Codes", "責任著者", "ポジション","責任著者名", "引用数", "被引用数", "D-index", "impact_index","Primary Topic", "Topics", "Publication Year", "Publication Date","Landing Page URL", "Authors", "Keywords", "Grants"]
        sheet_manager.sheet.update('A1',[headers])
        
        
        person_num = 4
        count_cores = count_logical_cores()
        max_works = count_cores*2
        
        await append_log_async(f"論理コア数:{count_cores},max_works:{max_works}")  # ログの追加
        
        creater = CreateAuthorIdList(topic_ids=topic_ids,primary=primary,threshold=threshold,year_threshold=year_threshold,title_and_abstract_search=title_and_abstract_search,max_works=max_works)
        creater.run_get_works()
        print('論文数:',len(creater.all_results))
        creater.extract_authors(only_japanese=True)
        print('著者数:',len(creater.authors_id_list))

        await append_log_async(f"論文数:{len(creater.all_results)},著者数:{len(creater.authors_id_list)}")  #ログの追加
        
        max_workers=max_works//person_num
        
        def process_author(author_id): 
            """
            個々のauthor_idに対して処理を実行する関数
            """
            try:
                print(author_id, "の調査")
                author = GatherAuthorData(author_id=author_id,max_workers=max_workers)
                author.run_fetch_works()
                
                if di_calculation:
                    author.di_calculation()
                
                profile_dict = author.gathering_author_data()
                works_data_dict = author.get_top_three_article()
                
                #profile辞書＋top_three_article
                profile_dict.update(works_data_dict)
                
                return profile_dict
            
            except Exception as e:
                logging.error(f"process_author内でエラー発生 (author_id: {author_id}): {e}", exc_info=True)
                #await append_log_async(f"process_author内でエラー発生 (author_id: {author_id}): {e}")  # ログの追加
                raise  # エラーを再スローして上位で処理
            
        # 並列処理
        results_list = []
        length = 10
        with ThreadPoolExecutor(max_workers=person_num) as executor:  # max_workersは並列スレッド数
            futures = {executor.submit(process_author, author_id): author_id for author_id in creater.authors_id_list}
            for future in as_completed(futures):
                author_id = futures[future]
                try:
                    result = future.result()  # 処理結果を取得
                    results_list.append(result)
                    
                    if len(results_list) >= length:  
                        print(f"著者{length}人の処理が完了しました。")
                        await append_log_async(f"著者{length}人の処理が完了しました。")  #ログの追加
                        length+=10
                
                except Exception as e: 
                    # メインスレッドでのエラーハンドリング
                    logging.error(f"{author_id} の処理中にエラーが発生しました: {e}")
                    await append_log_async(f"{author_id} の処理中にエラーが発生しました: {e}") #ログの追加
       
        #print("研究者数:",len(results_list))
        await append_log_async(f"処理が終了しました。スプレットシートに追加します。") 
        rows =[]
        for result in results_list:
            row = [str(value) for value in result.values()]
            rows.append(row)
            
        for row in rows:
            for i,each in enumerate(row):
                if len(each)>=50000:
                    #print("インデクス",i)
                    row[i] = each[:50000]
        
        sheet_manager.clear_rows_from_second()
        max_retries = 5
        attempt = 0  
        while attempt < max_retries:
            try:
                sheet_manager.append_rows(rows)
                print("スプレットシートに追加しました。")
                await append_log_async(f"スプレットシートに追加しました。") 
                break
            except Exception as e:
                attempt += 1
                print(f"エラーが発生しました (試行回数: {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    print(f"再試行します...")
                else:
                    print("最大リトライ回数に達しました。操作を終了します。")
                    raise ValueError(f"sheet_manager.append_rowsが最大リトライ回数に達しました: {e}")  # ValueError を再スロー
                
        
        return {"count_authors":len(results_list)}
    
    except ValueError as e:
        print(f"エラー: {e}")
        await append_log_async(f"エラーにより処理が中断しました。:{e}") 
        return e
    except Exception as e:
        print(f"予期しないエラー: {e}")
        await append_log_async(f"エラーにより処理が中断しました。:{e}") 
        return e
    
if __name__ == "__main__":
    # 開始時間を記録
    start_time = time.time()
    
    topic_ids= ["T10966"]
    execute(topic_ids,primary=True,threshold=15,year_threshold=2020,title_and_abstract_search='',max_works=16,di_calculation=False,output_sheet_name="API動作確認")
    
    # 終了時間を記録
    end_time = time.time()
    # 処理時間を計算
    elapsed_time = end_time - start_time
    print(f"処理時間: {elapsed_time:.2f} 秒")