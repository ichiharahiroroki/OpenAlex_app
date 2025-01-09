#様々なクラスメソッドを保管する場所
#スプレットシートを開くclass（シート名、ワークシート名）
import gspread
from google.oauth2.service_account import Credentials
import os

class SpreadsheetManager:
    def __init__(self, spreadsheet_name, worksheet_name):
        # 認証情報ファイルのパス
        base_dir = os.path.dirname(os.path.dirname(__file__))  # スクリプトのディレクトリを取得
        base_dir = f"{base_dir}/config"
        GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        self.service_account_file = os.path.join(base_dir, GOOGLE_APPLICATION_CREDENTIALS)
        # 必要なスコープ
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        # 認証情報の生成
        self.creds = Credentials.from_service_account_file(
            self.service_account_file,
            scopes=self.scopes
        )
        # gspreadクライアントの生成
        self.client = gspread.authorize(self.creds)
        # スプレッドシートとワークシートを開く
        self.sheet = self.client.open(spreadsheet_name).worksheet(worksheet_name)

    # ここに他の操作を追加するメソッドを定義できます
    def get_all_values(self):
        """1行目（ヘッダー行）を除外してすべての値を取得する"""
        all_values = self.sheet.get_all_values()
        return all_values[1:]  # 1行目を除外
        

    def append_rows(self, rows):
        """与えられたリストのリストをスプレッドシートに追加します。"""
        self.sheet.append_rows(rows, value_input_option='USER_ENTERED')
    
    def set_headers_if_empty(self, headers):
        """スプレッドシートの1行目が空白の場合にヘッダーを設定します。"""
        first_row = self.sheet.row_values(1)
        if not any(first_row):  # 1行目が全て空白かどうかを確認
            self.sheet.update(range_name='A1', values=[headers])

    def get_all_links(self):
        """スプレッドシート内の '記事リンク' カラムの全てのリンクを取得します。"""
        # 1行目（ヘッダー行）を取得
        headers = self.sheet.row_values(1)
        
        # '記事リンク' カラムのインデックスを取得
        try:
            col_index = headers.index("記事リンク") + 1  # gspreadは1ベースインデックス
        except ValueError:
            raise ValueError("'記事リンク' というカラムが見つかりません。")

        # '記事リンク' カラムの全てのデータを取得
        return self.sheet.col_values(col_index)[1:]  # ヘッダー行を除外


    def get_last_50_titles(self):
        """スプレッドシート内の 'タイトル' カラムの下から50個のテキストを取得します。"""
        # 1行目（ヘッダー行）を取得
        headers = self.sheet.row_values(1)
        
        # 'タイトル' カラムのインデックスを取得
        try:
            col_index = headers.index("タイトル") + 1  # gspreadは1ベースインデックス
        except ValueError:
            print("'タイトル' というカラムが見つかりません。")
            return None
            #raise ValueError("'タイトル' というカラムが見つかりません。")
            

        # 'タイトル' カラムの全てのデータを取得
        titles = self.sheet.col_values(col_index)[1:]  # ヘッダー行を除外
        
        # 取得したデータが50個以上ある場合は、下から50個を返す
        if len(titles) > 50:
            return titles[-50:]
        else:
            return titles
        # 下から50個のテキストを取得
        
    def clear_rows_from_third(self):
        """3行目以降のすべてのデータをクリアにする"""
        # ワークシートの総行数を取得
        total_rows = len(self.sheet.get_all_values())

        # 3行目以降が存在する場合のみクリア
        if total_rows > 2:
            range_to_clear = f"3:{total_rows}"  # 3行目から最終行までの範囲を指定
            self.sheet.batch_clear([range_to_clear])
    
    
    
    def get_rows_by_columns(self, column_names):
        """
        指定されたカラム名からすべての行を取得し、2次元リストとして返す。
        
        :param column_names: 取得するカラム名のリスト
        :return: 各行のデータを含む2次元リスト
        """
        headers = self.sheet.row_values(1)
        column_indices = []
        for col_name in column_names:
            try:
                col_index = headers.index(col_name) + 1  # gspreadは1ベースインデックス
                column_indices.append(col_index)
            except ValueError:
                raise ValueError(f"'{col_name}' というカラムが見つかりません。")

        rows = self.sheet.get_all_values()[1:]  # ヘッダー行を除外したすべての行を取得
        filtered_rows = []
        
        for row in rows:
            filtered_row = [row[i-1] for i in column_indices]  # 必要なカラムだけを抽出
            filtered_rows.append(filtered_row)
        
        return filtered_rows
    
    
    def get_latest_value_from_column(self, column_name):
        """
        指定されたカラム名の中から一番下の最新の値を抽出します。

        :param column_name: 抽出するカラム名
        :return: 一番下の最新の値
        """
        headers = self.sheet.row_values(1)
        try:
            col_index = headers.index(column_name) + 1
        except ValueError:
            raise ValueError(f"'{column_name}' というカラムが見つかりません。")
        
        values = self.sheet.col_values(col_index)[1:]  # ヘッダー行を除外
        if values:
            return values[-1]  # 一番下の最新の値を返す
        else:
            return None

        
        


# 使用例
# spreadsheet_manager = SpreadsheetManager("テスト", "助成金リスト")
 # 従来の方法でワークシートに行を追加
# spreadsheet_manager.sheet.append_row(["データ1", "データ2", "データ3"])

# if __name__ == "__main__":
 
# # 使用例
#     spreadsheet_manager = SpreadsheetManager("スタートアップ情報収集", "検索方式")
#     print(spreadsheet_manager.get_all_links())