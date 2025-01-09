import os, sys; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from utils.common_method import count_logical_cores
from services.create_author_id_list import CreateAuthorIdList
from services.gather_authors_data import GatherAuthorData
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from api.spreadsheet_manager import SpreadsheetManager
from config.secret_manager import SecretManager
import time
secret = SecretManager()

#条件を指定して研究者リスト作成する
def execute():
    person_num = 4
    count_cores = count_logical_cores()
    max_works = count_cores*2
    creater = CreateAuthorIdList(topic_ids=["T10966"],primary=True,threshold=15,year_threshold=2010,title_and_abstract_search='("novel target" OR "new target" OR "therapeutic target")',max_works=max_works)
    creater.run_get_works()
    print('論文数:',len(creater.all_results))
    creater.extract_authors(only_japanese=True)
    print('著者数:',len(creater.authors_id_list))
    
    max_workers=max_works//person_num
    
    def process_author(author_id): 
        """
        個々のauthor_idに対して処理を実行する関数
        """
        try:
            print(author_id, "の調査")
            author = GatherAuthorData(author_id=author_id,max_workers=max_workers)
            author.run_fetch_works()
            
            author.di_calculation()
            
            profile_dict = author.gathering_author_data()
            works_data_dict = author.get_top_three_article()
            
            #profile辞書＋top_three_article
            profile_dict.update(works_data_dict)
            
            return profile_dict
        
        except Exception as e:
            logging.error(f"process_author内でエラー発生 (author_id: {author_id}): {e}", exc_info=True)
            raise  # エラーを再スローして上位で処理
        
    # 並列処理
    results_list = []
    
    with ThreadPoolExecutor(max_workers=person_num) as executor:  # max_workersは並列スレッド数
        futures = {executor.submit(process_author, author_id): author_id for author_id in creater.authors_id_list}
        for future in as_completed(futures):
            author_id = futures[future]
            try:
                result = future.result()  # 処理結果を取得
                results_list.append(result)
            except Exception as e: 
                # メインスレッドでのエラーハンドリング
                logging.error(f"{author_id} の処理中にエラーが発生しました: {e}")

    print(len(results_list))
    
    rows =[]
    for result in results_list:
        row = [str(value) for value in result.values()]
        rows.append(row)
        
    for row in rows:
        for i,each in enumerate(row):
            if len(each)>=50000:
                print("インデクス",i)
                row[i] = each[:50000]
            
    sheet_manager = SpreadsheetManager("アプリケーション", "API動作確認")
    sheet_manager.append_rows(rows)
    
   
if __name__ == "__main__":
    # 開始時間を記録
    start_time = time.time()
    
    execute()
    
    # 終了時間を記録
    end_time = time.time()
    # 処理時間を計算
    elapsed_time = end_time - start_time
    print(f"処理時間: {elapsed_time:.2f} 秒")