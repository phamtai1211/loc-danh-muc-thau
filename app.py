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


# ==== Giao diện chính ====
st.title("💊 Hệ Thống Lọc & Phân Tích Danh Mục Thầu")
menu = st.sidebar.radio("Chọn chức năng", ["Lọc danh mục thầu", "Phân tích danh mục mời thầu", "Phân tích danh mục trúng thầu", "Dự đoán thầu kỳ tới"])

if menu == "Lọc danh mục thầu":
    file1 = st.file_uploader("📥 File 1: Danh mục thầu của BV", type=['xlsx'], key="file1")
    file2 = st.file_uploader("📥 File 2: Danh sách sản phẩm công ty", type=['xlsx'], key="file2")
    file3 = st.file_uploader("📥 File 3 (tuỳ chọn): Phân công địa bàn", type=['xlsx'], key="file3")

    if file2:
        df2 = read_excel_auto_header(file2)
        df2 = standardize_column_names(df2)
        save_file(df2, "file2.pkl")
    else:
        df2 = load_file("file2.pkl")

    if file3:
        df3 = pd.read_excel(file3, sheet_name='Chi tiết triển khai')
        df3 = df3[df3.iloc[:, 3].isna()]
        df3 = df3.rename(columns={
            df3.columns[0]: 'Miền', df3.columns[1]: 'Vùng', df3.columns[2]: 'Tỉnh',
            df3.columns[4]: 'Bệnh viện/SYT', df3.columns[5]: 'Địa bàn',
            df3.columns[10]: 'Tên sản phẩm', df3.columns[38]: 'Tên Khách hàng phụ trách triển khai'
        })
        save_file(df3, "file3.pkl")
    else:
        df3 = load_file("file3.pkl")

    if file1 and df2 is not None:
        df1 = read_excel_auto_header(file1)
        df1 = standardize_column_names(df1)
        df_merge = df1.merge(df2, how='left', on=['Tên hoạt chất', 'Nồng độ/Hàm lượng', 'Nhóm thuốc'])
        if df3 is not None:
            df_merge = df_merge.merge(df3[['Tên sản phẩm', 'Bệnh viện/SYT', 'Địa bàn', 'Tên Khách hàng phụ trách triển khai']], 
                                      on='Tên sản phẩm', how='left')
        st.dataframe(df_merge)
        st.download_button("📥 Tải kết quả", df_merge.to_excel(index=False), file_name="ket_qua_loc.xlsx")

elif menu.startswith("Phân tích"):
    file = st.file_uploader("📥 File danh mục mời/trúng thầu", type=['xlsx'])
    if file:
        df = read_excel_auto_header(file)
        df = standardize_column_names(df)
        df['Nhóm thuốc'] = df['Nhóm thuốc'].apply(format_nhom_thuoc)
        df['Trị giá thầu'] = df['Số lượng'] * df.get('Giá dự thầu', df.get('Giá kế hoạch', 0))
        df['Nhóm điều trị'] = df['Tên hoạt chất'].apply(classify_group)

        if 'Bệnh viện/SYT' not in df.columns and load_file("file3.pkl") is not None:
            df3 = load_file("file3.pkl")
            df = df.merge(df3[['Tên sản phẩm', 'Miền', 'Vùng', 'Tỉnh', 'Bệnh viện/SYT']], on='Tên sản phẩm', how='left')

        st.subheader("🔍 Hàm lượng chính")
        hl = df.groupby(['Tên hoạt chất', 'Nồng độ/Hàm lượng'])['Số lượng'].sum().reset_index()
        hl = hl.sort_values(['Tên hoạt chất', 'Số lượng'], ascending=[True, False])
        st.dataframe(hl.groupby('Tên hoạt chất').first().reset_index())

        st.subheader("📚 Nhóm điều trị chi tiêu cao")
        st.dataframe(df.groupby('Nhóm điều trị')['Trị giá thầu'].sum().sort_values(ascending=False).reset_index())

        st.subheader("📈 Tỉ trọng nhóm thuốc")
        tong = df.groupby('Tên hoạt chất')['Số lượng'].sum().reset_index(name='Tong')
        df_ti = df.merge(tong, on='Tên hoạt chất')
        df_ti['Tỉ trọng (%)'] = df_ti['Số lượng'] / df_ti['Tong'] * 100
        st.dataframe(df_ti[['Tên hoạt chất', 'Nhóm thuốc', 'Số lượng', 'Tỉ trọng (%)']])

        st.subheader("💰 Ước lượng doanh thu")
        df['Ước lượng doanh thu'] = df['Trị giá thầu']
        st.dataframe(df.groupby('Tên hoạt chất')['Ước lượng doanh thu'].sum().sort_values(ascending=False).reset_index())

        st.subheader("📊 Biểu đồ trị giá theo nhóm điều trị")
        fig, ax = plt.subplots()
        df.groupby('Nhóm điều trị')['Trị giá thầu'].sum().plot(kind='bar', ax=ax)
        st.pyplot(fig)

        save_file(df, "phan_tich_toan_bo.pkl")
        st.success("✅ Đã lưu phân tích toàn bộ để phục vụ dự đoán")

elif menu == "Dự đoán thầu kỳ tới":
    df_old = load_file("file2.pkl")
    df_all = load_file("phan_tich_toan_bo.pkl")
    if df_old is not None and df_all is not None:
        df_all = standardize_column_names(df_all)
        col1, col2, col3, col4 = st.columns(4)
        mien = col1.selectbox("Miền", sorted(df_all['Miền'].dropna().unique()))
        vung = col2.selectbox("Vùng", sorted(df_all[df_all['Miền'] == mien]['Vùng'].dropna().unique()))
        tinh = col3.selectbox("Tỉnh", sorted(df_all[df_all['Vùng'] == vung]['Tỉnh'].dropna().unique()))
        bv = col4.selectbox("BV/SYT", sorted(df_all[df_all['Tỉnh'] == tinh]['Bệnh viện/SYT'].dropna().unique()))

        df_loc = df_all[df_all['Bệnh viện/SYT'] == bv]
        df_merge = df_loc.merge(df_old, on=['Tên hoạt chất', 'Nồng độ/Hàm lượng', 'Nhóm thuốc'], how='inner')
        df_suggest = df_merge.groupby(['Tên hoạt chất', 'Nồng độ/Hàm lượng', 'Nhóm thuốc'])['Số lượng'].mean().reset_index()
        df_suggest = df_suggest.rename(columns={'Số lượng': 'Số lượng nên chuẩn bị'})
        st.subheader(f"📦 Gợi ý chuẩn bị thầu tại {bv}")
        st.dataframe(df_suggest.sort_values(by='Số lượng nên chuẩn bị', ascending=False))
    else:
        st.warning("⚠️ Chưa có đủ dữ liệu để dự đoán. Hãy chạy phân tích và tải lên sản phẩm công ty trước.")
