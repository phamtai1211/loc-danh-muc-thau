# Phần mềm lọc danh mục thầu thuốc bệnh viện - Phiên bản đầy đủ

import streamlit as st
import pandas as pd
import os
import pickle

st.set_page_config(layout="wide")
st.title("🔍 Phần mềm lọc và phân tích thầu thuốc bệnh viện")

# ------------------ CẤU HÌNH ------------------
# Thư mục lưu file cố định
FOLDER_SP = "du_lieu_luu/sp_file.pkl"
FOLDER_DB = "du_lieu_luu/db_file.pkl"
os.makedirs("du_lieu_luu", exist_ok=True)

# ------------------ TẢI HOẶC LƯU FILE 2 & 3 ------------------
with st.sidebar:
    st.header("📁 Quản lý dữ liệu cố định")

    uploaded_sp = st.file_uploader("Tải lên File 2: Danh sách sản phẩm công ty", type="xlsx")
    uploaded_db = st.file_uploader("Tải lên File 3: Phân công địa bàn (sheet 'Chi tiết triển khai')", type="xlsx")

    if uploaded_sp:
        sp_data = pd.read_excel(uploaded_sp)
        pickle.dump(sp_data, open(FOLDER_SP, "wb"))
        st.success("Đã lưu File 2 thành công")

    if uploaded_db:
        db_data = pd.read_excel(uploaded_db, sheet_name="Chi tiết triển khai")
        pickle.dump(db_data, open(FOLDER_DB, "wb"))
        st.success("Đã lưu File 3 thành công")

# ------------------ CHỨC NĂNG 1: LỌC DANH MỤC ------------------
st.subheader("📄 Chức năng 1: Lọc danh mục mời thầu")
dm_file = st.file_uploader("Tải lên File 1: Danh mục mời thầu (DM)", type="xlsx")

if dm_file:
    df_dm = pd.read_excel(dm_file)

    # Tải dữ liệu đã lưu sẵn
    try:
        df_sp = pickle.load(open(FOLDER_SP, "rb"))
        df_db = pickle.load(open(FOLDER_DB, "rb"))
    except:
        st.warning("Vui lòng tải trước File 2 và File 3 ở thanh bên")
        st.stop()

    # Lọc địa bàn
    st.markdown("### 🔍 Chọn địa bàn để lọc")
    col1, col2, col3 = st.columns(3)
    mien_list = sorted(df_db['Miền'].dropna().unique())
    mien = col1.selectbox("Chọn Miền", mien_list)

    vung_list = sorted(df_db[df_db['Miền'] == mien]['Vùng'].dropna().unique())
    vung = col2.selectbox("Chọn Vùng", vung_list)

    tinh_list = sorted(df_db[df_db['Vùng'] == vung]['Tỉnh'].dropna().unique())
    tinh = col3.selectbox("Chọn Tỉnh", tinh_list)

    df_loc = df_db[(df_db['Miền'] == mien) & (df_db['Vùng'] == vung) & (df_db['Tỉnh'] == tinh)]
    df_loc = df_loc[df_loc['Unnamed: 3'].isna()]  # Loại bỏ dòng có dữ liệu cột D

    st.markdown("#### ✅ Đã chọn địa bàn: {} – {} – {}".format(mien, vung, tinh))

    # Lấy danh sách sản phẩm cần lọc từ cột 'Tên sản phẩm' (K)
    ten_sp_loc = df_loc['Tên sản phẩm'].dropna().str.lower().unique().tolist()

    # Lọc trong file DM nếu có cột tên thuốc
    col_map = [c for c in df_dm.columns if 'tên' in c.lower() or 'thuốc' in c.lower()]
    if col_map:
        col_ten = col_map[0]
        df_filtered = df_dm[df_dm[col_ten].str.lower().fillna('').apply(lambda x: any(sp in x for sp in ten_sp_loc))]
        df_filtered = df_filtered.copy()
        df_filtered['Miền'] = mien
        df_filtered['Vùng'] = vung
        df_filtered['Tỉnh'] = tinh

        # TODO: Phân tích tỉ trọng theo hoạt chất và nhóm
        # Hiện tại sẽ chỉ hiển thị dữ liệu lọc

        st.success(f"Đã lọc được {len(df_filtered)} dòng phù hợp")
        st.dataframe(df_filtered)

        # Xuất file
        @st.cache_data
        def convert_df(df):
            return df.to_excel(index=False)

        st.download_button("📥 Tải kết quả Excel", data=convert_df(df_filtered), file_name="ket_qua_loc_thau.xlsx")
    else:
        st.error("Không tìm thấy cột tên thuốc trong File 1")

# ------------------ CHỨC NĂNG 2, 3, 4: Placeholder ------------------
st.subheader("📊 Chức năng 2: Phân tích danh mục")
st.info("Sẽ bao gồm: nhóm thuốc theo đường dùng, nhóm điều trị, top hoạt chất")

st.subheader("📈 Chức năng 3: Phân tích kết quả thầu")
st.info("Sẽ bao gồm: top nhà thầu trúng nhiều nhất, nhóm dùng nhiều nhất")

st.subheader("🔮 Chức năng 4: Dự đoán kỳ thầu tiếp theo")
st.info("Sẽ gợi ý hoạt chất nên làm dựa theo file SP và kết quả phân tích")

# ------------------ GHI CHÚ ------------------
st.caption("Tất cả dữ liệu giữ nguyên định dạng gốc. Phần mềm sẽ bổ sung thông tin phù hợp vào dòng trùng khớp.")
