import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Lọc & Phân tích Thầu BV", layout="wide")
st.title("📋 Hệ Thống Lọc & Phân Tích Danh Mục Thầu Bệnh Viện")

menu = st.sidebar.radio("Chọn chức năng", ["Lọc danh mục thầu", "Phân tích danh mục BV"])

if menu == "Lọc danh mục thầu":
    file1 = st.file_uploader("Tải lên file Danh mục thầu của Bệnh viện", type=["xls", "xlsx"], key="file1")
    file2 = st.file_uploader("Tải lên file Danh mục sản phẩm nội bộ", type=["xls", "xlsx"], key="file2")
    file3 = st.file_uploader("Tải lên file Thông tin triển khai", type=["xls", "xlsx"], key="file3")

    def standardize_columns(df):
        col_map = {}
        for col in df.columns:
            name = col.strip().lower()
            if 'tên hoạt chất' in name:
                col_map[col] = 'Tên hoạt chất'
            elif 'nồng độ' in name and 'hàm lượng' in name:
                col_map[col] = 'Nồng độ/Hàm lượng'
            elif 'nhóm' in name:
                col_map[col] = 'Nhóm thuốc'
        return df.rename(columns=col_map)

    if file1 and file2 and file3:
        try:
            df1 = pd.read_excel(file1)
            df2 = pd.read_excel(file2)
            df3 = pd.read_excel(file3)

            df1 = standardize_columns(df1)
            df2 = standardize_columns(df2)

            keys = ['Tên hoạt chất', 'Nồng độ/Hàm lượng', 'Nhóm thuốc']
            for df in [df1, df2]:
                for col in keys:
                    df[col] = df[col].astype(str).str.strip().str.lower()
            for df in [df1, df2]:
                df['Nhóm thuốc'] = df['Nhóm thuốc'].str.extract(r'(\d)$')[0]

            merged_df = pd.merge(df1, df2[keys + ['Tên sản phẩm']], on=keys, how='inner')
            df3['Tên sản phẩm'] = df3['Tên sản phẩm'].astype(str).str.strip().str.lower()
            merged_df['Tên sản phẩm'] = merged_df['Tên sản phẩm'].astype(str).str.strip().str.lower()
            final_df = pd.merge(merged_df, df3, on='Tên sản phẩm', how='left')

            # Tính tỉ trọng nhóm
            tong_theo_hoatchat_hamluong = (
                df1.groupby(['Tên hoạt chất', 'Nồng độ/Hàm lượng'])['Số lượng'].sum().reset_index()
                .rename(columns={'Số lượng': 'Tổng SL cùng hoạt chất-hàm lượng'})
            )
            final_df = pd.merge(final_df, tong_theo_hoatchat_hamluong, on=['Tên hoạt chất', 'Nồng độ/Hàm lượng'], how='left')
            final_df['Tỉ trọng nhóm (%)'] = round(final_df['Số lượng'] / final_df['Tổng SL cùng hoạt chất-hàm lượng'] * 100, 2)

            st.success(f"✅ Lọc được {len(final_df)} dòng phù hợp")
            st.dataframe(final_df)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                final_df.to_excel(writer, index=False, sheet_name='Kết quả lọc')
            output.seek(0)
            st.download_button("📥 Tải Excel kết quả lọc", data=output, file_name="danh_muc_tham_du.xlsx")

        except Exception as e:
            st.error(f"❌ Lỗi: {e}")
    else:
        st.info("⬆️ Tải đủ cả 3 file để lọc dữ liệu")

elif menu == "Phân tích danh mục BV":
    file_dm = st.file_uploader("Tải lên file Danh mục mời thầu của BV", type=["xls", "xlsx"], key="dmfile")

    if file_dm:
        try:
            df_dm = pd.read_excel(file_dm, sheet_name=0)
            df_dm['Nhóm thuốc chuẩn'] = df_dm['Nhóm thuốc'].astype(str).str.extract(r'(\d)$')[0]
            df_dm['Trị giá thầu'] = df_dm['Số lượng'] * df_dm['Giá kế hoạch']

            st.subheader("📊 Thống kê nhóm thuốc")
            nhom_summary = df_dm.groupby('Nhóm thuốc chuẩn').agg(SL=('Số lượng','sum'), Giá=('Trị giá thầu','sum'))
            st.dataframe(nhom_summary)

            st.subheader("💊 Thống kê dạng bào chế")
            dang_summary = df_dm.groupby('Dạng bào chế').agg(SL=('Số lượng','sum'), Giá=('Trị giá thầu','sum'))
            st.dataframe(dang_summary)

            st.subheader("🔥 Top 10 hoạt chất theo số lượng")
            top10 = df_dm.groupby('Tên hoạt chất').agg(SL=('Số lượng','sum')).sort_values(by='SL', ascending=False).head(10)
            st.dataframe(top10)

            st.subheader("📌 Phân nhóm điều trị")
            def classify_hoatchat(hc):
                hc = str(hc).lower()
                if any(x in hc for x in ['cef','peni','mycin','levo']): return 'Kháng sinh'
                elif any(x in hc for x in ['losartan','amlodipin','pril']): return 'Tim mạch'
                elif any(x in hc for x in ['metformin','insulin']): return 'Đái tháo đường'
                elif any(x in hc for x in ['paracetamol','ibu','meloxi']): return 'Giảm đau'
                elif any(x in hc for x in ['pantoprazol','omeprazol']): return 'Tiêu hóa'
                elif any(x in hc for x in ['cisplatin','doxo']): return 'Ung thư'
                else: return 'Khác'

            df_dm['Nhóm điều trị'] = df_dm['Tên hoạt chất'].apply(classify_hoatchat)
            group_dt = df_dm.groupby('Nhóm điều trị').agg(SL=('Số lượng','sum'), Giá=('Trị giá thầu','sum')).sort_values(by='Giá', ascending=False)
            st.dataframe(group_dt)

        except Exception as e:
            st.error(f"❌ Lỗi khi xử lý: {e}")
    else:
        st.info("⬆️ Tải lên file danh mục thầu bệnh viện để bắt đầu phân tích.")
