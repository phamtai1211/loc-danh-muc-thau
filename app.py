import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Lọc Danh Mục Thầu Thuốc BV", layout="wide")
st.title("📋 Hệ Thống Lọc Danh Mục Thầu Thuốc Bệnh Viện")

# Upload files
file1 = st.file_uploader("Bước 1️⃣: Tải lên file Danh mục thầu của Bệnh viện", type=["xls", "xlsx"], key="file1")
file2 = st.file_uploader("Bước 2️⃣: Tải lên file Danh mục sản phẩm nội bộ của công ty bạn", type=["xls", "xlsx"], key="file2")
file3 = st.file_uploader("Bước 3️⃣: Tải lên file Thông tin triển khai (Địa bàn, khách hàng phụ trách)", type=["xls", "xlsx"], key="file3")

if file1 and file2 and file3:
    try:
        df1 = pd.read_excel(file1)
        df2 = pd.read_excel(file2)
        df3 = pd.read_excel(file3)

        # Chuẩn hóa tên cột và xử lý dữ liệu
        keys = ['Tên hoạt chất', 'Nồng độ/Hàm lượng', 'Nhóm thuốc']
        for df in [df1, df2]:
            for col in keys:
                df[col] = df[col].astype(str).str.strip().str.lower()

        # Lọc thuốc có thể tham gia thầu
        merged_df = pd.merge(df1, df2[keys + ['Tên sản phẩm']], on=keys, how='inner')

        # Gộp thêm thông tin địa bàn và người phụ trách
        df3['Tên sản phẩm'] = df3['Tên sản phẩm'].astype(str).str.strip().str.lower()
        merged_df['Tên sản phẩm'] = merged_df['Tên sản phẩm'].astype(str).str.strip().str.lower()
        final_df = pd.merge(merged_df, df3, on='Tên sản phẩm', how='left')

        # Hiển thị và tải kết quả
        st.success(f"✅ Đã lọc được {len(final_df)} dòng phù hợp!")
        st.dataframe(final_df)

        # Xuất file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            final_df.to_excel(writer, index=False, sheet_name='Danh mục tham dự')
        output.seek(0)

        st.download_button(
            label="📥 Tải về kết quả Excel",
            data=output,
            file_name="danh_muc_tham_du_thau.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Lỗi trong quá trình xử lý: {e}")
else:
    st.info("⬆️ Vui lòng tải đủ cả 3 file để hệ thống bắt đầu xử lý.")
