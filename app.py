
import streamlit as st
import pandas as pd
import io



def standardize_column_names(df):
    rename_map = {}
    for col in df.columns:
        lower_col = str(col).strip().lower()
        if ('hoạt chất' in lower_col or 'thành phần' in lower_col) and 'tên' in lower_col:
            rename_map[col] = 'Tên hoạt chất'
        elif 'nồng độ' in lower_col and 'hàm lượng' in lower_col:
            rename_map[col] = 'Nồng độ/Hàm lượng'
        elif 'nhóm' in lower_col:
            rename_map[col] = 'Nhóm thuốc'
        elif 'giá' in lower_col and 'hoạch' in lower_col:
            rename_map[col] = 'Giá kế hoạch'
        elif 'giá' in lower_col and 'dự' in lower_col:
            rename_map[col] = 'Giá kế hoạch'
        elif 'giá' in lower_col and 'tạm' in lower_col:
            rename_map[col] = 'Giá kế hoạch'
    df = df.rename(columns=rename_map)
    return df
    for col in df.columns:
        lower_col = str(col).strip().lower()
        if ('hoạt chất' in lower_col or 'thành phần' in lower_col) and 'tên' in lower_col:
            rename_map[col] = 'Tên hoạt chất'
        elif 'nồng độ' in lower_col and 'hàm lượng' in lower_col:
            rename_map[col] = 'Nồng độ/Hàm lượng'
        elif 'nhóm' in lower_col:
            rename_map[col] = 'Nhóm thuốc'
    df = df.rename(columns=rename_map)
    return df



def read_excel_with_auto_header(uploaded_file):
    for i in range(5):
        df_try = pd.read_excel(uploaded_file, header=i)
        cols = [str(c).lower() for c in df_try.columns]
        if any("tên hoạt chất" in c or "tên thành phần" in c for c in cols):
            df = pd.read_excel(uploaded_file, header=i)
            break
    else:
        df = pd.read_excel(uploaded_file, header=0)
    for col in df.columns:
        if "tên hoạt chất" in col.lower() or "tên thành phần" in col.lower():
            df.rename(columns={col: "Tên hoạt chất"}, inplace=True)
            break
    return df


st.set_page_config(page_title="Lọc & Phân tích Thầu BV", layout="wide")
st.title("📋 Hệ Thống Lọc & Phân Tích Danh Mục Thầu Bệnh Viện")

menu = st.sidebar.radio("Chọn chức năng", ["Lọc danh mục thầu", "Phân tích danh mục mời thầu", "Phân tích danh mục trúng thầu"])

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
            df1 = read_excel_with_auto_header(file1)
            df2 = read_excel_with_auto_header(file2)
            df3 = read_excel_with_auto_header(file3)

            df1 = standardize_column_names(df1)
            df2 = standardize_column_names(df2)

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

            tong_theo_hoatchat_hamluong = (
                df1.groupby(['Tên hoạt chất', 'Nồng độ/Hàm lượng'])['Số lượng'].sum().reset_index()
                .rename(columns={'Số lượng': 'Tổng SL cùng hoạt chất-hàm lượng'})
            )
            final_df = pd.merge(final_df, tong_theo_hoatchat_hamluong, on=['Tên hoạt chất', 'Nồng độ/Hàm lượng'], how='left')
            final_df['Tỉ trọng nhóm (%)'] = round(final_df['Số lượng'] / final_df['Tổng SL cùng hoạt chất-hàm lượng'] * 100, 2)

            for col in ['Số lượng', 'Giá kế hoạch', 'Tổng SL cùng hoạt chất-hàm lượng']:
                if col in final_df.columns:
                    final_df[col] = final_df[col].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) else x)
            if 'Tỉ trọng nhóm (%)' in final_df.columns:
                final_df['Tỉ trọng nhóm (%)'] = final_df['Tỉ trọng nhóm (%)'].apply(lambda x: f"{x:.2f}%")

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


elif menu == "Phân tích danh mục mời thầu":
    file_dm = st.file_uploader("Tải lên file Danh mục MỜI thầu của BV", type=["xls", "xlsx"], key="dmfile_moi")
    if file_dm:
        try:
            df_dm = read_excel_with_auto_header(file_dm)
            df_dm = standardize_column_names(df_dm)
            df_dm['Nhóm thuốc chuẩn'] = df_dm['Nhóm thuốc'].astype(str).str.extract(r'(\d)$')[0]
            df_dm['Trị giá thầu'] = df_dm['Số lượng'] * df_dm['Giá kế hoạch']

            st.subheader("📊 Thống kê nhóm thuốc")
            nhom_summary = df_dm.groupby('Nhóm thuốc chuẩn').agg(SL=('Số lượng','sum'), Giá=('Trị giá thầu','sum'))
            nhom_summary['SL'] = nhom_summary['SL'].apply(lambda x: f"{x:,.0f}")
            nhom_summary['Giá'] = nhom_summary['Giá'].apply(lambda x: f"{x:,.0f}")
            st.dataframe(nhom_summary)

            st.subheader("🚀 Thống kê theo đường dùng")
            duong_summary = df_dm.groupby('Đường dùng').agg(SL=('Số lượng','sum'), Giá=('Trị giá thầu','sum'))
            duong_summary['SL'] = duong_summary['SL'].apply(lambda x: f"{x:,.0f}")
            duong_summary['Giá'] = duong_summary['Giá'].apply(lambda x: f"{x:,.0f}")
            st.dataframe(duong_summary)

            st.subheader("🏅 Top 10 hoạt chất theo từng đường dùng")
            for route in ['Uống', 'Tiêm']:
                st.markdown(f"### 👉 {route}")
                top_route = df_dm[df_dm['Đường dùng'] == route].groupby('Tên hoạt chất').agg(SL=('Số lượng', 'sum')).sort_values(by='SL', ascending=False).head(10)
                top_route['SL'] = top_route['SL'].apply(lambda x: f"{x:,.0f}")
                st.dataframe(top_route)

            st.subheader("📌 Phân nhóm điều trị")
            def classify_hoatchat(hc):
                hc = str(hc).lower()
                if any(x in hc for x in ['cef','peni','mycin','levo']): return 'Kháng sinh'
                elif any(x in hc for x in ['losartan','amlodipin','pril','bisoprolol','clopidogrel','atorvastatin','trimetazidin']): return 'Tim mạch'
                elif any(x in hc for x in ['metformin','insulin']): return 'Đái tháo đường'
                elif any(x in hc for x in ['paracetamol','ibu','meloxi','diclofenac','naproxen','aspirin']): return 'Giảm đau'
                elif any(x in hc for x in ['pantoprazol','omeprazol','rabeprazol','ranitidin','domperidon']): return 'Tiêu hóa'
                elif any(x in hc for x in ['cisplatin','doxo']): return 'Ung thư'
                else: return 'Khác'

            df_dm['Nhóm điều trị'] = df_dm['Tên hoạt chất'].apply(classify_hoatchat)
            group_dt = df_dm.groupby('Nhóm điều trị').agg(SL=('Số lượng','sum'), Giá=('Trị giá thầu','sum')).sort_values(by='Giá', ascending=False)
            group_dt['SL'] = group_dt['SL'].apply(lambda x: f"{x:,.0f}")
            group_dt['Giá'] = group_dt['Giá'].apply(lambda x: f"{x:,.0f}")
            st.dataframe(group_dt)

            st.subheader("🔍 Xem chi tiết theo hoạt chất")
            selected_hoatchat = st.selectbox("Chọn hoạt chất", df_dm['Tên hoạt chất'].dropna().unique())
            df_detail = df_dm[df_dm['Tên hoạt chất'] == selected_hoatchat]
            st.dataframe(df_detail[['Tên hoạt chất', 'Nồng độ/Hàm lượng', 'Nhóm thuốc', 'Số lượng', 'Giá kế hoạch', 'Trị giá thầu']])
        except Exception as e:
            st.error(f"❌ Lỗi khi xử lý file mời thầu: {e}")

elif menu == "Phân tích danh mục trúng thầu":
    file_dm = st.file_uploader("Tải lên file Danh mục TRÚNG thầu của BV", type=["xls", "xlsx"], key="dmfile_trung")
    if file_dm:
        try:
            df_dm = read_excel_with_auto_header(file_dm)
            df_dm = standardize_column_names(df_dm)
            df_dm['Nhóm thuốc chuẩn'] = df_dm['Nhóm thuốc'].astype(str).str.extract(r'(\d)$')[0]
            df_dm['Trị giá thầu'] = df_dm['Số lượng'] * df_dm['Giá dự thầu']

            st.subheader("📊 Top 20 Nhà thầu trúng thầu theo trị giá")
            if 'Nhà thầu trúng thầu' in df_dm.columns:
                top_nt = df_dm.groupby('Nhà thầu trúng thầu')['Trị giá thầu'].sum().sort_values(ascending=False).head(20)
                top_nt = top_nt.apply(lambda x: f"{x:,.0f}")
                st.dataframe(top_nt)

            st.subheader("📌 Phân nhóm điều trị")
            def classify_hoatchat(hc):
                hc = str(hc).lower()
                if any(x in hc for x in ['cef','peni','mycin','levo']): return 'Kháng sinh'
                elif any(x in hc for x in ['losartan','amlodipin','pril','bisoprolol','clopidogrel','atorvastatin','trimetazidin']): return 'Tim mạch'
                elif any(x in hc for x in ['metformin','insulin']): return 'Đái tháo đường'
                elif any(x in hc for x in ['paracetamol','ibu','meloxi','diclofenac','naproxen','aspirin']): return 'Giảm đau'
                elif any(x in hc for x in ['pantoprazol','omeprazol','rabeprazol','ranitidin','domperidon']): return 'Tiêu hóa'
                elif any(x in hc for x in ['cisplatin','doxo']): return 'Ung thư'
                else: return 'Khác'
            df_dm['Nhóm điều trị'] = df_dm['Tên hoạt chất'].apply(classify_hoatchat)
            st.dataframe(df_dm[['Tên hoạt chất', 'Nhóm điều trị', 'Trị giá thầu']].head(20))

        except Exception as e:
            st.error(f"❌ Lỗi khi xử lý file trúng thầu: {e}")

    file_dm = st.file_uploader("Tải lên file Danh mục mời thầu của BV", type=["xls", "xlsx"], key="dmfile")

    if file_dm:
        try:
            df_dm = read_excel_with_auto_header(file_dm)
            df_dm['Nhóm thuốc chuẩn'] = df_dm['Nhóm thuốc'].astype(str).str.extract(r'(\d)$')[0]
            df_dm['Trị giá thầu'] = df_dm['Số lượng'] * df_dm['Giá kế hoạch']

            st.subheader("📊 Thống kê nhóm thuốc")
            nhom_summary = df_dm.groupby('Nhóm thuốc chuẩn').agg(SL=('Số lượng','sum'), Giá=('Trị giá thầu','sum'))
            nhom_summary['SL'] = nhom_summary['SL'].apply(lambda x: f"{x:,.0f}")
            nhom_summary['Giá'] = nhom_summary['Giá'].apply(lambda x: f"{x:,.0f}")
            st.dataframe(nhom_summary)

            st.subheader("🚀 Thống kê theo đường dùng")
            duong_summary = df_dm.groupby('Đường dùng').agg(SL=('Số lượng','sum'), Giá=('Trị giá thầu','sum'))
            duong_summary['SL'] = duong_summary['SL'].apply(lambda x: f"{x:,.0f}")
            duong_summary['Giá'] = duong_summary['Giá'].apply(lambda x: f"{x:,.0f}")
            st.dataframe(duong_summary)

            st.subheader("🏅 Top 10 hoạt chất theo từng đường dùng")
            for route in ['Uống', 'Tiêm']:
                st.markdown(f"### 👉 {route}")
                top_route = df_dm[df_dm['Đường dùng'] == route].groupby('Tên hoạt chất').agg(SL=('Số lượng', 'sum')).sort_values(by='SL', ascending=False).head(10)
                top_route['SL'] = top_route['SL'].apply(lambda x: f"{x:,.0f}")
                st.dataframe(top_route)

            st.subheader("📌 Phân nhóm điều trị")
            def classify_hoatchat(hc):
                hc = str(hc).lower()
                if any(x in hc for x in ['cef','peni','mycin','levo']): return 'Kháng sinh'
                elif any(x in hc for x in ['losartan','amlodipin','pril','bisoprolol','clopidogrel','atorvastatin','trimetazidin']): return 'Tim mạch'
                elif any(x in hc for x in ['metformin','insulin']): return 'Đái tháo đường'
                elif any(x in hc for x in ['paracetamol','ibu','meloxi','diclofenac','naproxen','aspirin']): return 'Giảm đau'
                elif any(x in hc for x in ['pantoprazol','omeprazol','rabeprazol','ranitidin','domperidon']): return 'Tiêu hóa'
                elif any(x in hc for x in ['cisplatin','doxo']): return 'Ung thư'
                else: return 'Khác'

            df_dm['Nhóm điều trị'] = df_dm['Tên hoạt chất'].apply(classify_hoatchat)
            group_dt = df_dm.groupby('Nhóm điều trị').agg(SL=('Số lượng','sum'), Giá=('Trị giá thầu','sum')).sort_values(by='Giá', ascending=False)
            group_dt['SL'] = group_dt['SL'].apply(lambda x: f"{x:,.0f}")
            group_dt['Giá'] = group_dt['Giá'].apply(lambda x: f"{x:,.0f}")
            st.dataframe(group_dt)

            st.subheader("🔍 Xem chi tiết theo hoạt chất")
            selected_hoatchat = st.selectbox("Chọn hoạt chất", df_dm['Tên hoạt chất'].dropna().unique())
            df_detail = df_dm[df_dm['Tên hoạt chất'] == selected_hoatchat]
            st.dataframe(df_detail[['Tên hoạt chất', 'Nồng độ/Hàm lượng', 'Nhóm thuốc', 'Số lượng', 'Giá kế hoạch', 'Trị giá thầu']])

        except Exception as e:
            st.error(f"❌ Lỗi khi xử lý: {e}")
    else:
        st.info("⬆️ Tải lên file danh mục thầu bệnh viện để bắt đầu phân tích.")
