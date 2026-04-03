import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Strategic BI Dashboard", page_icon="📈", layout="wide")

# 2. HÀM TẢI VÀ XỬ LÝ DỮ LIỆU
@st.cache_data
def load_data():
    # Đọc file CSV
    df = pd.read_csv("amazon_laptop_prices_cleaned.csv")
    
    # Chuẩn hóa tên cột (viết thường, xóa khoảng trắng)
    df.columns = df.columns.str.strip().str.lower()
    
    # Xử lý cột giá (price)
    if 'price' in df.columns and df['price'].dtype == 'O':
        df['price'] = df['price'].astype(str).str.replace('$', '').str.replace(',', '').astype(float)
    
    # --- MÔ PHỎNG DỮ LIỆU NẾU THIẾU ---
    # Vì file CSV gốc của bạn có thể chưa có thông tin Doanh số và Tồn kho, 
    # chúng ta sẽ tạo dữ liệu giả lập (mock data) để công cụ phân tích có thể hoạt động.
    if 'sales_volume' not in df.columns:
        np.random.seed(42) # Giữ cho random ổn định
        df['sales_volume'] = np.random.randint(10, 500, size=len(df))
    if 'stock_level' not in df.columns:
        df['stock_level'] = np.random.randint(0, 100, size=len(df))
    if 'rating' not in df.columns:
        df['rating'] = np.random.uniform(3.0, 5.0, size=len(df))
        
    # Tính toán doanh thu
    df['revenue'] = df['price'] * df['sales_volume']
    
    return df

df = load_data()

# 3. GIAO DIỆN BỘ LỌC (SIDEBAR)
st.sidebar.header("🛠️ Điều Khiển Phân Tích")

# Lọc theo Hãng
brand_list = sorted(df['brand'].dropna().unique()) if 'brand' in df.columns else []
selected_brands = st.sidebar.multiselect("Chọn Thương Hiệu", brand_list, default=brand_list[:5])

# Lọc theo Phân khúc giá
price_segment = st.sidebar.selectbox(
    "Chọn Phân Khúc Giá", 
    ["Tất cả", "Dưới $1000", "$1000 - $2000", "Trên $2000"]
)

# Áp dụng bộ lọc
filtered_df = df.copy()
if selected_brands:
    filtered_df = filtered_df[filtered_df['brand'].isin(selected_brands)]

if price_segment == "Dưới $1000":
    filtered_df = filtered_df[filtered_df['price'] < 1000]
elif price_segment == "$1000 - $2000":
    filtered_df = filtered_df[(filtered_df['price'] >= 1000) & (filtered_df['price'] <= 2000)]
elif price_segment == "Trên $2000":
    filtered_df = filtered_df[filtered_df['price'] > 2000]

# 4. GIAO DIỆN CHÍNH
st.title("📊 Bảng Điều Khiển Chiến Lược Kinh Doanh Laptop")
st.markdown("Phân tích Định giá, Tồn kho và Thị hiếu Khách hàng dựa trên dữ liệu Amazon.")

# --- KHU VỰC KPI ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    total_rev = filtered_df['revenue'].sum()
    st.metric("Tổng Doanh Thu Ước Tính", f"${total_rev:,.0f}")
with col2:
    total_sold = filtered_df['sales_volume'].sum()
    st.metric("Sản Phẩm Đã Bán", f"{total_sold:,} chiếc")
with col3:
    avg_rating = filtered_df['rating'].mean()
    st.metric("Đánh Giá Trung Bình", f"{avg_rating:.1f} ⭐")
with col4:
    low_stock = len(filtered_df[filtered_df['stock_level'] < 15])
    st.metric("⚠️ Sắp Hết Hàng (Tồn < 15)", f"{low_stock} mã SP")

st.markdown("---")

# --- KHU VỰC BIỂU ĐỒ ---
row1_col1, row1_col2 = st.columns([2, 1])

with row1_col1:
    # Góc độ phân tích Động
    analysis_view = st.radio("Góc độ Phân tích:", ["Doanh số theo Hãng (Best Sellers)", "Tình trạng Tồn kho"], horizontal=True)
    
    if analysis_view == "Doanh số theo Hãng (Best Sellers)":
        chart_data = filtered_df.groupby('brand')['sales_volume'].sum().reset_index()
        fig_main = px.bar(chart_data, x='brand', y='sales_volume', color='brand', 
                          title="Tổng Số Lượng Bán Ra Theo Thương Hiệu",
                          labels={'brand': 'Thương hiệu', 'sales_volume': 'Số lượng đã bán'})
    else:
        chart_data = filtered_df.groupby('brand')['stock_level'].mean().reset_index()
        fig_main = px.bar(chart_data, x='brand', y='stock_level', color='stock_level', 
                          color_continuous_scale='RdYlGn',
                          title="Mức Tồn Kho Trung Bình Theo Thương Hiệu (Xanh: An toàn, Đỏ: Cần nhập hàng)",
                          labels={'brand': 'Thương hiệu', 'stock_level': 'Tồn kho TB'})
    
    st.plotly_chart(fig_main, use_container_width=True)

with row1_col2:
    st.subheader("Thị Phần Doanh Thu")
    pie_data = filtered_df.groupby('brand')['revenue'].sum().reset_index()
    fig_pie = px.pie(pie_data, names='brand', values='revenue', hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

# Biểu đồ Chiến lược định giá (Bubble Chart)
st.subheader("Chiến Lược Định Giá & Mức Độ Hài Lòng")
st.markdown("*Kích thước bóng thể hiện Doanh số bán ra*")
fig_scatter = px.scatter(
    filtered_df, 
    x='price', 
    y='rating', 
    size='sales_volume', 
    color='brand',
    hover_name='brand',
    size_max=40,
    title="Tương quan giữa Giá, Đánh giá và Doanh số",
    labels={'price': 'Giá bán ($)', 'rating': 'Điểm đánh giá (1-5)'}
)
# Thêm đường gạch ngang thể hiện rating mục tiêu (ví dụ 4.0)
fig_scatter.add_hline(y=4.0, line_dash="dot", annotation_text="Mục tiêu hài lòng (4.0)", annotation_position="bottom right")
st.plotly_chart(fig_scatter, use_container_width=True)