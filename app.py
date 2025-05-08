import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Pharma Tender Analysis", layout="wide")
st.title("💊 Hệ Thống Lọc & Phân Tích Danh Mục Thầu Bệnh Viện")

# -------------------- HÀM TIỆN ÍCH --------------------
@st.cache_data
def read_excel_dynamic_header(file):
    for header in range(5):
        try:
            df = pd.read_excel(file, header=header)
            if df.columns.str.contains("\w").sum() >= 3:
                return df
        except Exception:
            continue
    return pd.DataFrame()

def format_number(n):
    try:
        return f"{int(n):,}"
    except:
        return n

def extract_group(value):
    if pd.isna(value): return ""
    value = str(value).strip().lower()
    for g in ["1", "2", "3", "4", "5"]:
        if g in value:
            return f"Nhóm {g}"
    return "Khác"

# -------------------- KHỞI TẠO SESSION --------------------
if 'file2_data' not in st.session_state:
    st.session_state['file2_data'] = None
if 'file3_data' not in st.session_state:
    st.session_state['file3_data'] = None

# -------------------- TẢI FILE --------------------
st.sidebar.header("🔧 Chọn chức năng")
option = st.sidebar.radio("", ["Lọc danh mục thầu", "Phân tích danh mục BV", "Phân tích danh mục trúng thầu"])

file1 = st.file_uploader("📂 File 1: Danh mục chính (mời/trúng thầu)", type=["xls", "xlsx"])
file2 = st.file_uploader("📂 File 2: Sản phẩm nội bộ công ty", type=["xls", "xlsx"])
file3 = st.file_uploader("📂 File 3: Địa bàn & Khách hàng phụ trách", type=["xls", "xlsx"])

if file2:
    df2 = read_excel_dynamic_header(file2)
    st.session_state['file2_data'] = df2
if file3:
    df3 = pd.read_excel(file3, sheet_name='Chi tiết triển khai', header=0)
    df3 = df3[df3.iloc[:, 3].isna()]
    st.session_state['file3_data'] = df3

# -------------------- ĐỌC FILE CHÍNH --------------------
if file1:
    df1 = read_excel_dynamic_header(file1)
    df1.columns = df1.columns.str.strip()
    if 'Tên hoạt chất' not in df1.columns:
        match_col = [col for col in df1.columns if "tên hoạt chất" in col.lower() or "thành phần" in col.lower()]
        if match_col:
            df1.rename(columns={match_col[0]: 'Tên hoạt chất'}, inplace=True)
    if 'Nồng độ/hàm lượng' not in df1.columns:
        match_col = [col for col in df1.columns if "hàm lượng" in col.lower()]
        if match_col:
            df1.rename(columns={match_col[0]: 'Nồng độ/hàm lượng'}, inplace=True)
    if 'Nhóm thuốc' not in df1.columns:
        match_col = [col for col in df1.columns if "nhóm" in col.lower()]
        if match_col:
            df1.rename(columns={match_col[0]: 'Nhóm thuốc'}, inplace=True)

    df1['Nhóm thuốc'] = df1['Nhóm thuốc'].apply(extract_group)
    df1['Số lượng'] = pd.to_numeric(df1.get('Số lượng', 0), errors='coerce')

    if option == "Phân tích danh mục BV":
        st.header("📊 Phân tích Danh mục mời thầu")
        df1['Giá kế hoạch'] = pd.to_numeric(df1.get('Giá kế hoạch', 0), errors='coerce')
        df1['Trị giá thầu'] = df1['Số lượng'] * df1['Giá kế hoạch']

        top10 = df1.groupby('Tên hoạt chất')['Số lượng'].sum().nlargest(10).reset_index()
        top10['Số lượng'] = top10['Số lượng'].apply(format_number)
        st.subheader("🔥 Top 10 hoạt chất theo số lượng")
        st.dataframe(top10)

        group_ratio = df1.groupby('Nhóm thuốc')['Số lượng'].sum()
        total_qty = group_ratio.sum()
        df_ratio = (group_ratio / total_qty * 100).round(2).reset_index(name='% Số lượng')
        st.subheader("📌 Tỉ trọng theo Nhóm thuốc")
        st.dataframe(df_ratio)

    elif option == "Phân tích danh mục trúng thầu":
        st.header("🏥 Phân tích Danh mục TRÚNG thầu")
        df1['Giá dự thầu'] = pd.to_numeric(df1.get('Giá dự thầu', 0), errors='coerce')
        df1['Trị giá thầu'] = df1['Số lượng'] * df1['Giá dự thầu']
        top20 = df1.groupby('Nhà thầu trúng thầu')['Trị giá thầu'].sum().nlargest(20).reset_index()
        top20['Trị giá thầu'] = top20['Trị giá thầu'].apply(format_number)
        st.dataframe(top20)

    elif option == "Lọc danh mục thầu":
        st.header("🔍 Lọc Danh mục có thể tham gia")
        df2 = st.session_state['file2_data']
        df3 = st.session_state['file3_data']

        if df2 is not None:
            df2.columns = df2.columns.str.strip()
            if 'Tên hoạt chất' not in df2.columns:
                df2.rename(columns={df2.columns[0]: 'Tên hoạt chất'}, inplace=True)
            df_merged = df1.merge(df2[['Tên hoạt chất']], on='Tên hoạt chất', how='left', indicator=True)
            df_result = df_merged[df_merged['_merge'] == 'both'].copy()
            df_result.drop(columns=['_merge'], inplace=True)

            if df3 is not None:
                df3.columns = df3.columns.str.strip()
                df3.rename(columns={
                    df3.columns[0]: 'Miền',
                    df3.columns[1]: 'Vùng',
                    df3.columns[2]: 'Tỉnh',
                    df3.columns[4]: 'BV/SYT',
                    df3.columns[5]: 'Địa bàn',
                    df3.columns[10]: 'Tên sản phẩm',
                    df3.columns[38]: 'Tên Khách hàng phụ trách'
                }, inplace=True)

                # Giao diện lọc theo Miền - Vùng - Tỉnh - BV
                mien = st.selectbox("Chọn Miền", df3['Miền'].dropna().unique())
                vung = st.selectbox("Chọn Vùng", df3[df3['Miền'] == mien]['Vùng'].dropna().unique())
                tinh = st.selectbox("Chọn Tỉnh", df3[df3['Vùng'] == vung]['Tỉnh'].dropna().unique())
                bvsyt = st.selectbox("Chọn SYT/BV", df3[df3['Tỉnh'] == tinh]['BV/SYT'].dropna().unique())

                df3_filtered = df3[df3['BV/SYT'] == bvsyt]
                df_final = df_result.merge(df3_filtered[['Tên sản phẩm', 'Địa bàn', 'Tên Khách hàng phụ trách']],
                                           left_on='Tên hoạt chất', right_on='Tên sản phẩm', how='left')
                st.success(f"✅ Lọc được {len(df_final)} dòng phù hợp tại {bvsyt}")
                st.dataframe(df_final)
            else:
                st.warning("⚠️ Bạn chưa tải File 3 nên không có thông tin địa bàn & khách hàng phụ trách.")
                st.dataframe(df_result)
        else:
            st.warning("⚠️ Vui lòng tải File 2 (sản phẩm công ty) để sử dụng chức năng lọc.")
