import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

import asyncio
from api.spreadsheet_manager import SpreadsheetManager
from datetime import datetime
from pytz import timezone

# 固定のスプレッドシート名とシート名
FIXED_SPREADSHEET_NAME = "アプリケーション"
FIXED_WORKSHEET_NAME = "操作画面"

# 固定のSpreadsheetManagerインスタンスを作成
fixed_sheet_manager = SpreadsheetManager(FIXED_SPREADSHEET_NAME, FIXED_WORKSHEET_NAME)


async def append_log_async(text):
    """
    非同期でappend_logを実行する
    """
    # 日本時間のタイムゾーンを指定
    jst = timezone('Asia/Tokyo')
    current_time = datetime.now(jst)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, fixed_sheet_manager.append_row, [current_time.strftime("%Y-%m-%d %H:%M:%S"),text])


if __name__ == "__main__":
    # 使用例
    asyncio.run(append_log_async("非同期処理のログテスト"))