import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

import asyncio
from api.spreadsheet_manager import SpreadsheetManager

async def append_log_async(sheet_manager, text):
    """
    非同期でappend_logを実行する
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, sheet_manager.append_log, text)


if __name__ == "__main__":

    # 使用例
    sheet_manager = SpreadsheetManager("アプリケーション", "API動作確認")
    asyncio.run(append_log_async(sheet_manager, "非同期処理のログテスト"))