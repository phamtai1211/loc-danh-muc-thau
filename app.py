import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("🧪 Hệ Thống Lọc & Phân Tích Danh Mục Thầu Bệnh Viện")

# ========== FUNCTION ==========
def standardize_column_names(df):
    col_map = {}
    for col in df.columns:
        lower_col = col.lower()
        if "hoạt chất" in lower_col:
            col_map[col] = "Tên hoạt chất"
        elif "hàm lượng" in lower_col or "nồng độ" in lower_col:
            col_map[col] = "Nồng độ/Hàm lượng"
        elif "đường dùng" in lower_col:
            col_map[col] = "Đường dùng"
        elif "dạng bào chế" in lower_col:
            col_map[col] = "Dạng bào chế"
        elif "đơn vị" in lower_col and "tính" in lower_col:
            col_map[col] = "Đơn vị tính"
        elif "số lượng" in lower_col:
            col_map[col] = "Số lượng"
        elif "giá kế hoạch" in lower_col:
            col_map[col] = "Giá kế hoạch"
        elif "giá dự thầu" in lower_col:
            col_map[col] = "Giá dự thầu"
        elif "tên sản phẩm" in lower_col:
            col_map[col] = "Tên sản phẩm"
        elif "nhóm" in lower_col and "thuốc" in lower_col:
            col_map[col] = "Nhóm thuốc"
        elif "tên miền" in lower_col:
            col_map[col] = "Miền"
        elif "tên vùng" in lower_col:
            col_map[col] = "Vùng"
        elif "tỉnh" in lower_col:
            col_map[col] = "Tỉnh"
        elif "bệnh viện" in lower_col or "sở y tế" in lower_col:
            col_map[col] = "BV/SYT"
        elif "tên sản phẩm" in lower_col:
            col_map[col] = "Tên sản phẩm"
        elif "tên khách hàng" in lower_col:
            col_map[col] = "Tên khách hàng phụ trách"
        elif "địa bàn" in lower_col:
            col_map[col] = "Địa bàn"
    df.rename(columns=col_map, inplace=True)
    return df

# ========== FILE INPUT ==========
st.markdown("#### 📁 File 1: Danh mục chính mời thầu (DM)")
file1 = st.file_uploader("Tải lên file Danh mục mời thầu của BV", type=["xlsx"], key="file1")

st.markdown("#### 📁 File 2: Danh mục sản phẩm công ty")
file2 = st.file_uploader("Tải lên file Danh mục sản phẩm nội bộ công ty", type=["xlsx"], key="file2")

st.markdown("#### 📁 File 3: Địa bàn & Khách hàng phụ trách")
file3 = st.file_uploader("Tải lên file Thông tin triển khai (Địa bàn, khách hàng phụ trách)", type=["xlsx"], key="file3")

# ========== LOAD & CLEAN ==========
if file1 and file2:
    df1 = pd.read_excel(file1)
    df2 = pd.read_excel(file2)
    df1 = standardize_column_names(df1)
    df2 = standardize_column_names(df2)

    # Nếu có file 3
    if file3:
        df3 = pd.read_excel(file3, sheet_name="Chi tiết triển khai", header=0)
        df3 = standardize_column_names(df3)
        df3 = df3[df3["BV/SYT"].notna() & ~df3["BV/SYT"].astype(str).str.strip().eq("")]

        mien_list = df3["Miền"].dropna().unique().tolist()
        mien = st.selectbox("Chọn Miền", mien_list)

        vung_list = df3[df3["Miền"] == mien]["Vùng"].dropna().unique().tolist()
        vung = st.selectbox("Chọn Vùng", vung_list)

        tinh_list = df3[(df3["Miền"] == mien) & (df3["Vùng"] == vung)]["Tỉnh"].dropna().unique().tolist()
        tinh = st.selectbox("Chọn Tỉnh", tinh_list)

        bvsyt_list = df3[(df3["Miền"] == mien) & (df3["Vùng"] == vung) & (df3["Tỉnh"] == tinh)]["BV/SYT"].dropna().unique().tolist()
        bvsyt = st.selectbox("Chọn SYT/BV", bvsyt_list)

        sp_list = df3[df3["BV/SYT"] == bvsyt]["Tên sản phẩm"].dropna().unique().tolist()
        df_filtered = df2[df2["Tên sản phẩm"].isin(sp_list)]
    else:
        df_filtered = df2.copy()

    # ========== LỌC DỮ LIỆU ==========
    df_filtered["Tên hoạt chất"] = df_filtered["Tên hoạt chất"].str.strip().str.lower()
    df1["Tên hoạt chất"] = df1["Tên hoạt chất"].str.strip().str.lower()

    # Match chính xác hơn: theo hoạt chất, nồng độ, nhóm
    merge_cols = ["Tên hoạt chất"]
    for col in ["Nồng độ/Hàm lượng", "Nhóm thuốc"]:
        if col in df1.columns and col in df_filtered.columns:
            merge_cols.append(col)

    df_result = df1.merge(df_filtered[merge_cols], on=merge_cols, how="inner")

    # ========== TÍNH TRỊ GIÁ ==========
    price_col = "Giá dự thầu" if "Giá dự thầu" in df1.columns else "Giá kế hoạch"
    df_result["Trị giá thầu"] = df_result["Số lượng"] * df_result.get(price_col, 0)
    df_result["Trị giá thầu"] = df_result["Trị giá thầu"].fillna(0)

    # ========== HIỂN THỊ ==========
    st.markdown("### 🔍 Lọc Danh mục có thể tham gia")
    st.success(f"✅ Lọc được {len(df_result):,} dòng phù hợp tại BV đã chọn")
    st.dataframe(df_result, use_container_width=True)

else:
    st.warning("⚠️ Vui lòng tải lên File 1 (DM) và File 2 (sản phẩm công ty) để bắt đầu.")
