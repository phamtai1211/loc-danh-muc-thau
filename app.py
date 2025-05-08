import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Phân tích danh mục thầu bệnh viện", layout="wide")

# ---------- Hàm tiện ích ----------
def format_number(x):
    try:
        return f"{int(x):,}"
    except:
        return x

def get_column_name(possible_names, df):
    for name in possible_names:
        for col in df.columns:
            if name.lower() in col.lower():
                return col
    return None

# ---------- Upload File ----------
st.title("🧪 Hệ Thống Lọc & Phân Tích Danh Mục Thầu Bệnh Viện")

file1 = st.file_uploader("Tải lên File 1: Danh mục chính mời thầu (DM)", type=["xls", "xlsx"])
file2 = st.file_uploader("Tải lên File 2: Danh mục sản phẩm công ty", type=["xls", "xlsx"])
file3 = st.file_uploader("Tải lên File 3: Địa bàn & Khách hàng phụ trách", type=["xls", "xlsx"])

if file1 and file2:
    df1 = pd.read_excel(file1, header=None)
    df2 = pd.read_excel(file2)

    # Tìm dòng tiêu đề hợp lý trong file1
    for i in range(5):
        if df1.iloc[i].isnull().sum() < len(df1.columns) - 2:
            df1.columns = df1.iloc[i]
            df1 = df1.iloc[i + 1:]
            break

    df1 = df1.reset_index(drop=True)

    col_ten_hoat_chat = get_column_name(["hoạt chất", "thành phần"], df1)
    col_nhom_thuoc = get_column_name(["nhóm thuốc"], df1)
    col_soluong = get_column_name(["số lượng"], df1)
    col_gia_ke_hoach = get_column_name(["giá kế hoạch", "giá dự thầu"], df1)

    if not all([col_ten_hoat_chat, col_nhom_thuoc, col_soluong, col_gia_ke_hoach]):
        st.error("❌ Không tìm thấy đủ cột cần thiết trong File 1.")
    else:
        df1[col_soluong] = pd.to_numeric(df1[col_soluong], errors="coerce").fillna(0)
        df1[col_gia_ke_hoach] = pd.to_numeric(df1[col_gia_ke_hoach], errors="coerce").fillna(0)

        # Thêm cột trị giá thầu
        df1["Trị giá thầu"] = df1[col_soluong] * df1[col_gia_ke_hoach]

        # Tiêu chuẩn hóa tên nhóm thuốc
        df1[col_nhom_thuoc] = df1[col_nhom_thuoc].astype(str).str.extract(r'(\d)').fillna('Khác')
        df1[col_nhom_thuoc] = "Nhóm " + df1[col_nhom_thuoc]

        # Nếu có File 3 thì lọc theo địa bàn
        if file3:
            try:
                df3 = pd.read_excel(file3, sheet_name="Chi tiết triển khai", header=0)
                df3 = df3[df3.iloc[:, 3].isnull()]  # Bỏ dòng có dữ liệu ở cột D

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    mien = st.selectbox("Chọn Miền", sorted(df3.iloc[:, 0].dropna().unique()))
                with col2:
                    vung = st.selectbox("Chọn Vùng", sorted(df3[df3.iloc[:, 0] == mien].iloc[:, 1].dropna().unique()))
                with col3:
                    tinh = st.selectbox("Chọn Tỉnh", sorted(df3[(df3.iloc[:, 0] == mien) & (df3.iloc[:, 1] == vung)].iloc[:, 2].dropna().unique()))
                with col4:
                    sytbv = st.selectbox("Chọn SYT/BV", sorted(df3[(df3.iloc[:, 2] == tinh)].iloc[:, 4].dropna().unique()))

                df3_filtered = df3[(df3.iloc[:, 0] == mien) &
                                   (df3.iloc[:, 1] == vung) &
                                   (df3.iloc[:, 2] == tinh) &
                                   (df3.iloc[:, 4] == sytbv)]

                list_sanpham = df3_filtered.iloc[:, 10].dropna().astype(str).str.strip().unique()
                df2_filtered = df2[df2[df2.columns[0]].astype(str).str.strip().isin(list_sanpham)]

            except Exception as e:
                st.error(f"Lỗi khi xử lý File 3: {e}")
                df2_filtered = df2.copy()
        else:
            df2_filtered = df2.copy()

        # So khớp dữ liệu File 1 và File 2 theo tên hoạt chất ~ tên sản phẩm
        col_ten_san_pham = df2.columns[0]
        df_result = df1[df1[col_ten_hoat_chat].astype(str).str.lower().isin(
            df2_filtered[col_ten_san_pham].astype(str).str.lower())].copy()

        df_result["Số lượng"] = df_result[col_soluong].apply(format_number)
        df_result["Giá kế hoạch"] = df_result[col_gia_ke_hoach].apply(format_number)
        df_result["Trị giá thầu"] = df_result["Trị giá thầu"].apply(format_number)

        st.subheader("🔍 Lọc Danh mục có thể tham gia")
        st.success(f"✅ Lọc được {len(df_result)} dòng phù hợp tại BV đã chọn")

        st.dataframe(df_result.reset_index(drop=True), use_container_width=True)
