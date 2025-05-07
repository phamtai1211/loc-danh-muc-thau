import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Pharma Tender Analysis", layout="wide")
st.title("💊 Hệ Thống Lọc & Phân Tích Danh Mục Thầu Bệnh Viện")

# --- Utility functions ---
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
    return f"{int(n):,}" if pd.notna(n) and isinstance(n, (int, float)) else n

# --- Load saved data ---
if 'file2_data' not in st.session_state:
    st.session_state['file2_data'] = None
if 'file3_data' not in st.session_state:
    st.session_state['file3_data'] = None

# --- Sidebar: Choose analysis function ---
option = st.sidebar.radio("Chọn chức năng", ["Lọc danh mục thầu", "Phân tích danh mục BV", "Phân tích danh mục trúng thầu"])

# --- Upload files ---
st.subheader("📁 Tải lên file")
file1 = st.file_uploader("Tải lên file Danh mục chính (mời thầu/trúng thầu)", type=["xls", "xlsx"])
file2 = st.file_uploader("(Tuỳ chọn) Danh sách sản phẩm của công ty bạn", type=["xls", "xlsx"])
file3 = st.file_uploader("(Tuỳ chọn) File địa bàn - khách hàng phụ trách", type=["xls", "xlsx"])

if file2:
    df2 = read_excel_dynamic_header(file2)
    st.session_state['file2_data'] = df2
if file3:
    df3 = pd.read_excel(file3, sheet_name='Chi tiết triển khai', header=0)
    df3 = df3[df3.iloc[:, 3].isna()]  # Bỏ dòng có dữ liệu ở cột D
    st.session_state['file3_data'] = df3

# --- Load main file ---
if file1:
    df1 = read_excel_dynamic_header(file1)
    if df1.empty:
        st.error("❌ Không thể đọc dữ liệu từ file Danh mục chính.")
    else:
        df1.columns = df1.columns.str.strip()
        df1['Tên hoạt chất chuẩn'] = df1['Tên hoạt chất/ Tên thành phần của thuốc'].fillna(df1.get('Tên hoạt chất', ''))
        df1['Tên hoạt chất chuẩn'] = df1['Tên hoạt chất chuẩn'].str.strip().str.lower()

        if option == "Phân tích danh mục BV":
            st.subheader("📊 Phân tích danh mục mời thầu")
            if 'Số lượng' in df1.columns:
                df1['Số lượng'] = pd.to_numeric(df1['Số lượng'], errors='coerce')
            if 'Giá kế hoạch' in df1.columns:
                df1['Giá kế hoạch'] = pd.to_numeric(df1['Giá kế hoạch'], errors='coerce')
            df1['Trị giá thầu'] = df1['Số lượng'] * df1.get('Giá kế hoạch', 0)
            df1['Trị giá thầu'] = df1['Trị giá thầu'].fillna(0)
            
            top_hoatchat = df1.groupby('Tên hoạt chất chuẩn')['Số lượng'].sum().nlargest(10).reset_index()
            top_hoatchat['Số lượng'] = top_hoatchat['Số lượng'].apply(format_number)

            st.markdown("### 🔥 Top 10 hoạt chất theo số lượng")
            st.dataframe(top_hoatchat, use_container_width=True)

        elif option == "Phân tích danh mục trúng thầu":
            st.subheader("🏥 Phân tích danh mục TRÚNG thầu")
            if 'Giá dự thầu' in df1.columns:
                df1['Giá dự thầu'] = pd.to_numeric(df1['Giá dự thầu'], errors='coerce')
                df1['Trị giá thầu'] = df1['Số lượng'] * df1['Giá dự thầu']

            if 'Nhà thầu trúng thầu' in df1.columns:
                top_nhathau = df1.groupby('Nhà thầu trúng thầu')['Trị giá thầu'].sum().nlargest(20).reset_index()
                top_nhathau['Trị giá thầu'] = top_nhathau['Trị giá thầu'].apply(format_number)
                st.markdown("### 🏆 Top 20 nhà thầu trúng thầu theo trị giá")
                st.dataframe(top_nhathau, use_container_width=True)

        elif option == "Lọc danh mục thầu":
            st.subheader("🔍 Lọc danh mục theo sản phẩm công ty và địa bàn")
            if st.session_state['file2_data'] is not None:
                df_sanpham = st.session_state['file2_data']
                df_sanpham.columns = df_sanpham.columns.str.strip()
                ten_sp = df_sanpham.iloc[:, 0].dropna().str.lower().unique()
                df1['Tên hoạt chất chuẩn'] = df1['Tên hoạt chất chuẩn'].str.lower()
                df_matched = df1[df1['Tên hoạt chất chuẩn'].isin(ten_sp)]

                st.success(f"🔎 Lọc được {len(df_matched)} dòng khớp với danh sách sản phẩm công ty.")
                st.dataframe(df_matched, use_container_width=True)
            else:
                st.warning("📌 Bạn cần cung cấp File 2 để sử dụng chức năng này.")
