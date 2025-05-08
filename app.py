# ✅ Full mã Python đã cập nhật toàn bộ xử lý file 3, lọc theo Miền, Vùng, Tỉnh, SYT/BV
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("📋 Hệ Thống Lọc & Phân Tích Danh Mục Thầu Bệnh Viện")

# --- Tải lên các file ---
st.markdown("### 📁 File 1: Danh mục chính (mời thầu)")
file1 = st.file_uploader("Tải lên File 1", type=["xls", "xlsx"])

st.markdown("### 📁 File 2: Danh mục sản phẩm của công ty")
file2 = st.file_uploader("Tải lên File 2", type=["xls", "xlsx"])

st.markdown("### 📁 File 3: Địa bàn & Khách hàng phụ trách")
file3 = st.file_uploader("Tải lên File 3", type=["xls", "xlsx"])

# --- Xử lý dữ liệu file 3 nếu có ---
df3_filtered_unique = pd.DataFrame()
if file3:
    try:
        df3 = pd.read_excel(file3, sheet_name="Chi tiết triển khai", header=0)
        df3 = df3[df3.iloc[:, 3].isna()]  # Bỏ dòng có dữ liệu cột D
        df3.columns = df3.columns.str.strip()

        mien_list = df3["Miền"].dropna().unique().tolist()
        vung_list = df3["Vùng"].dropna().unique().tolist()
        tinh_list = df3["Tỉnh"].dropna().unique().tolist()
        sytbv_list = df3["Bệnh viện/SYT"].dropna().unique().tolist()

        selected_mien = st.selectbox("Chọn Miền", mien_list)
        selected_vung = st.selectbox("Chọn Vùng", vung_list)
        selected_tinh = st.selectbox("Chọn Tỉnh", tinh_list)
        selected_sytbv = st.selectbox("Chọn SYT/BV", sytbv_list)

        df3_filtered = df3[
            (df3["Miền"] == selected_mien) &
            (df3["Vùng"] == selected_vung) &
            (df3["Tỉnh"] == selected_tinh) &
            (df3["Bệnh viện/SYT"] == selected_sytbv)
        ]

        df3_filtered_unique = df3_filtered[["Tên sản phẩm", "Địa bàn", "Tên Khách hàng phụ trách triển khai"]].drop_duplicates()
    except Exception as e:
        st.error(f"Lỗi xử lý file 3: {e}")

# --- Xử lý file 1 & 2 nếu có ---
if file1 and file2:
    try:
        df1 = pd.read_excel(file1)
        df2 = pd.read_excel(file2)

        df1.columns = df1.columns.str.strip()
        df2.columns = df2.columns.str.strip()

        df1["Nhóm thuốc"] = df1["Nhóm thuốc"].astype(str).apply(lambda x: f"Nhóm {str(x).strip()[-1]}" if pd.notna(x) else x)
        df2["Nhóm thuốc"] = df2["Nhóm thuốc"].astype(str).apply(lambda x: f"Nhóm {str(x).strip()[-1]}" if pd.notna(x) else x)

        df1["Trị giá thầu"] = df1['Số lượng'] * df1.get('Giá dự thầu', df1.get('Giá kế hoạch', 0))
        df1["Trị giá thầu"] = df1["Trị giá thầu"].fillna(0)

        df_result = df1[df1['Tên hoạt chất'].isin(df2['Tên hoạt chất'])]

        if not df3_filtered_unique.empty:
            df_result = df_result.merge(
                df3_filtered_unique,
                how="left",
                left_on="Tên hoạt chất",
                right_on="Tên sản phẩm"
            )

        df_result["Số lượng"] = df_result["Số lượng"].apply(lambda x: f"{x:,.0f}")
        df_result["Trị giá thầu"] = df_result["Trị giá thầu"].apply(lambda x: f"{x:,.0f}")

        st.success(f"✅ Lọc được {len(df_result)} dòng phù hợp tại {selected_sytbv}")
        st.dataframe(df_result, use_container_width=True)
    except Exception as e:
        st.error(f"Lỗi xử lý file 1 & 2: {e}")
