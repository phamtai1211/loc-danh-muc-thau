import streamlit as st
import pandas as pd
import numpy as np
import re
import requests
from io import BytesIO
import plotly.express as px

# Tải dữ liệu mặc định từ GitHub (file2, file3, file4)
@st.cache_data
def load_default_data():
    url_file2 = "https://raw.githubusercontent.com/phamtai1211/Thau_3PPharma/main/file2.xlsx"
    url_file3 = "https://raw.githubusercontent.com/phamtai1211/Thau_3PPharma/main/file3.xlsx"
    url_file4 = "https://raw.githubusercontent.com/phamtai1211/Thau_3PPharma/main/nhom_dieu_tri.xlsx"

    file2 = pd.read_excel(BytesIO(requests.get(url_file2).content))
    file3 = pd.read_excel(BytesIO(requests.get(url_file3).content))
    file4 = pd.read_excel(BytesIO(requests.get(url_file4).content))
    return file2, file3, file4

file2, file3, file4 = load_default_data()

# Hàm tiện ích chuẩn hóa chuỗi để so sánh (không phân biệt hoa thường, khoảng trắng, ký tự đặc biệt)
def normalize_active(name: str) -> str:
    # Bỏ nội dung trong ngoặc đơn, chuyển về chữ thường, bỏ dư khoảng trắng
    return re.sub(r'\s+', ' ', re.sub(r'\(.*?\)', '', str(name))).strip().lower()

def normalize_concentration(conc: str) -> str:
    s = str(conc).lower()
    # Thay dấu phẩy bằng dấu chấm (cho số thập phân)
    s = s.replace(',', '.')
    # Bỏ cụm 'dung tích'
    s = s.replace('dung tích', '')
    # Tách các phần bởi dấu comma nếu có
    parts = [p.strip() for p in s.split(',') if p.strip() != '']
    # Loại bỏ các phần chỉ chứa chữ (mô tả) không có số
    parts = [p for p in parts if re.search(r'\d', p)]
    # Nếu có 2 phần dạng "X mg" và "Y ml" thì ghép thành "Xmg/Yml"
    if len(parts) >= 2 and re.search(r'(mg|mcg|g|%)', parts[0]) and 'ml' in parts[-1] and '/' not in parts[0]:
        conc_norm = parts[0].replace(' ', '') + '/' + parts[-1].replace(' ', '')
    else:
        conc_norm = ''.join([p.replace(' ', '') for p in parts])
    # Chuẩn hóa dấu cộng (nếu có dạng "mg + mg")
    conc_norm = conc_norm.replace('+', '+')
    return conc_norm

def normalize_group(grp: str) -> str:
    # Trích phần số trong mã nhóm thuốc (vd "Nhóm 4" -> "4", "N4" -> "4")
    return re.sub(r'\D', '', str(grp)).strip()

# Sidebar: Chọn chức năng chính
st.sidebar.title("Chức năng")
option = st.sidebar.radio("Chọn chức năng", 
    ["Lọc Danh Mục Thầu", "Phân Tích Danh Mục Thầu", "Phân Tích Danh Mục Trúng Thầu", "Đề Xuất Hướng Triển Khai"])

# 1. Lọc Danh Mục Thầu
if option == "Lọc Danh Mục Thầu":
    st.header("📂 Lọc Danh Mục Thầu")
    # Chọn Miền
    regions = sorted(file3["Miền"].dropna().unique())
    selected_region = st.selectbox("Chọn Miền", regions)
    sub_df = file3[file3["Miền"] == selected_region] if selected_region else file3.copy()
    # Chọn Vùng (nếu có)
    areas = sorted(sub_df["Vùng"].dropna().unique())
    selected_area = None
    if areas:
        selected_area = st.selectbox("Chọn Vùng", ["(Tất cả)"] + areas)
        if selected_area and selected_area != "(Tất cả)":
            sub_df = sub_df[sub_df["Vùng"] == selected_area]
    # Chọn Tỉnh
    provinces = sorted(sub_df["Tỉnh"].dropna().unique())
    selected_prov = st.selectbox("Chọn Tỉnh", provinces)
    sub_df = sub_df[sub_df["Tỉnh"] == selected_prov] if selected_prov else sub_df
    # Chọn Bệnh viện/SYT
    hospitals = sorted(sub_df["Bệnh viện/SYT"].dropna().unique())
    selected_hospital = st.selectbox("Chọn Bệnh viện/Sở Y Tế", hospitals)
    # Upload file danh mục mời thầu
    uploaded_file = st.file_uploader("Tải lên file Danh Mục Mời Thầu (.xlsx)", type=["xlsx"])
    if uploaded_file is not None and selected_hospital:
        # Đọc Excel và xác định sheet chứa dữ liệu chính
        xls = pd.ExcelFile(uploaded_file)
        sheet_name = None
        max_cols = 0
        for name in xls.sheet_names:
            try:
                df_test = xls.parse(name, nrows=1, header=None)
                cols = df_test.shape[1]
            except Exception:
                cols = 0
            if cols > max_cols:
                max_cols = cols
                sheet_name = name
        if sheet_name is None:
            st.error("❌ Không tìm thấy sheet dữ liệu phù hợp trong file.")
        else:
            # Đọc toàn bộ sheet (không đặt header) để tìm dòng tiêu đề
            df_raw = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=None)
            header_index = None
            for i in range(10):
                row = " ".join(df_raw.iloc[i].fillna('').astype(str).tolist())
                if "Tên hoạt chất" in row and "Số lượng" in row:
                    header_index = i
                    break
            if header_index is None:
                st.error("❌ Không xác định được dòng tiêu đề trong file.")
            else:
                # Tạo DataFrame với header chính xác
                header = df_raw.iloc[header_index].tolist()
                df_all = df_raw.iloc[header_index+1:].reset_index(drop=True)
                df_all.columns = header
                # Bỏ các dòng trống hoàn toàn (nếu có)
                df_all = df_all.dropna(how='all').reset_index(drop=True)
                # So sánh 3 cột (hoạt chất, hàm lượng, nhóm thuốc) với danh mục công ty (file2)
                df_all["active_norm"] = df_all["Tên hoạt chất"].apply(normalize_active)
                df_all["conc_norm"] = df_all["Nồng độ/hàm lượng"].apply(normalize_concentration)
                df_all["group_norm"] = df_all["Nhóm thuốc"].apply(normalize_group)
                df_comp = file2.copy()
                df_comp["active_norm"] = df_comp["Tên hoạt chất"].apply(normalize_active)
                df_comp["conc_norm"] = df_comp["Nồng độ/Hàm lượng"].apply(normalize_concentration)
                df_comp["group_norm"] = df_comp["Nhóm thuốc"].apply(normalize_group)
                # Inner merge để giữ lại các dòng khớp với danh mục công ty
                merged_df = pd.merge(df_all, df_comp, on=["active_norm", "conc_norm", "group_norm"], how="inner", suffixes=(None, "_comp"))
                # Chọn các cột gốc + tên sản phẩm (brand), đồng thời gắn Địa bàn và Khách hàng phụ trách
                result_columns = df_all.columns.tolist() + ["Tên sản phẩm"]
                result_df = merged_df[result_columns].copy()
                # Thêm thông tin Địa bàn, Khách hàng phụ trách từ file3
                hosp_data = file3[file3["Bệnh viện/SYT"] == selected_hospital][["Tên sản phẩm", "Địa bàn", "Tên Khách hàng phụ trách triển khai"]]
                result_df = pd.merge(result_df, hosp_data, on="Tên sản phẩm", how="left")
                # Tính cột "Tỷ trọng SL/DM Tổng"
                # Lập bảng tổng số lượng theo Nhóm điều trị cho toàn bộ danh mục thầu (df_all)
                # Ánh xạ hoạt chất -> nhóm điều trị từ file4
                treat_map = { normalize_active(a): grp for a, grp in zip(file4["Hoạt chất"], file4["Nhóm điều trị"]) }
                group_total = {}
                for _, row in df_all.iterrows():
                    act = normalize_active(row["Tên hoạt chất"])
                    group = treat_map.get(act)
                    qty = pd.to_numeric(row.get("Số lượng", 0), errors='coerce')
                    if pd.isna(qty):
                        qty = 0
                    if group:
                        group_total[group] = group_total.get(group, 0) + float(qty)
                # Tính tỷ trọng cho từng dòng kết quả
                ratios = []
                for _, row in result_df.iterrows():
                    act = normalize_active(row["Tên hoạt chất"])
                    group = treat_map.get(act)
                    qty = pd.to_numeric(row.get("Số lượng", 0), errors='coerce')
                    if pd.isna(qty) or group is None or group not in group_total or group_total[group] == 0:
                        ratios.append(None)
                    else:
                        ratio = float(qty) / group_total[group]
                        ratios.append(f"{ratio:.2%}")
                result_df["Tỷ trọng SL/DM Tổng"] = ratios
                # Hiển thị kết quả lọc và nút tải về
                st.success(f"✅ Đã lọc được {len(result_df)} mục thuốc thuộc danh mục công ty.")
                st.dataframe(result_df.head(10))
                # Xuất file Excel kết quả
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    result_df.to_excel(writer, sheet_name="KetQuaLoc", index=False)
                st.download_button("⬇️ Tải File Kết Quả", data=output.getvalue(), file_name="Ketqua_loc.xlsx")
                # Lưu DataFrame đã lọc vào session_state để dùng cho phân tích
                st.session_state["filtered_df"] = result_df
                st.session_state["selected_hospital"] = selected_hospital

# 2. Phân Tích Danh Mục Thầu
elif option == "Phân Tích Danh Mục Thầu":
    st.header("📊 Phân Tích Danh Mục Thầu")
    if "filtered_df" not in st.session_state:
        st.info("Vui lòng thực hiện bước 'Lọc Danh Mục Thầu' trước.")
    else:
        df_filtered = st.session_state["filtered_df"].copy()
        # Đảm bảo kiểu dữ liệu số
        df_filtered["Số lượng"] = pd.to_numeric(df_filtered["Số lượng"], errors='coerce').fillna(0)
        df_filtered["Giá kế hoạch"] = pd.to_numeric(df_filtered["Giá kế hoạch"], errors='coerce').fillna(0)
        # Thêm cột trị giá = Số lượng * Giá kế hoạch
        df_filtered["Trị giá"] = df_filtered["Số lượng"] * df_filtered["Giá kế hoạch"]
        # Biểu đồ 1: Nhóm thầu sử dụng nhiều nhất theo trị giá
        group_val = df_filtered.groupby("Nhóm thuốc")["Trị giá"].sum().reset_index().sort_values("Trị giá", ascending=False)
        fig1 = px.bar(group_val, x="Nhóm thuốc", y="Trị giá", title="Trị giá theo Nhóm thầu (gói thầu)")
        st.plotly_chart(fig1, use_container_width=True)
        # Biểu đồ 2: Phân tích đường dùng (tiêm/uống) theo trị giá
        # Xác định loại đường dùng cho từng mục (Tiêm, Uống hoặc Khác)
        route_df = df_filtered.copy()
        def classify_route(route_str):
            route = str(route_str).lower()
            if "tiêm" in route:
                return "Tiêm"
            elif "uống" in route:
                return "Uống"
            else:
                return "Khác"
        route_df["Loại đường dùng"] = route_df["Đường dùng"].apply(classify_route)
        route_val = route_df.groupby("Loại đường dùng")["Trị giá"].sum().reset_index()
        fig2 = px.pie(route_val, names="Loại đường dùng", values="Trị giá", title="Tỷ trọng trị giá theo đường dùng")
        st.plotly_chart(fig2, use_container_width=True)
        # Biểu đồ 3: Top 10 hoạt chất theo Số lượng
        top_active_qty = df_filtered.groupby("Tên hoạt chất")["Số lượng"].sum().reset_index().sort_values("Số lượng", ascending=False).head(10)
        fig3 = px.bar(top_active_qty, x="Tên hoạt chất", y="Số lượng", title="Top 10 Hoạt chất (theo Số lượng)")
        st.plotly_chart(fig3, use_container_width=True)
        # Biểu đồ 4: Top 10 hoạt chất theo Trị giá
        top_active_val = df_filtered.groupby("Tên hoạt chất")["Trị giá"].sum().reset_index().sort_values("Trị giá", ascending=False).head(10)
        fig4 = px.bar(top_active_val, x="Tên hoạt chất", y="Trị giá", title="Top 10 Hoạt chất (theo Trị giá)")
        st.plotly_chart(fig4, use_container_width=True)
        # Biểu đồ 5: Phân tích Nhóm điều trị và top 10 sản phẩm
        # Gắn cột Nhóm điều trị cho từng mục
        treat_map = { normalize_active(a): grp for a, grp in zip(file4["Hoạt chất"], file4["Nhóm điều trị"]) }
        df_filtered["Nhóm điều trị"] = df_filtered["Tên hoạt chất"].apply(lambda x: treat_map.get(normalize_active(x), "Khác"))
        # Tổng trị giá theo nhóm điều trị
        treat_val = df_filtered.groupby("Nhóm điều trị")["Trị giá"].sum().reset_index().sort_values("Trị giá", ascending=False)
        fig5 = px.bar(treat_val, x="Trị giá", y="Nhóm điều trị", orientation='h', title="Trị giá theo Nhóm điều trị")
        st.plotly_chart(fig5, use_container_width=True)
        # Chọn nhóm điều trị để xem Top 10 sản phẩm
        groups = treat_val["Nhóm điều trị"].tolist()
        selected_grp = st.selectbox("Chọn Nhóm điều trị để xem Top 10 sản phẩm", groups)
        if selected_grp:
            top_products = df_filtered[df_filtered["Nhóm điều trị"] == selected_grp].groupby("Tên sản phẩm")["Trị giá"].sum().reset_index().sort_values("Trị giá", ascending=False).head(10)
            fig6 = px.bar(top_products, x="Trị giá", y="Tên sản phẩm", orientation='h', title=f"Top 10 sản phẩm - Nhóm {selected_grp}")
            st.plotly_chart(fig6, use_container_width=True)
        # Biểu đồ 6: Hiệu quả theo Tên khách hàng phụ trách triển khai (tổng trị giá theo người phụ trách)
        rep_val = df_filtered.groupby("Tên Khách hàng phụ trách triển khai")["Trị giá"].sum().reset_index().sort_values("Trị giá", ascending=False)
        fig7 = px.bar(rep_val, x="Trị giá", y="Tên Khách hàng phụ trách triển khai", orientation='h', title="Trị giá theo Khách hàng phụ trách")
        st.plotly_chart(fig7, use_container_width=True)

# 3. Phân Tích Danh Mục Trúng Thầu
elif option == "Phân Tích Danh Mục Trúng Thầu":
    st.header("🏆 Phân Tích Danh Mục Trúng Thầu")
    win_file = st.file_uploader("Tải lên file Kết Quả Trúng Thầu (.xlsx)", type=["xlsx"])
    invite_file = st.file_uploader("Tải lên file Danh Mục Mời Thầu (để đối chiếu, tùy chọn)", type=["xlsx"])
    if win_file is not None:
        # Xác định sheet chính của file trúng thầu
        xls_win = pd.ExcelFile(win_file)
        win_sheet = xls_win.sheet_names[0]
        max_cols = 0
        for name in xls_win.sheet_names:
            try:
                df_test = xls_win.parse(name, nrows=1, header=None)
                cols = df_test.shape[1]
            except:
                cols = 0
            if cols > max_cols:
                max_cols = cols
                win_sheet = name
        # Đọc toàn bộ sheet và xác định dòng tiêu đề
        df_win_raw = pd.read_excel(win_file, sheet_name=win_sheet, header=None)
        header_idx = None
        for i in range(10):
            row_text = " ".join(df_win_raw.iloc[i].fillna('').astype(str).tolist())
            if "Tên hoạt chất" in row_text and "Nhà thầu trúng" in row_text:
                header_idx = i
                break
        if header_idx is None:
            st.error("❌ Không xác định được tiêu đề cột trong file trúng thầu.")
        else:
            header = df_win_raw.iloc[header_idx].tolist()
            df_win = df_win_raw.iloc[header_idx+1:].reset_index(drop=True)
            df_win.columns = header
            df_win = df_win.dropna(how='all').reset_index(drop=True)
            # Chuyển kiểu số cho Số lượng và giá
            df_win["Số lượng"] = pd.to_numeric(df_win.get("Số lượng", 0), errors='coerce').fillna(0)
            # Xác định cột giá trúng (nếu không có thì dùng Giá kế hoạch)
            price_col = None
            for col in df_win.columns:
                if "Giá trúng" in str(col):
                    price_col = col
                    break
            if price_col is None:
                price_col = "Giá kế hoạch"
            df_win[price_col] = pd.to_numeric(df_win.get(price_col, 0), errors='coerce').fillna(0)
            # Tính trị giá trúng thầu mỗi mục
            df_win["Trị giá"] = df_win["Số lượng"] * df_win[price_col]
            # Biểu đồ: Top 20 nhà thầu trúng trị giá cao nhất
            win_val = df_win.groupby("Nhà thầu trúng")["Trị giá"].sum().reset_index().sort_values("Trị giá", ascending=False).head(20)
            fig_w1 = px.bar(win_val, x="Trị giá", y="Nhà thầu trúng", orientation='h', title="Top 20 Nhà thầu trúng (theo trị giá)")
            st.plotly_chart(fig_w1, use_container_width=True)
            # Biểu đồ: Phân tích theo nhóm điều trị (cơ cấu trị giá)
            df_win["Nhóm điều trị"] = df_win["Tên hoạt chất"].apply(lambda x: treat_map.get(normalize_active(x), "Khác"))
            treat_win = df_win.groupby("Nhóm điều trị")["Trị giá"].sum().reset_index().sort_values("Trị giá", ascending=False)
            fig_w2 = px.pie(treat_win, names="Nhóm điều trị", values="Trị giá", title="Cơ cấu trị giá theo Nhóm điều trị (Trúng thầu)")
            st.plotly_chart(fig_w2, use_container_width=True)
            # Nếu có upload danh mục mời thầu để đối chiếu
            if invite_file is not None:
                xls_inv = pd.ExcelFile(invite_file)
                inv_sheet = xls_inv.sheet_names[0]
                df_inv_raw = pd.read_excel(invite_file, sheet_name=inv_sheet, header=None)
                header_idx2 = None
                for i in range(10):
                    row_text = " ".join(df_inv_raw.iloc[i].fillna('').astype(str).tolist())
                    if "Tên hoạt chất" in row_text and "Số lượng" in row_text:
                        header_idx2 = i
                        break
                if header_idx2 is not None:
                    header2 = df_inv_raw.iloc[header_idx2].tolist()
                    df_inv_full = df_inv_raw.iloc[header_idx2+1:].reset_index(drop=True)
                    df_inv_full.columns = header2
                    df_inv_full = df_inv_full.dropna(how='all').reset_index(drop=True)
                    # So sánh các mục không trúng (có trong mời thầu nhưng không có trong trúng thầu)
                    if "Mã phần (Lô)" in df_inv_full.columns and "Mã phần (Lô)" in df_win.columns:
                        inv_ids = set(df_inv_full["Mã phần (Lô)"].astype(str))
                        win_ids = set(df_win["Mã phần (Lô)"].astype(str))
                        missing_ids = inv_ids - win_ids
                        missing_items = df_inv_full[df_inv_full["Mã phần (Lô)"].astype(str).isin(missing_ids)]
                    else:
                        # Dùng kết hợp hoạt chất + hàm lượng để đối chiếu nếu không có Mã phần
                        inv_keys = df_inv_full["Tên hoạt chất"].astype(str) + df_inv_full["Nồng độ/hàm lượng"].astype(str)
                        win_keys = df_win["Tên hoạt chất"].astype(str) + df_win["Nồng độ/hàm lượng"].astype(str)
                        missing_mask = ~inv_keys.isin(win_keys)
                        missing_items = df_inv_full[missing_mask]
                    if not missing_items.empty:
                        st.write("**Các thuốc mời thầu không có nhà thầu trúng:**")
                        st.dataframe(missing_items[["Tên hoạt chất", "Nồng độ/hàm lượng", "Số lượng", "Giá kế hoạch"]])
                        st.write(f"📌 Số lượng thuốc không trúng thầu: {len(missing_items)}")
                        # Lưu vào session_state để dùng cho đề xuất
                        st.session_state["missing_items"] = missing_items
                    else:
                        st.write("✅ Tất cả thuốc mời thầu đều đã có nhà thầu trúng.")

# 4. Đề Xuất Hướng Triển Khai
elif option == "Đề Xuất Hướng Triển Khai":
    st.header("💡 Đề Xuất Hướng Triển Khai")
    if "filtered_df" not in st.session_state:
        st.info("Vui lòng thực hiện phân tích trước để có dữ liệu.")
    else:
        df_filtered = st.session_state["filtered_df"]
        hospital = st.session_state.get("selected_hospital", "")
        # Danh sách đề xuất
        suggestions_yes = []  # nên triển khai
        suggestions_no = []   # không nên triển khai
        # 1. Các sản phẩm trong danh mục công ty tại bệnh viện nhưng chưa có trong danh mục mời thầu
        hosp_products = set(file3[file3["Bệnh viện/SYT"] == hospital]["Tên sản phẩm"])
        included_products = set(df_filtered["Tên sản phẩm"])
        not_included = hosp_products - included_products
        # Xác định nhóm bệnh viện tương tự (cùng Miền, cùng loại SYT hoặc BV)
        hosp_info = file3[file3["Bệnh viện/SYT"] == hospital].iloc[0] if not file3[file3["Bệnh viện/SYT"] == hospital].empty else None
        similar_df = file3.copy()
        if hosp_info is not None:
            if "SYT" in hospital:
                # các Sở Y Tế khác trong cùng Miền
                similar_df = similar_df[similar_df["Bệnh viện/SYT"].str.contains("SYT") & (similar_df["Miền"] == hosp_info["Miền"])]
            else:
                # các Bệnh viện khác (không phải SYT) trong cùng Miền
                similar_df = similar_df[~similar_df["Bệnh viện/SYT"].str.contains("SYT") & (similar_df["Miền"] == hosp_info["Miền"])]
        for prod in not_included:
            if prod in set(similar_df["Tên sản phẩm"]):
                suggestions_yes.append(f"- Nên triển khai **{prod}**: Sản phẩm chưa có trong thầu của {hospital}, nhưng nhiều đơn vị tương tự đã có nhu cầu.")
            else:
                suggestions_no.append(f"- Chưa cần triển khai **{prod}**: Sản phẩm chưa có trong thầu {hospital} và chưa phổ biến ở nhóm bệnh viện tương tự.")
        # 2. Các sản phẩm mời thầu nhưng không có nhà thầu trúng (nếu có)
        if "missing_items" in st.session_state:
            missing_items = st.session_state["missing_items"]
            for _, row in missing_items.iterrows():
                suggestions_yes.append(f"- Thử triển khai **{row['Tên hoạt chất']}**: Thuốc được mời thầu {hospital} nhưng chưa có nhà thầu trúng, có thể là cơ hội đưa sản phẩm vào.")
        # 3. Các sản phẩm có đối thủ trúng thầu (công ty chưa trúng)
        # Giả sử công ty theo dõi các sản phẩm đã được đưa vào thầu (df_filtered), nếu không trúng thầu có thể cân nhắc mức độ ưu tiên
        if "missing_items" in st.session_state or "filtered_df" in st.session_state:
            # Nếu một sản phẩm có mặt trong danh mục mời thầu (của công ty) nhưng công ty không trúng -> đối thủ đã trúng
            # (Đơn giản coi như mọi mục trong df_filtered là công ty có tham gia, nếu không nằm trong missing_items tức là có người trúng)
            if "missing_items" in st.session_state:
                lost_df = df_filtered.copy()
                for _, miss in st.session_state["missing_items"].iterrows():
                    # loại các mục không ai trúng (đã xử lý ở trên)
                    lost_df = lost_df[~((lost_df["Tên hoạt chất"] == miss["Tên hoạt chất"]) & (lost_df["Nồng độ/hàm lượng"] == miss["Nồng độ/hàm lượng"]))]
            else:
                lost_df = df_filtered
            # Tất cả mục còn lại trong lost_df coi như có đối thủ trúng
            for _, row in lost_df.iterrows():
                suggestions_no.append(f"- Hạn chế tập trung **{row['Tên hoạt chất']}**: Đã có đối thủ trúng thầu tại {hospital}, cần cân nhắc nếu không có lợi thế cạnh tranh.")
        # Hiển thị đề xuất
        st.subheader("🔸 Đề xuất nên triển khai")
        if suggestions_yes:
            st.markdown("\n".join(suggestions_yes))
        else:
            st.write("Không có sản phẩm mới nào cần triển khai thêm tại thời điểm này.")
        st.subheader("🔹 Đề xuất không nên triển khai")
        if suggestions_no:
            st.markdown("\n".join(suggestions_no))
        else:
            st.write("Không có sản phẩm nào cần ngừng triển khai; tiếp tục duy trì các danh mục hiện có.")
