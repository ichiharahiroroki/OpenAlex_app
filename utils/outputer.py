from datetime import datetime
from utils.async_log_to_sheet import append_log_async

async def output_to_sheet(sheet_manager,header,rows):
    attempt = 1
    max_retries = 6
    while attempt < max_retries:
        try:
            sheet_manager.sheet.update('A1',[header])
            break
        except Exception as e:
            await append_log_async(f"headerの追加をやり直す。エラー:{e}") 
    
    
    for i in range(0, len(rows), 1000):
        attempt = 1
        max_retries = 6
        while attempt < max_retries:
            try:
                sheet_manager.append_rows(rows[i:i+1000])
                await append_log_async(f"[{i}:{i+1000}]を追加しました。") 
                break
            except Exception as e:
                await append_log_async(f"[{i}:{i+1000}]をやり直す。エラー:{e}") 
            attempt+=1
            
        if attempt < max_retries:
            continue
        else:
            raise ValueError(f"スプレットシートに追加できませんでした。エラー:{e}")
            

def truncate_and_report_long_cells(data, limit=50000):
    try:
        for i, row in enumerate(data):
            for j, cell in enumerate(row):
                if len(cell) > limit:
                    data[i][j] = cell[:limit]  # セルの内容をlimit文字に切り捨て
    except Exception as e:
        raise ValueError(f"truncate_and_report_long_cells関数の使い方に問題があります。エラー:{e}")

    return data


#スプレットシートにアップするために、各要素はstr型の２次元リストに変換。
def dict_list_to_string_rows(dict_list):
    rows =[]
    for result in dict_list:
        row = [str(value) for value in result.values()]
        rows.append(row)
    return rows


def adjust_indicators(dict_list,add_key_list=[]):
    # 新しい辞書リストを格納するリスト
    new_list = []
    header = ["研究者ID", "名前", "最新の所属", "キャリア年数", "出版数", "全ての出版の被引用数", "H-Index", "過去5年H-index", "企業との共著数", "first論文数", "対応(last)論文数", "DI0.8以上のworks数", "世界ランキング","総数","STP.論文ID", "STP.論文タイトル", "STP.論文出版年月", "STP.論文被引用数","CTP.論文ID", "CTP.論文タイトル", "CTP.論文出版年月", "CTP.論文被引用数"]
        
    # 必要なキー
    need_keys = [
        "researcher_id", "name", "latest_affiliation",
        "career_years", "works_count", "total_works_citations",
        "h_index", "last_5_year_h_index", "coauthor_from_company_count", "first_paper_count",
        "corresponding_paper_count", "disruption_index_above_08",
        "世界ランキング","総数","条件論文1:ID","条件論文1:タイトル","条件論文1:出版年月","条件論文1:被引用数",
        "論文1:ID","論文1:タイトル","論文1:出版年月","論文1:被引用数"
        # "論文2:ID","論文2:タイトル","論文2:出版年月","論文2:被引用数",
        # "論文3:ID","論文3:タイトル","論文3:出版年月","論文3:被引用数",
    ]
    
    #add_key_list に含まれるキーを need_keys に追加（重複を避ける）
    need_keys.extend([key for key in add_key_list if key not in need_keys])
    
    # 入力リスト内の各辞書について処理
    for original_dict in dict_list:
        # 新しい辞書を作成して、必要なキーとその値だけをコピー
        new_dict = {key: original_dict[key] for key in need_keys if key in original_dict}
        new_list.append(new_dict)
    
    return header ,new_list



def sort_dict_list_by_key(dict_list, sort_key):
    """
    辞書リストを指定したキーの値で降順にソートする関数。

    :param dict_list: 辞書リスト (List[dict])
    :param sort_key: ソートの基準となるキー名 (str)
    :return: ソートされた辞書リスト (List[dict])
    """
    try:
        sorted_list = sorted(dict_list, key=lambda x: x.get(sort_key, 0), reverse=True)
        return sorted_list
    except Exception as e:
        raise Exception(f"ソートに失敗しました。エラー: {e}")