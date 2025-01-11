import requests

# APIのエンドポイントURL
#http://127.0.0.1:8000/

#url ="  http://44.211.68.239:8000/count_japanese/"


url = "http://127.0.0.1:8000/feach_japanese/"


# 送信するデータ
data = {
    "author_info_source": "Example Source",
    "topic_id": ["T10966"],  # リストとして修正
    "primary": True,  # フィールドを追加
    "citation_count": 20,  # 整数に修正
    "publication_year": 2020,  # 整数に修正
    "title_and_abstract_search": '("novel target" OR "new target" OR "therapeutic target")',  # フィールドを追加
    "di_calculation": False,  # ブール値に修正
    "output_sheet_name": "API動作確認"
}

# POSTリクエストを送信して結果を確認
response = requests.post(url, json=data)

# レスポンスを表示
print("Status Code:", response.status_code)
print("Response Body:", response.json())