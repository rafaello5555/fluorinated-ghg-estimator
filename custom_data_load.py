
import os
import requests
import pandas as pd

def read_excel_file(excel_path, sheet_name = None):

    if sheet_name:
        df = pd.read_excel(excel_path, sheet_name, engine="openpyxl")

    else:
        df =  pd.read_excel(excel_path, engine="openpyxl")

    return df



if __name__ == "__main__":
    file_path = "l_o_freq_request_data.xlsx"
    df = read_excel_file(file_path, sheet_name="Emissions from P&T Proc by Chem")


