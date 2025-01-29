import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

from utils.common_method import get_type_counts,extract_id_from_url
import requests
from collections import Counter

class FetchAuthorEntity:
    def __init__(self,author_id):
        self.author_id = extract_id_from_url(author_id)
        self.data = self.fetch_author_json(author_id)
        
    def fetch_author_json(self,author_id):
        url = f"https://api.openalex.org/authors/{author_id}"
        retrial_num=1 #全てのリトライをカウント
        server_retrial=1 #予期せぬエラーのみカウント
        while True:
            try:
                response = requests.get(url,timeout=5)
                if response.status_code == 200:
                    # 全著者情報をJSON形式で取得
                    data = response.json()
                    return data
                else:
                    if retrial_num>8:
                        print(author_id,"の情報をauthorエンティティから収集できませんでした。")
                        return {}
                    print(author_id,"リクエストやり直し。retrial_num:",retrial_num)
                    time.sleep(retrial_num)
            except requests.exceptions.Timeout:
                if retrial_num>8:
                    print(author_id,"の情報をauthorエンティティから収集できませんでした。")
                    return {}
                print("リクエストがタイムアウトしました。再試行します。retrial_num:",retrial_num)
                time.sleep(retrial_num)
            except:
                if server_retrial>8:
                    time.sleep(15)
                    return {}
                else:
                    print("予期せぬエラー（ネットワーク接続も含む）10秒後に再接続してみます。server_retrial:",server_retrial)
                    server_retrial+=1
                    time.sleep(10)
            retrial_num+=1
    

    def extract_researcher_info(self):
        if not self.data:
            return {}
        
        return {
            "id": self.data.get("id", "N/A"),
            "display_name": self.data.get("display_name", "N/A"),
            "display_name_alternatives": self.data.get("display_name_alternatives", []),
            "ORCID": self.data.get("orcid", "N/A"),
            "Works Count": self.data.get("works_count", "N/A"),
            "cited_by_count": self.data.get("cited_by_count", "N/A"),
            "2yr Mean Citedness": self.data.get("summary_stats", {}).get("2yr_mean_citedness", "N/A"),
            "H-Index": self.data.get("summary_stats", {}).get("h_index", "N/A"),
            "I10-Index": self.data.get("summary_stats", {}).get("i10_index", "N/A"),
            "Affiliations": [
                {
                    "Institution ID": affiliation.get("institution", {}).get("id", "N/A"),
                    "Institution Name": affiliation.get("institution", {}).get("display_name", "N/A"),
                    "Country Code": affiliation.get("institution", {}).get("country_code", "N/A"),
                    "type": affiliation.get("institution", {}).get("type", "N/A"),
                    "Years": affiliation.get("years", [])
                }
                for affiliation in self.data.get("affiliations", [])
            ],
            "Last Known Institutions": [
                {
                    "Institution ID": inst.get("id", "N/A"),
                    "Institution Name": inst.get("display_name", "N/A"),
                    "Country Code": inst.get("country_code", "N/A")
                }
                for inst in self.data.get("last_known_institutions", [])
            ],
            "topics": [
                {
                    "Topic ID": topic.get("id", "N/A"),
                    "Display Name": topic.get("display_name", "N/A"),
                    "Count": topic.get("count", "N/A"),
                    "Subfield": topic.get("subfield", {}).get("display_name", "N/A"),
                    "Field": topic.get("field", {}).get("display_name", "N/A"),
                    "Domain": topic.get("domain", {}).get("display_name", "N/A")
                }
                for topic in self.data.get("topics", [])
            ],
            "counts_by_year": self.data.get("counts_by_year", [])
        }

    def calculate_type_counts(self):
        researcher_info = self.extract_researcher_info()
        affiliations = researcher_info.get("Affiliations", [])
        if not affiliations:
            return {}
        type_list = [affiliation.get("type", "N/A") for affiliation in affiliations]
        type_counts = Counter(type_list)
        return dict(type_counts)

    def calculate_country_counts(self):
        researcher_info = self.extract_researcher_info()
        affiliations = researcher_info.get("Affiliations", [])
        if not affiliations:
            return {}
        country_list = [affiliation.get("Country Code", "N/A") for affiliation in affiliations]
        country_counts = Counter(country_list)
        return dict(country_counts)

    def calculate_growth_rates(self):
        researcher_info = self.extract_researcher_info()
        data = researcher_info.get("counts_by_year", [])
        growth_rates = []
        for i in range(min(3, len(data) - 1)):
            current = data[i]
            prev = data[i + 1]
            current_cited = current.get("cited_by_count", 0)
            prev_cited = prev.get("cited_by_count", 0)
            if prev_cited != 0:
                growth_rate = round((current_cited - prev_cited) / prev_cited * 100, 2)
            else:
                growth_rate = ""
            growth_rates.append({
                "year": current.get("year", "N/A"),
                "growth_rate": growth_rate
            })
        return growth_rates

    def calculate_career_years(self):
        researcher_info = self.extract_researcher_info()
        affiliations = researcher_info.get("Affiliations", [])
        if not affiliations:
            return ""
        all_years = [year for affiliation in affiliations for year in affiliation.get("Years", [])]
        if not all_years:
            return ""
        min_year = min(all_years)
        max_year = max(all_years)
        return max_year - min_year + 1  # 1年分加算して年数に変換

    # ゲッターメソッドの実装

    def get_author_id(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("id", "N/A")

    def get_display_name(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("display_name", "N/A")

    def get_alternative_names(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("display_name_alternatives", [])

    def get_orcid(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("ORCID", "N/A")

    def get_works_count(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("Works Count", "N/A")

    def get_cited_by_count(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("cited_by_count", "N/A")

    def get_two_year_mean_citedness(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("2yr Mean Citedness", "N/A")

    def get_h_index(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("H-Index", "N/A")

    def get_i10_index(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("I10-Index", "N/A")

    def get_affiliations(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("Affiliations", [])

    def get_affiliations_for_display(self):
        affiliations = self.get_affiliations()
        return "\n".join(
            f"{affiliation['Institution Name']}: {', '.join(map(str, affiliation['Years']))}"
            for affiliation in affiliations
        )

    def get_last_institution_names(self):
        researcher_info = self.extract_researcher_info()
        return [
            inst.get("Institution Name", "N/A") 
            for inst in researcher_info.get("Last Known Institutions", [])
        ]

    def get_country_codes(self):
        researcher_info = self.extract_researcher_info()
        return [
            inst.get("Country Code", "N/A") 
            for inst in researcher_info.get("Last Known Institutions", [])
        ]

    def get_type_counts(self):
        return self.calculate_type_counts()

    def get_country_counts(self):
        return self.calculate_country_counts()

    def get_growth_rates(self):
        return self.calculate_growth_rates()

    def get_career_years(self):
        return self.calculate_career_years()

    def get_topics(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("topics", [])

    def get_counts_by_year(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("counts_by_year", [])
        
if __name__ == "__main__":
    # 使用例
    start_time = time.time()  # 実行開始時刻を記録
    
    author_id = "https://openalex.org/A5038138665"
    author_entity = FetchAuthorEntity(author_id)
    
    #print(author_entity.calculate_type_counts())
    # print("Author ID:", author_entity.get_author_id())
    # print("Display Name:", author_entity.get_display_name())
    # print("Alternative Names:", author_entity.get_alternative_names())
    # print("ORCID:", author_entity.get_orcid())
    # print("Works Count:", author_entity.get_works_count())
    # print("Cited By Count:", author_entity.get_cited_by_count())
    # print("2yr Mean Citedness:", author_entity.get_two_year_mean_citedness())
    print("H-Index:", author_entity.get_h_index())
    # print("I10-Index:", author_entity.get_i10_index())
    #print("Affiliations:", len(author_entity.get_affiliations()))
    # print("Last Institution Names:", author_entity.get_last_institution_names())
    # print("Country Codes:", author_entity.get_country_codes())
    # print("Type Counts:", author_entity.get_type_counts())
    print("Country Counts:", author_entity.get_country_counts())
    # print("Growth Rates:", author_entity.get_growth_rates())
    #print("Career Years:", author_entity.get_career_years())
    # print("Topics:", author_entity.get_topics())
    # print("Counts by Year:", author_entity.get_counts_by_year())
    
    end_time = time.time()  # 実行終了時刻を記録
    elapsed_time = end_time - start_time  # 経過時間を計算
    #print(f"プログラムの実行時間: {elapsed_time:.2f} 秒")