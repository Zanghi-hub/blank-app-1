
import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.express as px
import os
import random  # Để gợi ý sản phẩm ngẫu nhiên
from geopy.distance import geodesic  # Thêm thư viện tính khoảng cách
import folium  # Thêm thư viện bản đồ
from streamlit_folium import folium_static  # Hiển thị bản đồ trong Streamlit

st.set_page_config(page_title="Hệ thống LIS - Quản lý Bán hàng Đa kênh", layout="wide")
st.title("📦 HỆ THỐNG LIS - BÁN HÀNG & GIAO HÀNG ĐA KÊNH")

menu = st.sidebar.radio("🔍 Bạn là:", ["👨‍💼 Doanh nghiệp", "🛍️ Khách hàng"])

# ------------------ DATA ------------------
kho_path = "data/kho.csv"
don_path = "data/don_hang.csv"
os.makedirs("data", exist_ok=True)

if os.path.exists(don_path):
    df_don = pd.read_csv(don_path)
else:
    df_don = pd.DataFrame(columns=[
        "ten_khach", "san_pham", "kenh", "trang_thai", "ngay_tao",
        "gia_tri", "khu_vuc", "don_vi_vc", "eta_ngay"
    ])

if os.path.exists(kho_path):
    df_kho = pd.read_csv(kho_path)
else:
    df_kho = pd.DataFrame(columns=["ten_sp", "so_luong", "gia"])

# ------------------ HÀM TÍNH KHOẢNG CÁCH ------------------
def tinh_khoang_cach(dia_chi_kho, dia_chi_khach):
    # Tọa độ các kho (giả lập)
    kho_toa_do = {
        "Kho HCM": (10.8231, 106.6297),
        "Kho Hà Nội": (21.0278, 105.8342),
        "Kho Đà Nẵng": (16.0544, 108.2022)
    }
    
    # Giả lập tọa độ khách hàng (trong thực tế dùng API Geocoding)
    khach_toa_do = {
        "HCM": (10.7758, 106.7019),
        "Hà Nội": (21.0285, 105.8542),
        "Đà Nẵng": (16.0680, 108.2127),
        "Khác": (10.9639, 106.8567)
    }
    
    try:
        kho = kho_toa_do[dia_chi_kho]
        khach = khach_toa_do[dia_chi_khach]
        return geodesic(kho, khach).km
    except:
        return None

# ------------------ HÀM TẠO BẢN ĐỒ ------------------
def tao_ban_do(dia_chi_kho, dia_chi_khach):
    # Tọa độ các kho (giả lập)
    kho_toa_do = {
        "Kho HCM": (10.8231, 106.6297),
        "Kho Hà Nội": (21.0278, 105.8342),
        "Kho Đà Nẵng": (16.0544, 108.2022)
    }
    
    # Giả lập tọa độ khách hàng
    khach_toa_do = {
        "HCM": (10.7758, 106.7019),
        "Hà Nội": (21.0285, 105.8542),
        "Đà Nẵng": (16.0680, 108.2127),
        "Khác": (10.9639, 106.8567)
    }
    
    try:
        kho = kho_toa_do[dia_chi_kho]
        khach = khach_toa_do[dia_chi_khach]
        
        # Tạo bản đồ
        m = folium.Map(location=[(kho[0]+khach[0])/2, (kho[1]+khach[1])/2], zoom_start=10)
        
        # Thêm marker cho kho
        folium.Marker(
            location=kho,
            popup=dia_chi_kho,
            icon=folium.Icon(color="green", icon="warehouse")
        ).add_to(m)
        
        # Thêm marker cho khách hàng
        folium.Marker(
            location=khach,
            popup=f"Khách hàng: {dia_chi_khach}",
            icon=folium.Icon(color="red", icon="user")
        ).add_to(m)
        
        # Vẽ đường đi (giả lập)
        folium.PolyLine(
            locations=[kho, khach],
            color="blue",
            weight=2.5,
            opacity=1
        ).add_to(m)
        
        return m
    except:
        return None

# ------------------ DOANH NGHIỆP ------------------
if menu == "👨‍💼 Doanh nghiệp":
    st.header("📦 Quản lý đơn hàng & Bán hàng đa kênh")
    tabs = st.tabs([
        "📋 Đơn hàng", "➕ Lên đơn", "📊 Thống kê", "🚚 Giao hàng & Kho", "📤 Xuất báo cáo", "📈 Phân tích doanh thu"
    ])

    with tabs[0]:
        st.subheader("📋 Danh sách đơn hàng")
        st.dataframe(df_don, use_container_width=True)

    with tabs[1]:
        st.subheader("➕ Tạo đơn hàng mới")
        with st.form("form_don"):
            ten_khach = st.text_input("👤 Tên khách hàng")
            san_pham = st.selectbox("📦 Chọn sản phẩm", df_kho["ten_sp"].unique() if not df_kho.empty else [])
            so_luong = st.number_input("🔢 Số lượng", 1, step=1)
            kenh = st.selectbox("🛒 Kênh bán hàng", ["Website", "Shopee", "Lazada", "Zalo OA"])
            khu_vuc = st.selectbox("📍 Khu vực giao hàng", ["HCM", "Hà Nội", "Đà Nẵng", "Khác"])
            ngay_tao = st.date_input("📅 Ngày tạo", value=datetime.date.today())
            submit = st.form_submit_button("📤 Lưu đơn hàng")

            if submit:
                if not ten_khach or not san_pham:
                    st.warning("⚠️ Vui lòng nhập đầy đủ thông tin")
                else:
                    def get_vc_eta(khu_vuc):
                        options = {
                            "HCM": ("GHTK", 1),
                            "Hà Nội": ("GHN", 2),
                            "Đà Nẵng": ("VNPost", 3),
                            "Khác": ("Viettel Post", 5)
                        }
                        return options.get(khu_vuc, ("VNPost", 5))

                    don_vi_vc, eta = get_vc_eta(khu_vuc)
                    mask = df_kho["ten_sp"].str.lower() == san_pham.lower()

                    if mask.any():
                        index = df_kho[mask].index[0]
                        if df_kho.at[index, "so_luong"] >= so_luong:
                            df_kho.at[index, "so_luong"] -= so_luong
                            don_gia = df_kho.at[index, "gia"]
                            tong_tien = don_gia * so_luong

                            df_kho.to_csv(kho_path, index=False)

                            new_row = pd.DataFrame([[ten_khach, san_pham, kenh, "Chờ xử lý",
                                                     ngay_tao, tong_tien, khu_vuc,
                                                     don_vi_vc, eta]],
                                                   columns=df_don.columns)
                            df_don = pd.concat([df_don, new_row], ignore_index=True)
                            df_don.to_csv(don_path, index=False)

                            st.success("✅ Đơn hàng đã được tạo!")

                            st.markdown("### 🧾 Hóa đơn")
                            st.info(f"""
**Khách hàng**: {ten_khach}  
**Sản phẩm**: {san_pham}  
**Số lượng**: {so_luong}  
**Giá**: {don_gia:,.0f} đ  
**Tổng tiền**: {tong_tien:,.0f} đ  
**Vận chuyển**: {don_vi_vc} - ETA {eta} ngày
""")
                            
                            # Tính khoảng cách và hiển thị bản đồ
                            distance = tinh_khoang_cach("Kho HCM", khu_vuc)  # Giả sử kho HCM là kho xuất phát
                            if distance:
                                st.success(f"📏 Khoảng cách từ Kho HCM đến {khu_vuc}: {distance:.2f} km")
                                map_obj = tao_ban_do("Kho HCM", khu_vuc)
                                folium_static(map_obj, width=700, height=400)
                            else:
                                st.warning("Không thể tính khoảng cách.")
                            
                        else:
                            st.error("❌ Không đủ tồn kho!")
                    else:
                        st.error("⚠️ Sản phẩm không tồn tại trong kho")

    with tabs[2]:
        st.subheader("📊 Thống kê đơn hàng")
        col1, col2, col3 = st.columns(3)
        col1.metric("Tổng đơn", len(df_don))
        col2.metric("Đơn đang giao", (df_don["trang_thai"] == "Đang giao").sum())
        col3.metric("ETA trung bình", f"{df_don['eta_ngay'].mean():.1f} ngày")
        st.plotly_chart(px.pie(df_don, names="kenh", title="Tỉ lệ kênh bán"))

    with tabs[3]:
        st.subheader("🚚 Vận chuyển & Gợi ý kho")
        khu = st.selectbox("Chọn khu vực giao hàng", df_don["khu_vuc"].unique())
        st.info(f"🏬 Kho phù hợp: {'Kho HCM' if khu=='HCM' else 'Kho Hà Nội' if khu=='Hà Nội' else 'Kho Miền Trung'}")

    with tabs[4]:
        st.subheader("📥 Xuất báo cáo")
        if st.button("Tải báo cáo Excel"):
            df_don.to_excel("bao_cao_don.xlsx", index=False)
            with open("bao_cao_don.xlsx", "rb") as f:
                st.download_button("📥 Tải xuống", data=f, file_name="bao_cao_don.xlsx")

    # ------------------ PHÂN TÍCH DOANH THU ------------------
    with tabs[5]:
        st.subheader("📈 Phân tích doanh thu theo kênh")
        revenue_by_channel = df_don.groupby("kenh")["gia_tri"].sum().reset_index()
        st.bar_chart(revenue_by_channel.set_index("kenh"))

        # Phân tích doanh thu theo thời gian
        st.subheader("📅 Doanh thu theo thời gian")
        df_don["ngay_tao"] = pd.to_datetime(df_don["ngay_tao"])
        revenue_by_date = df_don.groupby(df_don["ngay_tao"].dt.date)["gia_tri"].sum().reset_index()
        st.line_chart(revenue_by_date.set_index("ngay_tao"))

# ------------------ KHÁCH HÀNG ------------------
else:
    st.header("🛍️ Trải nghiệm mua sắm")

    # Theo dõi đơn hàng theo thời gian thực
    st.subheader("🔍 Theo dõi đơn hàng")
    order_id = st.text_input("Nhập mã đơn hàng để theo dõi")
    if st.button("🔎 Theo dõi"):
        order_status = df_don[df_don["ten_khach"].str.contains(order_id, na=False)]
        if not order_status.empty:
            st.success(f"Trạng thái đơn hàng: {order_status['trang_thai'].values[0]}")
        else:
            st.warning("❌ Không tìm thấy đơn hàng với mã này.")

    # Chương trình khuyến mãi
    st.subheader("🎉 Nhập mã giảm giá")
    promo_code = st.text_input("Nhập mã giảm giá")
    if st.button("Áp dụng"):
        if promo_code == "DISCOUNT10":
            st.success("✅ Mã giảm giá hợp lệ! Bạn được giảm 10% cho đơn hàng này.")
        else:
            st.error("❌ Mã giảm giá không hợp lệ.")

    st.subheader("🔍 Tra cứu đơn hàng")
    name = st.text_input("Nhập tên khách hàng hoặc sản phẩm")
    if st.button("🔎 Tra cứu"):
        result = df_don[df_don["ten_khach"].str.contains(name, case=False, na=False) |
                        df_don["san_pham"].str.contains(name, case=False, na=False)]
        if not result.empty:
            st.dataframe(result)
        else:
            st.warning("❌ Không tìm thấy đơn phù hợp")

    st.subheader("⭐ Gửi đánh giá")
    ten = st.text_input("Tên bạn")
    rate = st.slider("Chất lượng (1-5)", 1, 5)
    comment = st.text_area("Ý kiến")
    if st.button("📤 Gửi"):
        if ten and comment:
            st.success("💬 Cảm ơn phản hồi của bạn!")
            # Lưu đánh giá vào file hoặc cơ sở dữ liệu (có thể mở rộng thêm)
        else:
            st.warning("⚠️ Vui lòng nhập tên và ý kiến của bạn")

    st.subheader("💬 Chatbot hỗ trợ")
    st.info("Vui lòng nhập câu hỏi để được hỗ trợ về vận đơn, thanh toán, mua hàng...")

    # Chatbot đơn giản
    user_input = st.text_input("Nhập câu hỏi của bạn...")
    if user_input:
        if "trạng thái" in user_input.lower():
            st.success("Bạn vui lòng cung cấp mã đơn hàng hoặc tên/SĐT để tra cứu trạng thái đơn hàng.")
        elif "đổi trả" in user_input.lower():
            st.success("Chính sách đổi trả trong vòng 7 ngày với điều kiện sản phẩm còn nguyên seal.")
        elif "thanh toán" in user_input.lower():
            st.success("Chúng tôi hỗ trợ thanh toán qua: COD, chuyển khoản, VNPay, Momo và thẻ quốc tế.")
        else:
            st.warning("Tôi chưa hiểu rõ câu hỏi. Bạn vui lòng liên hệ hotline 1900 1234 để được hỗ trợ trực tiếp.")

    st.subheader("🛒 Gợi ý lần mua tiếp")
    if not df_don.empty:
        sp_pho_bien = df_don["san_pham"].value_counts().idxmax()
        st.success(f"🎁 Gợi ý: {sp_pho_bien}")

    # Lịch sử mua hàng
    st.subheader("📜 Lịch sử mua hàng")
    if not df_don.empty:
        st.dataframe(df_don[df_don["ten_khach"].str.contains(name, case=False, na=False)])
    else:
        st.warning("Chưa có lịch sử mua hàng.")

    # Gợi ý sản phẩm dựa trên sở thích
    st.subheader("🎁 Gợi ý sản phẩm cho bạn")
    if not df_don.empty:
        popular_product = df_don["san_pham"].value_counts().idxmax()
        st.success(f"Gợi ý sản phẩm: {popular_product}")

    # Hệ thống tích điểm
    st.subheader("📈 Tích điểm thưởng")
    points = random.randint(100, 1000)  # Giả lập điểm tích lũy
    st.metric("Điểm tích lũy của bạn", points)
    if st.button("Đổi điểm lấy quà"):
        st.success("Bạn đã đổi điểm thành công!")
