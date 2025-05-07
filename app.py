# app.py - Phiên bản đầy đủ + dự đoán theo địa bàn
import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import base64
import pickle

st.set_page_config(layout="wide")
SAVE_DIR = "saved_data"
os.makedirs(SAVE_DIR, exist_ok=True)

# ==== Hàm hỗ trợ ====
def read_excel_auto_header(file):
    df_all = pd.read_excel(file, None)
    if 'Chi tiết triển khai' in df_all:
        df = df_all['Chi tiết triển khai']
    else:
        df = list(df_all.values())[0]
    for i in range(5):
        if df.iloc[i].astype(str).str.contains("tên hoạt chất", case=False).any():
            df.columns = df.iloc[i]
            return df.iloc[i+1:].reset_index(drop=True)
    return df

def standardize_column_names(df):
    rename_map = {}
    for col in df.columns:
        lower_col = str(col).strip().lower()
        if ('hoạt chất' in lower_col or 'thành phần' in lower_col) and 'tên' in lower_col:
            rename_map[col] = 'Tên hoạt chất'
        elif 'nồng độ' in lower_col or 'hàm lượng' in lower_col:
            rename_map[col] = 'Nồng độ/Hàm lượng'
        elif 'nhóm' in lower_col:
            rename_map[col] = 'Nhóm thuốc'
        elif 'số lượng' in lower_col:
            rename_map[col] = 'Số lượng'
        elif 'giá' in lower_col and ('hoạch' in lower_col or 'kế hoạch' in lower_col):
            rename_map[col] = 'Giá kế hoạch'
        elif 'giá' in lower_col and ('dự' in lower_col or 'trúng' in lower_col or 'thực tế' in lower_col):
            rename_map[col] = 'Giá dự thầu'
        elif 'đường dùng' in lower_col or 'dạng bào chế' in lower_col:
            rename_map[col] = 'Đường dùng'
        elif 'nhà thầu' in lower_col:
            rename_map[col] = 'Nhà thầu trúng thầu'
        elif 'địa bàn' in lower_col:
            rename_map[col] = 'Địa bàn'
        elif 'triển khai' in lower_col or 'khách hàng' in lower_col:
            rename_map[col] = 'Tên Khách hàng phụ trách triển khai'
    df = df.rename(columns=rename_map)
    return df

def format_nhom_thuoc(value):
    try:
        number = str(value).strip()[-1]
        if number.isdigit():
            return f"Nhóm {number}"
    except:
        pass
    return "Không rõ"

def classify_group(hoatchat):
    hc = str(hoatchat).lower()
    if any(x in hc for x in ['cef', 'peni', 'mycin']): return 'Kháng sinh'
    if any(x in hc for x in ['losartan', 'amlodipin', 'clopidogrel', 'statin']): return 'Tim mạch'
    if any(x in hc for x in ['metformin', 'insulin']): return 'Đái tháo đường'
    if any(x in hc for x in ['paracetamol', 'ibu', 'diclofenac']): return 'Giảm đau'
    if any(x in hc for x in ['omeprazol', 'pantoprazol']): return 'Tiêu hóa'
    return 'Khác'

def save_file(data, name):
    with open(os.path.join(SAVE_DIR, name), 'wb') as f:
        pickle.dump(data, f)

def load_file(name):
    path = os.path.join(SAVE_DIR, name)
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return pickle.load(f)
    return None
