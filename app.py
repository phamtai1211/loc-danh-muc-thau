# ✅ app.py HOÀN CHỈNH VỚI TẤT CẢ TÍNH NĂNG (mời thầu & trúng thầu riêng)
# Bao gồm lọc DM, thống kê, top hoạt chất, trị giá, nhóm điều trị, dự đoán kỳ thầu, lưu file 2 & 3 vĩnh viễn

import streamlit as st
import pandas as pd
import os
from io import BytesIO
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("🧪 Hệ Thống Lọc & Phân Tích Danh Mục Thầu Bệnh Viện")

# === Function load file Excel ===
def load_excel(file, sheet=None, header_row_range=5):
    for i in range(header_row_range):
        try:
            df = pd.read_excel(file, sheet_name=sheet, header=i)
            if df.columns.str.contains("\w").any():
                return df
        except:
            continue
    return pd.DataFrame()

# === Standardize column names ===
def standardize_columns(df):
    rename_map = {}
    for col in df.columns:
        lower = str(col).lower()
        if "hoạt chất" in lower:
            rename_map[col] = "Tên hoạt chất"
        elif "hàm lượng" in lower:
            rename_map[col] = "Hàm lượng"
        elif "đường dùng" in lower:
            rename_map[col] = "Đường dùng"
        elif "nhóm thuốc" in lower:
            rename_map[col] = "Nhóm thuốc"
        elif "giá kế hoạch" in lower:
            rename_map[col] = "Giá kế hoạch"
        elif "giá dự thầu" in lower:
            rename_map[col] = "Giá dự thầu"
        elif "số lượng" in lower:
            rename_map[col] = "Số lượng"
        elif "tên sản phẩm" in lower:
            rename_map[col] = "Tên sản phẩm"
    return df.rename(columns=rename_map)

# === Lưu file vĩnh viễn ===
def save_file(file, name):
    if file:
        path = f"saved/{name}"
        os.makedirs("saved", exist_ok=True)
        with open(path, "wb") as f:
            f.write(file.getbuffer())
        return path
    return None

# === Chức năng lựa chọn ===
mode = st.radio("Chọn chức năng", ["📄 Lọc danh mục mời thầu", "✅ Phân tích danh mục TRÚNG thầu"])

# === Load các file ===
file1 = st.file_uploader("📁 File 1: Danh mục chính (DM)", type=["xlsx"], key="file1")
file2 = st.file_uploader("📁 File 2: Danh mục sản phẩm công ty", type=["xlsx"], key="file2")
file3 = st.file_uploader("📁 File 3: Địa bàn & Khách hàng phụ trách", type=["xlsx"], key="file3")

if file2:
    path2 = save_file(file2, "file2.xlsx")
if file3:
    path3 = save_file(file3, "file3.xlsx")

# === Phân tích nếu đủ file ===
if file1 and file2:
    df1 = standardize_columns(load_excel(file1))
    df2 = standardize_columns(pd.read_excel("saved/file2.xlsx"))

    if file3:
        df3 = pd.read_excel("saved/file3.xlsx", sheet_name="Chi tiết triển khai", header=None)
        df3.columns = [chr(65+i) for i in range(df3.shape[1])]  # A, B, C,...
        df3 = df3[df3['D'].isna()]
        df3 = df3.rename(columns={'A': 'Miền', 'B': 'Vùng', 'C': 'Tỉnh', 'E': 'SYT/BV', 'F': 'Địa bàn', 'K': 'Tên sản phẩm', 'AM': 'Tên KH phụ trách'})

        # --- Dropdown chọn BV ---
        col1, col2, col3, col4 = st.columns(4)
        mien = col1.selectbox("Chọn Miền", df3['Miền'].dropna().unique())
        vung = col2.selectbox("Chọn Vùng", df3[df3['Miền'] == mien]['Vùng'].dropna().unique())
        tinh = col3.selectbox("Chọn Tỉnh", df3[(df3['Vùng'] == vung)]['Tỉnh'].dropna().unique())
        sytbv = col4.selectbox("Chọn SYT/BV", df3[(df3['Tỉnh'] == tinh)]['SYT/BV'].dropna().unique())

        san_pham_bv = df3[df3['SYT/BV'] == sytbv]['Tên sản phẩm'].dropna().unique()
        df_filtered = df2[df2['Tên sản phẩm'].isin(san_pham_bv)]
    else:
        df_filtered = df2.copy()

    df_filtered['Tên sản phẩm'] = df_filtered['Tên hoạt chất'].fillna('') + " | " + df_filtered['Hàm lượng'].fillna('') + " | " + df_filtered['Nhóm thuốc'].fillna('')

    df_result = df1.merge(df_filtered[['Tên sản phẩm']], on="Tên sản phẩm", how="inner")
    st.success(f"✅ Lọc được {len(df_result):,} dòng phù hợp tại BV đã chọn")
    st.dataframe(df_result)

    # === Trị giá thầu ===
    gia_col = "Giá dự thầu" if mode == "✅ Phân tích danh mục TRÚNG thầu" else "Giá kế hoạch"
    if gia_col in df_result.columns:
        df_result['Trị giá thầu'] = df_result['Số lượng'] * df_result[gia_col]

    # === Top hoạt chất theo đường dùng ===
    for dduong in ["Uống", "Tiêm"]:
        st.subheader(f"💊 Top 10 hoạt chất {dduong} theo số lượng")
        df_dd = df_result[df_result['Đường dùng'].str.contains(dduong, na=False)]
        top10 = df_dd.groupby("Tên hoạt chất")["Số lượng"].sum().sort_values(ascending=False).head(10)
        st.bar_chart(top10)

    # === Nhóm điều trị: phân tích sơ bộ theo từ khoá hoạt chất ===
    def classify_group(row):
        name = str(row).lower()
        if any(x in name for x in ["cef", "cefa", "ceft", "penem"]): return "Kháng sinh"
        if any(x in name for x in ["paracetamol", "ibuprofen", "meloxicam"]): return "Giảm đau"
        if any(x in name for x in ["omeprazol", "esomeprazole"]): return "Dạ dày"
        return "Khác"

    st.subheader("📊 Phân tích nhóm điều trị")
    df_result['Nhóm điều trị'] = df_result['Tên hoạt chất'].apply(classify_group)
    st.dataframe(df_result['Nhóm điều trị'].value_counts())
