import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Konfigurasi Halaman & Tema Dasar
st.set_page_config(
    page_title="Lingkar Cerita Dashboard",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Sentuhan Kustom CSS (Sidebar, Metrics, & Bagan Grafik dengan Transparansi Pastel)
st.markdown("""
    <style>
    /* Mengubah warna latar belakang utama halaman */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* 🟢 KUSTOMISASI SIDEBAR (KONTROL NAVIGASI) */
    section[data-testid="stSidebar"] {
        background-color: rgba(241, 243, 245, 0.95) !important;
        border-right: 1px solid #dee2e6;
    }
    section[data-testid="stSidebar"] .stSelectbox label {
        color: #495057 !important;
        font-weight: 700 !important;
    }
    /* Kotak pilah di dalam sidebar */
    section[data-testid="stSidebar"] div[data-baseweb="select"] {
        background-color: rgba(74, 144, 226, 0.08) !important;
        border: 1px solid rgba(74, 144, 226, 0.3) !important;
        border-radius: 8px;
    }
    
    /* 🔵 TARGETING KARTU METRICS */
    /* Kartu 1 (Total Laporan) - Biru Pastel */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stMetric"] {
        background-color: rgba(74, 144, 226, 0.12) !important;
        border-left: 5px solid rgba(74, 144, 226, 0.7);
    }
    /* Kartu 2 (Total Halaman) - Hijau Sage */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stMetric"] {
        background-color: rgba(76, 175, 80, 0.12) !important;
        border-left: 5px solid rgba(76, 175, 80, 0.7);
    }
    /* Kartu 3 (Rata-rata Skor Empati) - Ungu Lavender */
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stMetric"] {
        background-color: rgba(155, 89, 182, 0.12) !important;
        border-left: 5px solid rgba(155, 89, 182, 0.7);
    }
    
    /* Base Styling Metrics */
    div[data-testid="stMetric"] {
        border-radius: 12px !important;
        padding: 20px 25px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.01) !important;
        border-top: 1px solid rgba(0,0,0,0.03) !important;
        border-right: 1px solid rgba(0,0,0,0.03) !important;
        border-bottom: 1px solid rgba(0,0,0,0.03) !important;
        transition: transform 0.3s ease, box-shadow 0.3s ease !important;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.06) !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 13px !important;
        color: #495057 !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 26px !important;
        color: #212529 !important;
        font-weight: 800 !important;
    }
    
    /* 🟠 KUSTOMISASI KOTAK LATAR BELAKANG UNTUK SETIAP GRAFIK */
    .element-container:has(iframe) {
        background-color: rgba(255, 255, 255, 0.6) !important;
        padding: 15px !important;
        border-radius: 14px !important;
        border: 1px solid rgba(233, 236, 239, 0.8) !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.01) !important;
    }
    
    hr {
        margin-top: 2rem;
        margin-bottom: 2rem;
        border-color: #e9ecef;
    }
    </style>
    """, unsafe_allow_html=True)

# Title & Deskripsi Awal
st.title("📖 Dashboard Komunitas Lingkar Cerita")
st.markdown("Memonitoring Konsistensi Membaca & Perkembangan Tren Empati Anggota.")
st.markdown("---")

# 3. KONEKSI DATA & CACHING (Efisien agar tidak berat saat reload)
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRefCDk21THyWTZxfyzVeOam0ads4HD2m_GySetpi3uIoSLR7YAITUXjfAQSMXLAAEtXvufxrKuwuBe/pub?gid=1074415517&single=true&output=csv" # Ganti dengan URL CSV Publish to Web kamu

@st.cache_data(ttl=300) # Data disimpan di memori selama 5 menit agar loading instan
def load_data():
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        df.columns = ['Timestamp', 'Nama', 'Judul Buku', 'Halaman', 'Refleksi', 'Skor Empati', 'Feedback AI']
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df['Skor Empati'] = pd.to_numeric(df['Skor Empati'], errors='coerce')
        df['Halaman'] = pd.to_numeric(df['Halaman'], errors='coerce')
        return df
    except Exception as e:
        return None

df = load_data()

if df is not None:
    # --- SIDEBAR INTERAKTIF (Filter Kontrol) ---
    st.sidebar.header("🎯 Kontrol Navigasi")
    st.sidebar.markdown("Gunakan filter di bawah ini untuk melihat metrik personal atau kelompok.")
    
    # Filter Nama Anggota
    list_nama = ["Semua Anggota"] + list(df['Nama'].unique())
    pilihan_nama = st.sidebar.selectbox("Pilih Anggota:", list_nama)
    
    # Filter Data berdasarkan Pilihan
    if pilihan_nama == "Semua Anggota":
        df_filtered = df
    else:
        df_filtered = df[df['Nama'] == pilihan_nama]

    # --- ROW 1: MODERN METRICS CARDS (Dengan Efek Hover CSS) ---
    c1, c2, c3 = st.columns(3)
    
    total_laporan = len(df_filtered)
    total_halaman = int(df_filtered['Halaman'].sum()) if not df_filtered['Halaman'].isna().all() else 0
    rata_empati = df_filtered['Skor Empati'].mean()
    rata_empati_text = f"{rata_empati:.1f}/100" if not pd.isna(rata_empati) else "0.0"
    
    c1.metric(label="📚 TOTAL LAPORAN", value=f"{total_laporan} Data")
    c2.metric(label="🔥 TOTAL HALAMAN DIBACA", value=f"{total_halaman} Hlm")
    c3.metric(label="🧠 RATA-RATA SKOR EMPATI", value=rata_empati_text)

    st.markdown("---")

    # --- ROW 2: GRAFIK INTERAKTIF (Berdasar JavaScript Plotly - Ringan & Responsif) ---
    col_grafik1, col_grafik2 = st.columns([1, 1.5])

    with col_grafik1:
        st.subheader("📊 Distribusi Kontribusi")
        # Donut Chart untuk melihat persentasi keaktifan
        fig_pie = px.pie(
            df_filtered, 
            names='Nama', 
            hole=0.5,
            template="plotly_white",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        # Mengatur posisi legenda agar rapi
        fig_pie.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_grafik2:
        st.subheader("📈 Rata-rata Skor Empati per Anggota")
        
        # Menghitung rata-rata skor empati untuk setiap nama anggota
        df_avg_empati = df_filtered.groupby('Nama')['Skor Empati'].mean().reset_index()
        df_avg_empati = df_avg_empati.dropna().sort_values('Skor Empati', ascending=True)
        
        if not df_avg_empati.empty:
            # Membuat Bar Chart Horizontal yang sederhana dan rapi
            fig_trend = px.bar(
                df_avg_empati, 
                x='Skor Empati', 
                y='Nama', 
                orientation='h', # Grafik horizontal agar nama tidak terpotong
                text='Skor Empati', # Menampilkan angka skor langsung di atas batang
                template="plotly_white",
                color='Skor Empati', # Memberikan gradasi warna berdasarkan skor
                color_continuous_scale=px.colors.sequential.Purples # Palet ungu senada dengan kartu skor
            )
            
            # Merapikan tampilan teks skor (dibulatkan 1 angka di belakang koma)
            fig_trend.update_traces(
                texttemplate='%{text:.1f}', 
                textposition='inside',
                hovertemplate="<b>% {y}</b><br>Rata-rata Skor: % {x:.1f}"
            )
            
            # Menghilangkan bar skala warna di sebelah kanan agar grafik lebih bersih
            fig_trend.update_layout(coloraxis_showscale=False, xaxis_title="Skor Empati (1-100)", yaxis_title="")
            
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Belum ada data skor empati untuk visualisasi tren.")



    # --- ROW 3: TABEL DATA INTERAKTIF ---
    st.markdown("---")
    st.subheader("📄 Catatan Refleksi & Feedback AI Terbaru")
    
    # Menampilkan tabel interaktif bawaan Streamlit yang bisa di-sort, filter, dan di-search oleh user
    tabel_tampil = df_filtered[['Timestamp', 'Nama', 'Judul Buku', 'Halaman', 'Skor Empati', 'Feedback AI']].sort_values('Timestamp', ascending=False)
    
    st.dataframe(
        tabel_tampil,
        use_container_width=True,
        hide_index=True
    )

else:
    st.warning("⚠️ Koneksi data gagal. Periksa kembali URL CSV Google Sheets pada kode script.")
