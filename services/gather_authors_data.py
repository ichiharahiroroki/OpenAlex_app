import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from api.spreadsheet_manager import SpreadsheetManager
from config.secret_manager import SecretManager
from utils.common_method import get_type_counts,extract_id_from_url
from gather_author_data_libs.create_author_profile import create_author_profile
from utils.calculater import Calculater
from utils.fetch_result_parser import OpenAlexResultParser, author_dict_list_to_author_work_data_list
from api.list_openAlex_fetcher import OpenAlexPagenationDataFetcher
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ThreadPoolExecutor, as_completed
from data_class.researcher_data import ResearcherData,AuthorProfileData,AuthorWorkData
from typing import List, Dict

class GatherAuthorData:
    def __init__(self,author_id,max_workers=1,found_date=""):
        self.article_dict_list = []
        self.author_id = extract_id_from_url(author_id)
        self.found_date = found_date
        self.max_workers = max_workers
    def run_fetch_works(self):
        if not self.found_date:
            endpoint_url = "https://api.openalex.org/works" 
            
            params = {
                "filter": f'author.id:{self.author_id}', #publication_date:<{found_date}>,#type:article',publication_year:2006'
                "page": 1,
                "per_page": 200,
                # "mailto":"ichiharabox@gmail.com"
            }#type_crossref: "journal-article" #publication_date:"2018-02-13"#cited_by_count:>20#type_crossref:journal-article
            
            fetcher = OpenAlexPagenationDataFetcher(endpoint_url, params, self.author_id, max_works=self.max_workers, only_japanese=False, correspondingR=False)
            _, self.article_dict_list = OpenAlexResultParser.works_dict_list_from_works_results(fetcher.all_results)

        else:
            print("現在、found_dateの対応が完了していません。")
            sys.exit(1)
    
    def di_calculation(self):
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_article = {executor.submit(Calculater.calculate_disruption_index_for_article, article): article 
                for article in self.article_dict_list
                }
                for future in as_completed(future_to_article):
                    article = future_to_article[future]
                    try:
                        updated_article = future.result()
                        # 計算された disruption_index を元の article_dict_list に戻す
                        article.update(updated_article)
                    except Exception as exc:
                        print(f"{article['ID']} の処理中にエラーが発生しました#D-indexとimpactの計算: {exc}")
       
   
    def gathering_author_data(self,get_type_counts_info=False):
        author_dict_list = OpenAlexResultParser.author_dict_list_from_article_dict_list(self.article_dict_list, only_single_author_id=self.author_id)
        authorWoorkData_list = author_dict_list_to_author_work_data_list(author_dict_list)
        profile = create_author_profile(authorWoorkData_list)
        
        if get_type_counts_info:
            type_crossref_dict = get_type_counts(self.author_id,type="type_crossref",found_date=self.found_date)
            type_dict = get_type_counts(self.author_id,type="type",found_date=self.found_date)
            profile.article_type_crossref_dict = type_crossref_dict
            profile.article_type_dict = type_dict
            
        #profileデータ→辞書
        profile_dict = profile.to_dict()
        
        return profile_dict
        
        
    def get_top_three_article(self):
        """
        article_dict_list内の各辞書を評価し、impact_indexが存在して0より大きいものを優先的に、
        そうでないものはCited By Countでソートして上位3つを抽出する関数。

        Parameters:
            article_dict_list (list): 各辞書が記事情報を含むリスト。

        Returns:
            list: 上位3つの辞書リスト。
        """
        # impact_indexが存在し、かつ0より大きい記事を収集
        articles_with_impact = []
        articles_without_impact = []

        for article in self.article_dict_list:
            impact = article.get("impact_index")
            try:
                impact_val = float(impact)
                if impact_val > 0:
                    articles_with_impact.append(article)
                else:
                    articles_without_impact.append(article)
            except (ValueError, TypeError):
                # impact_indexが""やNoneなど数値に変換できない場合
                articles_without_impact.append(article)

        # impact_indexがある記事をimpact_indexの降順でソート
        articles_with_impact_sorted = sorted(
            articles_with_impact,
            key=lambda x: float(x["impact_index"]),
            reverse=True
        )

        # impact_indexがない記事をCited By Countの降順でソート
        articles_without_impact_sorted = sorted(
            articles_without_impact,
            key=lambda x: int(x.get("Cited By Count", 0)),
            reverse=True
        )

        # 上位3つを抽出
        top_articles = articles_with_impact_sorted[:3]

        # impact_indexが0より大きい記事が3つ未満の場合、Cited By Countで埋める
        if len(top_articles) < 3:
            needed = 3 - len(top_articles)
            top_articles.extend(articles_without_impact_sorted[:needed])

        top_articles_dict_list = OpenAlexResultParser.author_dict_list_from_article_dict_list(top_articles,only_single_author_id=self.author_id)
        
        works_data = {}
        for i, article in enumerate(top_articles_dict_list[:3], start=1):  # 1から始める
            works_data[f"論文{i}:Article ID"] = article.get("Article ID", "N/A")
            works_data[f"論文{i}:名前"] = article.get("Author Name", "N/A")
            works_data[f"論文{i}:所属"] = article.get("Affiliation", "N/A")
            works_data[f"論文{i}:Country Codes"] = article.get("Country Codes", "N/A")
            works_data[f"論文{i}:Corresponding Authors"] = any(
                extract_id_from_url(art.get("id")) == self.author_id for art in article.get("Corresponding Authors", [])
            )
            works_data[f"論文{i}:Author Position"] = article.get("Author Position", "N/A")
            works_data[f"論文{i}:Corresponding Authors name"] = [
                author['name'] for author in article.get("Corresponding Authors", [])
            ]
            works_data[f"論文{i}:Cited By Count"] = article.get("Referenced Works Count", 0)
            works_data[f"論文{i}:Total Citations"] = article.get("Cited By Count", 0)
            works_data[f"論文{i}:D-Index"] = article.get("Disruption Index", -200)
            works_data[f"論文{i}:impact_index"] = article.get("impact_index", -200.0)
            works_data[f"論文{i}:Primary Topic"] = article.get("Primary Topic", "N/A")
            works_data[f"論文{i}:Topics"] = article.get("Topics", [])
            works_data[f"論文{i}:Publication Year"] = article.get("Publication Year", 0)
            works_data[f"論文{i}:Publication Date"] = article.get("Publication Date", "N/A")
            works_data[f"論文{i}:Landing Page URL"] = article.get("Landing Page URL", "N/A")
            works_data[f"論文{i}:Authors"] = article.get("Authors", "N/A")
            works_data[f"論文{i}:Keywords"] = article.get("Keywords", "N/A")
            works_data[f"論文{i}:Grants"] = article.get("Grants", [])
        
        return works_data
        
   
    

if __name__ == "__main__":
    
    secret = SecretManager()
    sheet_manager = SpreadsheetManager("アプリケーション", "API動作確認")

    # 開始時間を記録
    start_time = time.time()

    author = GatherAuthorData(author_id="https://openalex.org/authors/A5038138665")
    author.run_fetch_works()
    print(len(author.article_dict_list))
    #author.di_calculation(max_workers=16)
    profile_dict = author.gathering_author_data(True)
    works_data = author.get_top_three_article()
    
    #profile辞書＋top_three_article
    profile_dict.update(works_data)
    
    # 終了時間を記録
    end_time = time.time()
    # 処理時間を計算
    elapsed_time = end_time - start_time
    print(f"処理時間: {elapsed_time:.2f} 秒")
        
    
    row = [str(value) for value in profile_dict.values()]
    rows = [row]  # `append_rows`はリストのリストを期待する
    for row in rows:
        for i,each in enumerate(row):
            if len(each)>=50000:
                print("インデクス",i)
                row[i] = each[:50000]
            
    sheet_manager.append_rows(rows)