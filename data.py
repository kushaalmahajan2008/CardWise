import gspread
import pandas as pd

def get_data(SPREADSHEET_ID,filename,worksheet_name):
    SPREADSHEET_ID = "1NAltgEBsrDnQeqPL0nB0O3XBH4vQJ7WnR6ZPmZDbotc"
    gc = gspread.service_account(filename)
    sh = gc.open_by_key(SPREADSHEET_ID)
    worksheet = sh.worksheet(worksheet_name)
    df = pd.DataFrame(worksheet.get_all_records())
    return df