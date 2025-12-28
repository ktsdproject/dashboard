import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# ⚙️ ส่วนตั้งค่า (แก้ไขตรงนี้ให้ตรงกับ Google Sheet ของคุณ)
# ==========================================

# 1. ลิงก์ CSV จาก Google Sheet (อย่าลืมเครื่องหมายคำพูด)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ75RDJdohY6N12_oX9IVC48zBLT3nU4Ym_VJXaaalYcGY9wlSyyXvBOJCfRkzxvVh8BCgCwbnFZc7G/"

# 2. ตั้งชื่อหัวข้อคอลัมน์ (ให้ตรงกับบรรทัดแรกใน Excel เป๊ะๆ)
COL_NAME = "รายการ"      # ชื่อสินค้า/วัสดุ
COL_CAT = "หมวดหมู่"     # หมวดหมู่ (เช่น เครื่องเขียน, อุปกรณ์)
COL_QTY = "คงเหลือ"      # จำนวนที่มีอยู่ (ต้องเป็นตัวเลข)
COL_PRICE = "ราคาต่อหน่วย" # ราคา (ถ้าไม่มีให้ใส่ None)
COL_STATUS = "สถานะ"     # เช่น พร้อมใช้, ของหมด, ต้องซื้อ

# ==========================================
# 🎨 ตั้งค่าหน้าเว็บและดีไซน์
# ==========================================
st.set_page_config(page_title="Inventory Dashboard", layout="wide", page_icon="📦")

# CSS: เปลี่ยนฟอนต์เป็น Kanit และซ่อนเมนูที่ไม่จำเป็น
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;700&display=swap');
        html, body, [class*="css"]  { font-family: 'Kanit', sans-serif; }
        
        /* ซ่อน Hamburger Menu และ Footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* ปรับแต่ง Metric Card */
        div[data-testid="stMetric"] {
            background-color: #f0f2f6;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 📥 โหลดข้อมูล
# ==========================================
@st.cache_data(ttl=60)
def load_data():
    try:
        data = pd.read_csv(SHEET_URL)
        # แปลงข้อมูลตัวเลขให้แน่ใจว่าเป็นตัวเลขจริงๆ
        if COL_QTY in data.columns:
            data[COL_QTY] = pd.to_numeric(data[COL_QTY], errors='coerce').fillna(0)
        if COL_PRICE and COL_PRICE in data.columns:
            data[COL_PRICE] = pd.to_numeric(data[COL_PRICE], errors='coerce').fillna(0)
        return data
    except Exception as e:
        return None

df = load_data()

# ==========================================
# 🖥️ ส่วนแสดงผลหลัก
# ==========================================

if df is not None:
    # --- Sidebar (เมนูซ้าย) ---
    with st.sidebar:
        st.title("🎛️ ตัวเลือก")
        st.info("กรองข้อมูลที่ต้องการแสดงผล")

        # กรองหมวดหมู่
        if COL_CAT in df.columns:
            all_cats = df[COL_CAT].unique()
            selected_cats = st.multiselect("เลือกหมวดหมู่", all_cats, default=all_cats)
            # Filter Data
            df_filtered = df[df[COL_CAT].isin(selected_cats)]
        else:
            df_filtered = df

        st.write("---")
        st.caption("Updated: Real-time from Google Sheets")

    # --- Header ---
    st.title("📦 ระบบจัดการวัสดุและอุปกรณ์")
    st.markdown(f"**ภาพรวมข้อมูลทั้งหมด:** {len(df)} รายการ")
    st.write("---")

    # --- KPI Metrics (ตัวเลขสรุป) ---
    col1, col2, col3, col4 = st.columns(4)
    
    total_qty = df_filtered[COL_QTY].sum()
    low_stock = df_filtered[df_filtered[COL_QTY] < 5].shape[0] # สมมติน้อยกว่า 5 คือใกล้หมด
    
    col1.metric("📦 จำนวนชิ้นรวม", f"{int(total_qty):,}")
    col2.metric("⚠️ ของใกล้หมด", f"{low_stock} รายการ", delta_color="inverse")
    
    if COL_PRICE and COL_PRICE in df.columns:
        total_value = (df_filtered[COL_QTY] * df_filtered[COL_PRICE]).sum()
        col3.metric("💰 มูลค่ารวมในคลัง", f"{total_value:,.0f} บาท")
    
    col4.metric("📊 หมวดหมู่", f"{df_filtered[COL_CAT].nunique()} หมวด")

    st.write("") # เว้นบรรทัด

    # --- TABS (แบ่งหน้า) ---
    tab1, tab2, tab3 = st.tabs(["📈 Dashboard", "📋 รายการทั้งหมด", "🛒 ต้องซื้อเพิ่ม"])

    # === TAB 1: Dashboard กราฟ ===
    with tab1:
        c1, c2 = st.columns([6, 4])
        
        with c1:
            st.subheader("ระดับสินค้าคงเหลือ (Top 10)")
            # กราฟแท่งแนวนอน
            top_items = df_filtered.sort_values(by=COL_QTY, ascending=False).head(10)
            fig_bar = px.bar(
                top_items, 
                x=COL_QTY, 
                y=COL_NAME, 
                orientation='h', 
                text=COL_QTY,
                color=COL_QTY,
                color_continuous_scale='Blues'
            )
            fig_bar.update_layout(xaxis_title="จำนวน", yaxis_title=None)
            st.plotly_chart(fig_bar, use_container_width=True)

        with c2:
            st.subheader("สัดส่วนหมวดหมู่")
            if COL_CAT in df_filtered.columns:
                cat_count = df_filtered[COL_CAT].value_counts().reset_index()
                cat_count.columns = ['Category', 'Count']
                fig_pie = px.donut(cat_count, values='Count', names='Category', hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)

    # === TAB 2: Table ตารางละเอียด ===
    with tab2:
        st.subheader("📦 สต็อกวัสดุทั้งหมด")
        
        # ตั้งค่า Column Config ให้สวยงาม
        column_cfg = {
            COL_NAME: st.column_config.TextColumn("ชื่อสินค้า", width="medium"),
            COL_QTY: st.column_config.ProgressColumn(
                "คงเหลือ",
                format="%d",
                min_value=0,
                max_value=int(df[COL_QTY].max()), # Max ตามค่าสูงสุดจริง
                help="ปริมาณสินค้าคงเหลือ"
            ),
        }
        
        # เพิ่ม config ราคาถ้ามี
        if COL_PRICE:
            column_cfg[COL_PRICE] = st.column_config.NumberColumn("ราคา/หน่วย", format="฿%d")

        st.dataframe(
            df_filtered,
            column_config=column_cfg,
            use_container_width=True,
            hide_index=True,
            height=500
        )

    # === TAB 3: Restock ของที่ต้องซื้อ ===
    with tab3:
        st.subheader("🛒 รายการที่ต้องดำเนินการ")
        
        # กรองของที่ต้องซื้อ (แก้เงื่อนไขตรงนี้ได้ตามต้องการ)
        # ตัวอย่าง: ถ้ามีคอลัมน์สถานะ ให้หาคำว่า "ซื้อ" หรือ "หมด"
        if COL_STATUS in df.columns:
            # กรองคำที่มีคำว่า "ซื้อ" หรือ "หมด" หรือ "Buy"
            mask = df[COL_STATUS].astype(str).str.contains('ซื้อ|หมด|Buy|Low', case=False, na=False)
            restock_df = df[mask]
        else:
            # ถ้าไม่มีคอลัมน์สถานะ ให้กรองจากจำนวนน้อยกว่า 5
            restock_df = df[df[COL_QTY] < 5]

        if not restock_df.empty:
            st.warning(f"มีรายการต้องจัดการทั้งหมด {len(restock_df)} รายการ")
            
            for index, row in restock_df.iterrows():
                with st.expander(f"🔴 {row[COL_NAME]} (เหลือ {row[COL_QTY]})"):
                    st.write(f"**หมวดหมู่:** {row.get(COL_CAT, '-')}")
                    st.write(f"**สถานะ:** {row.get(COL_STATUS, 'Stock น้อย')}")
                    if COL_PRICE:
                        st.write(f"**ราคาประเมิน:** {row[COL_PRICE]} บาท")
        else:
            st.success("✅ เยี่ยมมาก! ไม่มีสินค้าต้องซื้อเพิ่มในขณะนี้")

else:
    # กรณีโหลดข้อมูลไม่ได้ หรือยังไม่ใส่ Link
    st.error("ไม่สามารถโหลดข้อมูลได้")
    st.warning("👉 กรุณาตรวจสอบลิงก์ Google Sheet CSV ในโค้ดบรรทัดที่ 10")
    st.info("วิธีเอาลิงก์: File > Share > Publish to web > เลือก CSV")