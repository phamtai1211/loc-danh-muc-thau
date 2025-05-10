# loc_thau_thuoc_app.py

import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import re

st.set_page_config(page_title="Lọc danh mục thầu thuốc bệnh viện", layout="wide")
st.title("Lọc danh mục thầu thuốc bệnh viện")

# ---------- Utilities ----------
def normalize_colname(name):
    name = name.lower().strip()
    name = re.sub(r"[\s\-_/]+", " ", name)
    return name

def fuzzy_find_column(columns, keywords):
    columns_norm = {col: normalize_colname(col) for col in columns}
    for key in keywords:
        for col, norm in columns_norm.items():
            if key in norm:
                return col
    return None

# ---------- File Uploads ----------
st.sidebar.header("1. Tải các file dữ liệu")
file2 = st.sidebar.file_uploader("Tải file 2 - Dữ liệu thuốc công ty", type="xlsx", key="f2")
file3 = st.sidebar.file_uploader("Tải file 3 - File phân khai triển khai", type="xlsx", key="f3")
file1 = st.sidebar.file_uploader("Tải file 1 - Danh mục thầu từ BV/SYT", type="xlsx", key="f1")

# ---------- Read Files ----------
data2, data3, data1_main = None, None, None
if file2:
    data2 = pd.read_excel(file2)
if file3:
    data3 = pd.read_excel(file3, sheet_name="Chi tiết triển khai")

# UI lựa chọn bệnh viện từ file 3
if data3 is not None:
    mien_list = sorted(data3["Miền"].dropna().unique())
    mien = st.selectbox("Chọn Miền", mien_list)
    vung_list = sorted(data3[data3["Miền"] == mien]["Vùng"].dropna().unique())
    vung = st.selectbox("Chọn Vùng", vung_list)
    tinh_list = sorted(data3[data3["Vùng"] == vung]["Tỉnh"].dropna().unique())
    tinh = st.selectbox("Chọn Tỉnh", tinh_list)
    bv_list = sorted(data3[data3["Tỉnh"] == tinh]["Bệnh viện/SYT"].dropna().unique())
    bv = st.selectbox("Chọn Bệnh viện/SYT", bv_list)

# ---------- Xử lý File 1 ----------
if file1:
    sheet_all = pd.read_excel(file1, sheet_name=None)
    selected_sheet = max(sheet_all.items(), key=lambda x: x[1].shape[1])[0]
    data1 = sheet_all[selected_sheet].copy()

    # Tìm cột phù hợp theo key
    col_hoatchat = fuzzy_find_column(data1.columns, ["hoat chat", "ten thanh phan"])
    col_hamluong = fuzzy_find_column(data1.columns, ["ham luong", "nong do"])
    col_nhom = fuzzy_find_column(data1.columns, ["nhom", "nhom thuoc"])

    if col_hoatchat and col_hamluong and col_nhom and data2 is not None:
        df1 = data1.rename(columns={
            col_hoatchat: "Tên hoạt chất",
            col_hamluong: "Hàm lượng",
            col_nhom: "Nhóm"
        })
        df2 = data2.rename(columns=lambda x: x.strip())

        # Chuẩn hóa nhóm chỉ lấy số cuối
        def clean_nhom(val):
            if pd.isna(val): return ""
            digits = re.findall(r"\d", str(val))
            return digits[-1] if digits else ""

        df1["Nhóm"] = df1["Nhóm"].apply(clean_nhom)
        df2["Nhóm"] = df2["Nhóm"].apply(clean_nhom)

        # So sánh 3 cột
        merge_df = df1.merge(
            df2,
            left_on=["Tên hoạt chất", "Hàm lượng", "Nhóm"],
            right_on=["Tên hoạt chất", "Nồng độ/hàm lượng", "Nhóm"],
            how="left"
        )

        # Nếu có file3 và chọn bệnh viện → thêm dữ liệu triển khai
        if data3 is not None:
            subset3 = data3[(data3["Miền"] == mien) & (data3["Vùng"] == vung) &
                            (data3["Tỉnh"] == tinh) & (data3["Bệnh viện/SYT"] == bv)]
            merge_df = merge_df.merge(
                subset3[["Tên sản phẩm", "Địa bàn", "Tên Khách hàng phụ trách triển khai"]],
                on="Tên sản phẩm",
                how="left"
            )

        # Hiển thị bảng rút gọn (chỉ các dòng có Tên sản phẩm)
        df_show = merge_df[~merge_df["Tên sản phẩm"].isna()]
        st.subheader(f"Số dòng có thể tham gia thầu: {len(df_show)}")
        st.dataframe(df_show)

        # Tải kết quả đầy đủ
        def convert_df(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            return output.getvalue()

        result_xlsx = convert_df(merge_df)
        st.download_button(
            label="📥 Tải kết quả đầy đủ (Excel)",
            data=result_xlsx,
            file_name="ket_qua_loc_thau.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("Không tìm được đủ 3 cột cần thiết trong file danh mục thầu hoặc thiếu file công ty.")
