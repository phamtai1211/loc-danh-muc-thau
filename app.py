import streamlit as st
import pandas as pd
import numpy as np

# Tiêu đề
st.markdown("""
# 🧪 Hệ Thống Lọc & Phân Tích Danh Mục Thầu Bệnh Viện
""")

# Tải lên các file cần thiết
st.subheader("📁 File 1: Danh mục chính mời thầu (DM)")
file1 = st.file_uploader("Tải lên file Danh mục mời thầu của BV", type=["xlsx", "xls"])

st.subheader("📁 File 2: Danh mục sản phẩm công ty")
file2 = st.file_uploader("Tải lên file Danh mục sản phẩm nội bộ công ty", type=["xlsx", "xls"])

st.subheader("📁 File 3: Địa bàn & Khách hàng phụ trách")
file3 = st.file_uploader("Tải lên file Thông tin triển khai (Địa bàn, khách hàng phụ trách)", type=["xlsx", "xls"])

if file1 and file2:
    df1 = pd.read_excel(file1, header=None)
    for i in range(5):
        if df1.iloc[i].astype(str).str.contains("Tên hoạt chất", case=False).any():
            df1.columns = df1.iloc[i]
            df1 = df1[i+1:]
            break
    df1 = df1.reset_index(drop=True)

    col_map = {}
    for col in df1.columns:
        col_str = str(col).lower()
        if 'tên hoạt' in col_str:
            col_map[col] = 'Tên hoạt chất'
        elif 'nồng độ' in col_str:
            col_map[col] = 'Nồng độ'
        elif 'nhóm' in col_str:
            col_map[col] = 'Nhóm thuốc'
        elif 'số lượng' in col_str:
            col_map[col] = 'Số lượng'
        elif 'giá kế hoạch' in col_str:
            col_map[col] = 'Giá kế hoạch'
        elif 'giá dự thầu' in col_str:
            col_map[col] = 'Giá dự thầu'
        elif 'đường dùng' in col_str:
            col_map[col] = 'Đường dùng'
    df1 = df1.rename(columns=col_map)

    df2 = pd.read_excel(file2)
    df2 = df2.rename(columns=lambda x: x.strip())
    col_map2 = {}
    for col in df2.columns:
        col_str = str(col).lower()
        if 'tên hoạt' in col_str:
            col_map2[col] = 'Tên hoạt chất'
        elif 'nồng độ' in col_str:
            col_map2[col] = 'Nồng độ'
        elif 'nhóm' in col_str:
            col_map2[col] = 'Nhóm thuốc'
        elif 'tên sản phẩm' in col_str:
            col_map2[col] = 'Tên sản phẩm'
    df2 = df2.rename(columns=col_map2)

    df_merge = pd.merge(df1, df2, on=['Tên hoạt chất', 'Nồng độ', 'Nhóm thuốc'], how='left')
    df_merge['Trị giá thầu'] = df_merge['Số lượng'] * df_merge.get('Giá dự thầu', df_merge.get('Giá kế hoạch', 0))

    df_result = df_merge.copy()

    if file3:
        df3 = pd.read_excel(file3, sheet_name='Chi tiết triển khai')
        df3 = df3[df3.iloc[:, 3].isna()]  # Loại bỏ dòng có dữ liệu ở cột D
        df3.columns.values[0] = 'Miền'
        df3.columns.values[1] = 'Vùng'
        df3.columns.values[2] = 'Tỉnh'
        df3.columns.values[4] = 'Bệnh viện/SYT'
        df3.columns.values[5] = 'Địa bàn'
        df3.columns.values[10] = 'Tên sản phẩm'
        df3.columns.values[38] = 'Tên Khách hàng phụ trách'

        mien_list = sorted(df3['Miền'].dropna().unique())
        mien_selected = st.selectbox("Chọn Miền", mien_list)

        vung_list = sorted(df3[df3['Miền'] == mien_selected]['Vùng'].dropna().unique())
        vung_selected = st.selectbox("Chọn Vùng", vung_list)

        tinh_list = sorted(df3[(df3['Miền'] == mien_selected) & (df3['Vùng'] == vung_selected)]['Tỉnh'].dropna().unique())
        tinh_selected = st.selectbox("Chọn Tỉnh", tinh_list)

        sytbv_list = sorted(df3[
            (df3['Miền'] == mien_selected) &
            (df3['Vùng'] == vung_selected) &
            (df3['Tỉnh'] == tinh_selected)
        ]['Bệnh viện/SYT'].dropna().unique())

        sytbv_selected = st.selectbox("Chọn SYT/BV", sytbv_list)

        df3_filtered = df3[
            (df3['Miền'] == mien_selected) &
            (df3['Vùng'] == vung_selected) &
            (df3['Tỉnh'] == tinh_selected) &
            (df3['Bệnh viện/SYT'] == sytbv_selected)
        ]

        df3_filtered_unique = df3_filtered[['Tên sản phẩm', 'Địa bàn', 'Tên Khách hàng phụ trách']].drop_duplicates(subset=['Tên sản phẩm'])
        df_result = df_result.merge(df3_filtered_unique, left_on='Tên hoạt chất', right_on='Tên sản phẩm', how='left')

    st.subheader("🔍 Lọc Danh mục có thể tham gia")
    st.success(f"✅ Lọc được {len(df_result)} dòng phù hợp tại {sytbv_selected if file3 else 'BV đã chọn'}")
    st.dataframe(df_result)

    import io
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_result.to_excel(writer, index=False, sheet_name='KQ')
        writer.save()
    st.download_button(label="📥 Tải kết quả Excel", data=output.getvalue(), file_name="Danh_muc_tham_gia.xlsx")
