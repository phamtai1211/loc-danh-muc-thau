# Phần mềm lọc danh mục thầu thuốc bệnh viện - Phiên bản thông minh hơn + Rút gọn File 3

import streamlit as st
import pandas as pd
import os
import pickle

st.set_page_config(layout="wide")
st.title("🔍 Phần mềm lọc và phân tích thầu thuốc bệnh viện")

# ------------------ HÀM TIỆN ÍCH ------------------
def smart_read_excel(file, sheet_name_hint="Chi tiết triển khai", max_header_row=10):
    xls = pd.ExcelFile(file)
    sheet_name = next((s for s in xls.sheet_names if sheet_name_hint.lower() in s.lower()), xls.sheet_names[0])
    for i in range(max_header_row):
        try:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=i)
            df.columns = [str(c).strip().replace("\n", " ").replace("\r", "") for c in df.columns]
            if any("miền" in str(c).lower() for c in df.columns):
                return df
        except:
            continue
    return pd.read_excel(xls, sheet_name=sheet_name)

def standardize_column(df, mapping):
    rename_map = {}
    for col in df.columns:
        if not isinstance(col, str):
            continue
        clean_col = col.lower().strip().replace("\n", " ").replace("\r", "")
        for std, synonyms in mapping.items():
            if any(s.lower() in clean_col for s in synonyms):
                rename_map[col] = std
    return df.rename(columns=rename_map)

def rut_gon_file3(df):
    selected_columns = [
        "Miền", "Vùng", "Tỉnh", "Bệnh viện/SYT", "Địa bàn",
        "Tên sản phẩm", "Hoạt chất", "Hàm lượng/ Nồng độ", "Gói thầu", "Tên KH phụ trách triển khai"
    ]
    df_filtered = df[[col for col in selected_columns if col in df.columns]]
    return df_filtered

# ------------------ CẤU HÌNH ------------------
FOLDER_SP = "du_lieu_luu/sp_file.pkl"
FOLDER_DB = "du_lieu_luu/db_file.pkl"
os.makedirs("du_lieu_luu", exist_ok=True)

# ------------------ TẢI HOẶC LƯU FILE 2 & 3 ------------------
with st.sidebar:
    st.header("📁 Quản lý dữ liệu cố định")

    uploaded_sp = st.file_uploader("Tải lên File 2: Danh sách sản phẩm công ty", type="xlsx")
    uploaded_db = st.file_uploader("Tải lên File 3: Phân công địa bàn (sheet 'Chi tiết triển khai')", type="xlsx")

    if uploaded_sp:
        sp_data = smart_read_excel(uploaded_sp)
        pickle.dump(sp_data, open(FOLDER_SP, "wb"))
        st.success("✅ Đã lưu File 2 thành công")

    if uploaded_db:
        db_data = smart_read_excel(uploaded_db, sheet_name_hint="Chi tiết triển khai")
        pickle.dump(db_data, open(FOLDER_DB, "wb"))
        st.success("✅ Đã lưu File 3 thành công")

        # Tạo file rút gọn và cho phép tải
        st.markdown("### 📂 Tải File 3 rút gọn")
        df_tomtat = rut_gon_file3(db_data)
        st.download_button(
            "📥 Tải về file3_tomtat.xlsx",
            df_tomtat.to_excel(index=False, engine='openpyxl'),
            file_name="file3_tomtat.xlsx"
        )

# ------------------ CHỨC NĂNG 1: LỌC DANH MỤC ------------------
st.subheader("📄 Chức năng 1: Lọc danh mục mời thầu")
dm_file = st.file_uploader("Tải lên File 1: Danh mục mời thầu (DM)", type="xlsx")

if dm_file:
    df_dm = smart_read_excel(dm_file)

    try:
        df_sp = pickle.load(open(FOLDER_SP, "rb"))
        df_db = pickle.load(open(FOLDER_DB, "rb"))
    except:
        st.warning("Vui lòng tải trước File 2 và File 3 ở thanh bên")
        st.stop()

    col_mapping_db = {
        'Miền': ['miền', 'mien'],
        'Vùng': ['vùng', 'vung'],
        'Tỉnh': ['tỉnh', 'tinh'],
        'Tên sản phẩm': ['tên sản phẩm', 'tên thuốc', 'thuốc'],
        'Địa bàn': ['địa bàn', 'khu vực'],
        'Tên KH phụ trách': ['tên khách hàng', 'người phụ trách', 'khách hàng phụ trách'],
        'Bệnh viện/SYT': ['bệnh viện', 'syt', 'đơn vị']
    }
    df_db = standardize_column(df_db, col_mapping_db)
    st.write("### 🧪 Các cột hiện tại trong File 3 (sau khi chuẩn hóa):", list(df_db.columns))
    if 'Miền' not in df_db.columns:
        st.error("❌ Không tìm thấy cột 'Miền' sau khi chuẩn hóa. Hãy kiểm tra lại tên cột trong File 3.")
        st.stop()

    df_db = df_db[df_db.iloc[:, 3].isna()]

    st.markdown("### 🔍 Chọn địa bàn để lọc")
    col1, col2, col3 = st.columns(3)
    mien_list = sorted(df_db['Miền'].dropna().unique())
    mien = col1.selectbox("Chọn Miền", mien_list)

    vung_list = sorted(df_db[df_db['Miền'] == mien]['Vùng'].dropna().unique())
    vung = col2.selectbox("Chọn Vùng", vung_list)

    tinh_list = sorted(df_db[df_db['Vùng'] == vung]['Tỉnh'].dropna().unique())
    tinh = col3.selectbox("Chọn Tỉnh", tinh_list)

    df_loc = df_db[(df_db['Miền'] == mien) & (df_db['Vùng'] == vung) & (df_db['Tỉnh'] == tinh)]
    ten_sp_loc = df_loc['Tên sản phẩm'].dropna().str.lower().unique().tolist()

    ten_cols = [c for c in df_dm.columns if isinstance(c, str) and any(x in c.lower() for x in ['tên', 'thuốc'])]
    if ten_cols:
        col_ten = ten_cols[0]
        df_filtered = df_dm[df_dm[col_ten].str.lower().fillna('').apply(lambda x: any(sp in x for sp in ten_sp_loc))]
        df_filtered = df_filtered.copy()
        df_filtered['Miền'] = mien
        df_filtered['Vùng'] = vung
        df_filtered['Tỉnh'] = tinh

        st.success(f"Đã lọc được {len(df_filtered)} dòng phù hợp")
        st.dataframe(df_filtered)

        @st.cache_data
        def convert_df(df):
            return df.to_excel(index=False)

        st.download_button("📥 Tải kết quả Excel", data=convert_df(df_filtered), file_name="ket_qua_loc_thau.xlsx")
    else:
        st.error("Không tìm thấy cột tên thuốc phù hợp trong File 1")
