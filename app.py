import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Hệ Thống Phân Tích Doanh Số Amazon", page_icon="💻", layout="wide")

# --- 2. POWER QUERY MÔ PHỎNG (ETL) ---
@st.cache_data
def load_and_transform_data():
    try:
        df = pd.read_csv("amazon_laptop_prices_cleaned.csv")
        # Chuẩn hóa tên cột
        df.columns = df.columns.str.strip().str.lower()
        
        # Làm sạch cột Giá
        if 'price' in df.columns and df['price'].dtype == 'O':
            df['price'] = df['price'].astype(str).str.replace(r'[\$,]', '', regex=True).astype(float)
        
        # Khởi tạo dữ liệu mô phỏng cho các cột có thể thiếu trong CSV thô để demo tính năng
        np.random.seed(10)
        if 'sales_volume' not in df.columns:
            df['sales_volume'] = np.random.randint(10, 1000, size=len(df))
        if 'stock_level' not in df.columns:
            df['stock_level'] = np.random.randint(0, 200, size=len(df))
        if 'rating' not in df.columns:
            df['rating'] = np.random.uniform(3.5, 5.0, size=len(df))
        if 'reviews' not in df.columns:
            df['reviews'] = np.random.randint(5, 5000, size=len(df))
            
        df['revenue'] = df['price'] * df['sales_volume']
        return df
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu: {e}")
        return pd.DataFrame()

df = load_and_transform_data()

if not df.empty:
    # --- 3. GIAO DIỆN LỌC ĐỘNG (BÊN TRÁI) ---
    st.sidebar.title("🔍 Bộ Lọc Dữ Liệu")
    brand_list = sorted(df['brand'].dropna().unique())
    selected_brands = st.sidebar.multiselect("Chọn Thương Hiệu:", brand_list, default=brand_list[:6])
    
    price_range = st.sidebar.slider("Khoảng Giá ($):", min_value=0, max_value=int(df['price'].max()), value=(0, 3000))

    # Áp dụng bộ lọc thời gian thực
    mask = (df['brand'].isin(selected_brands)) & (df['price'] >= price_range[0]) & (df['price'] <= price_range[1])
    filtered_df = df[mask]

    # --- 4. GIAO DIỆN CHÍNH & CHIA TAB PHÂN TÍCH ---
    st.title("Phân Tích Doanh Số Bán Hàng Laptop")
    
    # Tạo 3 Tabs tương ứng với 3 mục tiêu kinh doanh
    tab1, tab2, tab3 = st.tabs(["📊 Hiệu Suất & Bán Chạy", "💰 Định Giá & Khách Hàng", "📦 Quản Lý Tồn Kho"])

    # === TAB 1: HIỆU SUẤT ===
    with tab1:
        st.markdown("### Theo dõi hiệu suất thời gian thực & Xác định sản phẩm bán chạy")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tổng Doanh Thu", f"${filtered_df['revenue'].sum():,.0f}")
        col2.metric("Sản Phẩm Đã Bán", f"{filtered_df['sales_volume'].sum():,} máy")
        col3.metric("Điểm Đánh Giá TB", f"{filtered_df['rating'].mean():.2f} ⭐")
        col4.metric("Lượt Tương Tác (Reviews)", f"{filtered_df['reviews'].sum():,}")

        c1, c2 = st.columns([2, 1])
        with c1:
            # Biểu đồ Doanh thu theo Hãng
            sales_by_brand = filtered_df.groupby('brand')['revenue'].sum().reset_index().sort_values('revenue', ascending=False)
            fig_sales = px.bar(sales_by_brand, x='brand', y='revenue', color='brand', title="Doanh Thu Theo Thương Hiệu")
            st.plotly_chart(fig_sales, use_container_width=True)
        with c2:
            # Thị phần
            fig_pie = px.pie(filtered_df, names='brand', values='sales_volume', title="Thị Phần Sản Lượng", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

    # === TAB 2: ĐỊNH GIÁ & KHÁCH HÀNG ===
    with tab2:
        st.markdown("### Tối ưu hóa chiến lược định giá & Hiểu rõ sở thích khách hàng")
        # Phân tích Giá: Thấp nhất, Trung bình, Cao nhất (Giống hệt hình Power BI)
        price_stats = filtered_df.groupby('brand')['price'].agg(['min', 'mean', 'max']).reset_index()
        fig_price = go.Figure()
        fig_price.add_trace(go.Bar(x=price_stats['brand'], y=price_stats['max'], name='Giá Cao Nhất', marker_color='indianred'))
        fig_price.add_trace(go.Bar(x=price_stats['brand'], y=price_stats['mean'], name='Giá Trung Bình', marker_color='lightsalmon'))
        fig_price.add_trace(go.Bar(x=price_stats['brand'], y=price_stats['min'], name='Giá Thấp Nhất', marker_color='lightblue'))
        fig_price.update_layout(title="Khảo Sát Các Phân Khúc Giá Theo Thương Hiệu", barmode='group')
        st.plotly_chart(fig_price, use_container_width=True)

        # Mối quan hệ giữa Giá và Đánh giá khách hàng
        fig_scatter = px.scatter(filtered_df, x='price', y='rating', size='reviews', color='brand',
                                 title="Tương quan: Mức Giá - Điểm Đánh Giá - Lượt Phản Hồi (Kích thước bóng)",
                                 labels={'price': 'Giá ($)', 'rating': 'Đánh giá (1-5)'}, hover_data=['title'] if 'title' in df.columns else [])
        fig_scatter.add_hline(y=4.0, line_dash="dash", annotation_text="Khách hàng hài lòng (>4.0)")
        st.plotly_chart(fig_scatter, use_container_width=True)

    # === TAB 3: QUẢN LÝ TỒN KHO ===
    with tab3:
        st.markdown("### Lập kế hoạch mức tồn kho chính xác, giảm tình trạng thiếu hụt")
        # Danh sách cần nhập gấp
        critical_stock = filtered_df[filtered_df['stock_level'] < 20]
        if not critical_stock.empty:
            st.warning(f"⚠️ Cảnh báo: Có {len(critical_stock)} dòng sản phẩm sắp hết hàng.")
        else:
            st.success("✅ Tình trạng tồn kho hiện tại đang ổn định.")

        # So sánh giữa Nhu cầu (Doanh số) và Khả năng cung ứng (Tồn kho)
        inv_data = filtered_df.groupby('brand')[['sales_volume', 'stock_level']].sum().reset_index()
        fig_inv = go.Figure()
        fig_inv.add_trace(go.Bar(x=inv_data['brand'], y=inv_data['sales_volume'], name='Tổng Nhu Cầu (Đã Bán)', marker_color='royalblue'))
        fig_inv.add_trace(go.Bar(x=inv_data['brand'], y=inv_data['stock_level'], name='Khả Năng Cung Cấp (Tồn Kho Hiện Tại)', marker_color='lightgray'))
        fig_inv.update_layout(title="Phân Tích Cung Cầu: Doanh Số vs Tồn Kho", barmode='group')
        st.plotly_chart(fig_inv, use_container_width=True)

