import streamlit as st
import pandas as pd
import os
from io import BytesIO

st.set_page_config(layout="wide")
st.title("🧪 Hệ Thống Lọc & Phân Tích Danh Mục Thầu Bệnh Viện")

# ======= FUNCTION ==========
def format_number(n):
    try:
        return f"{int(n):,}"
    except:
        return n

def load_excel_file(uploaded_file):
    if uploaded_file is not None:
        try:
            return pd.read_excel(uploaded_file)
        except:
            st.error("❌ File không hợp lệ hoặc bị lỗi!")
            return None
    return None

def standardize_column_name(col):
    if pd.isna(col):
        return col
    col = str(col).strip().lower()
    if 'hoạt chất' in col:
        return 'Tên hoạt chất'
    elif 'hàm lượng' in col:
        return 'Nồng độ/Hàm lượng'
    elif 'đường dùng' in col:
        return 'Đường dùng'
    elif 'nhóm' in col:
        return 'Nhóm thuốc'
    elif 'số lượng' in col:
        return 'Số lượng'
    elif 'giá kế hoạch' in col.lower():
        return 'Giá kế hoạch'
    elif 'giá dự thầu' in col.lower():
        return 'Giá dự thầu'
    elif 'tên sản phẩm' in col:
        return 'Tên sản phẩm'
    return col

# ========== UPLOAD FILES ==========
col1, col2, col3 = st.columns(3)

with col1:
    file1 = st.file_uploader("📁 File 1: Danh mục chính mời thầu (DM)", type=['xlsx'], key="file1")
    df1 = load_excel_file(file1)
    if df1 is not None:
        df1.columns = [standardize_column_name(c) for c in df1.columns]

with col2:
    file2 = st.file_uploader("📁 File 2: Danh mục sản phẩm công ty", type=['xlsx'], key="file2")
    df2 = load_excel_file(file2)
    if df2 is not None:
        df2.columns = [standardize_column_name(c) for c in df2.columns]

with col3:
    file3 = st.file_uploader("📁 File 3: Địa bàn & Khách hàng phụ trách", type=['xlsx'], key="file3")
    df3 = load_excel_file(file3)
    if df3 is not None:
        try:
            df3 = pd.read_excel(file3, sheet_name="Chi tiết triển khai", header=0)
        except:
            df3 = None

# ========== LỌC DANH MỤC ==========
st.subheader("🔍 Lọc Danh mục có thể tham gia")

if df1 is not None and df2 is not None:
    # Nếu có file 3 => lọc theo địa bàn
    if df3 is not None:
        df3.columns = [str(c).strip() for c in df3.columns]

        mien = st.selectbox("Chọn Miền", sorted(df3['Miền'].dropna().unique()))
        vung = st.selectbox("Chọn Vùng", sorted(df3[df3['Miền']==mien]['Vùng'].dropna().unique()))
        tinh = st.selectbox("Chọn Tỉnh", sorted(df3[df3['Vùng']==vung]['Tỉnh'].dropna().unique()))
        choices_bv = df3[df3['Tỉnh'] == tinh]['Bệnh viện/SYT'].dropna().unique()
        tenbv = st.selectbox("Chọn SYT/BV", sorted(choices_bv))

        df3_bv = df3[df3['Bệnh viện/SYT'] == tenbv]
        san_pham_cua_bv = df3_bv['Tên sản phẩm'].dropna().unique()
        df2_filtered = df2[df2['Tên sản phẩm'].isin(san_pham_cua_bv)]
    else:
        df2_filtered = df2.copy()

    if not df2_filtered.empty:
        if 'Tên sản phẩm' in df1.columns and 'Tên sản phẩm' in df2_filtered.columns:
            df_result = df1.merge(df2_filtered[['Tên sản phẩm']], on="Tên sản phẩm", how="inner")
        elif 'Tên hoạt chất' in df1.columns and 'Tên hoạt chất' in df2_filtered.columns:
            df_result = df1.merge(df2_filtered[['Tên hoạt chất']], on="Tên hoạt chất", how="inner")
        else:
            st.error("⚠️ Không tìm thấy cột 'Tên sản phẩm' hoặc 'Tên hoạt chất' để đối chiếu!")
            df_result = pd.DataFrame()

        if not df_result.empty:
            if 'Giá dự thầu' in df_result.columns:
                df_result['Trị giá thầu'] = df_result['Số lượng'] * df_result.get('Giá dự thầu', 0)
            else:
                df_result['Trị giá thầu'] = df_result['Số lượng'] * df_result.get('Giá kế hoạch', 0)

            st.success(f"✅ Lọc được {len(df_result):,} dòng phù hợp tại BV đã chọn")
            st.dataframe(df_result.head(30).style.format(format_number))
        else:
            st.warning("⚠️ Không tìm thấy dữ liệu phù hợp để lọc!")
    else:
        st.warning("⚠️ File 2 không có dữ liệu phù hợp")
