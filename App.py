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
    .stApp {
        background-color: #f8f9fa;
    }
    section[data-testid="stSidebar"] {
        background-color: rgba(241, 243, 245, 0.95) !important;
        border-right: 1px solid #dee2e6;
    }
    section[data-testid="stSidebar"] .stSelectbox label {
        color: #495057 !important;
        font-weight: 700 !important;
    }
    section[data-testid="stSidebar"] div[data-baseweb="select"] {
        background-color: rgba(74, 144, 226, 0.08) !important;
        border: 1px solid rgba(74, 144, 226, 0.3) !important;
        border-radius: 8px;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stMetric"] {
        background-color: rgba(74, 144, 226, 0.12) !important;
        border-left: 5px solid rgba(74, 144, 226, 0.7);
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stMetric"] {
        background-color: rgba(76, 175, 80, 0.12) !important;
        border-left: 5px solid rgba(76, 175, 80, 0.7);
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stMetric"] {
        background-color: rgba(155, 89, 182, 0.12) !important;
        border-left: 5px solid rgba(155, 89, 182, 0.7);
    }
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

st.title("📖 Dashboard Komunitas Lingkar Cerita")
st.markdown("Memonitoring Konsistensi Membaca & Perkembangan Tren Empati Anggota.")
st.markdown("---")

# 3. KONEKSI DATA & CACHING
# PENTING (privasi): URL ini HARUS menunjuk ke tab "Publik" yang TIDAK berisi
# kolom Nomor WhatsApp — bukan tab mentah hasil Google Form. Nomor WA anggota
# cukup dipakai oleh bot.js untuk reminder personal, tidak untuk dashboard publik.
#
# URL diambil dari st.secrets (Settings > Secrets di Streamlit Cloud), bukan
# ditulis langsung di kode, supaya aman kalau kode ini di-share/upload ke GitHub.
try:
    SHEET_CSV_URL = st.secrets["sheet_csv_url_publik"]
except (KeyError, FileNotFoundError):
    st.error(
        "URL Google Sheets belum diatur. Tambahkan `sheet_csv_url_publik` di "
        "Settings > Secrets (Streamlit Cloud) atau file `.streamlit/secrets.toml` "
        "saat menjalankan secara lokal."
    )
    st.stop()

KOLOM_DIHARAPKAN = ['Timestamp', 'Nama', 'Judul Buku', 'Halaman', 'Refleksi', 'Skor Empati', 'Feedback AI']


@st.cache_data(ttl=300)  # Data disimpan di memori selama 5 menit agar loading instan
def load_data():
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        if len(df.columns) != len(KOLOM_DIHARAPKAN):
            st.warning(
                f"Jumlah kolom di sheet ({len(df.columns)}) tidak sesuai dugaan "
                f"({len(KOLOM_DIHARAPKAN)}). Pastikan tab 'Publik' hanya berisi "
                f"kolom: {', '.join(KOLOM_DIHARAPKAN)} — tanpa kolom Nomor WhatsApp."
            )
            return None
        df.columns = KOLOM_DIHARAPKAN
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
        df['Skor Empati'] = pd.to_numeric(df['Skor Empati'], errors='coerce')
        df['Halaman'] = pd.to_numeric(df['Halaman'], errors='coerce')
        return df
    except Exception:
        return None


df = load_data()

if df is not None:
    st.sidebar.header("🎯 Kontrol Navigasi")
    st.sidebar.markdown("Gunakan filter di bawah ini untuk melihat metrik personal atau kelompok.")

    list_nama = ["Semua Anggota"] + sorted(df['Nama'].dropna().unique().tolist())
    pilihan_nama = st.sidebar.selectbox("Pilih Anggota:", list_nama)

    df_filtered = df if pilihan_nama == "Semua Anggota" else df[df['Nama'] == pilihan_nama]

    # --- ROW 1: METRICS CARDS ---
    c1, c2, c3 = st.columns(3)

    total_laporan = len(df_filtered)
    total_halaman = int(df_filtered['Halaman'].sum()) if not df_filtered['Halaman'].isna().all() else 0
    rata_empati = df_filtered['Skor Empati'].mean()
    rata_empati_text = f"{rata_empati:.1f}/100" if pd.notna(rata_empati) else "Belum ada data"

    c1.metric(label="📚 TOTAL LAPORAN", value=f"{total_laporan} Data")
    c2.metric(label="🔥 TOTAL HALAMAN DIBACA", value=f"{total_halaman} Hlm")
    c3.metric(label="🧠 RATA-RATA SKOR EMPATI", value=rata_empati_text)

    st.markdown("---")

    # --- ROW 2: GRAFIK ---
    col_grafik1, col_grafik2 = st.columns([1, 1.5])

    with col_grafik1:
        st.subheader("📊 Distribusi Kontribusi")
        if not df_filtered.empty:
            fig_pie = px.pie(
                df_filtered,
                names='Nama',
                hole=0.5,
                template="plotly_white",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.1))
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Belum ada data untuk ditampilkan.")

    with col_grafik2:
        st.subheader("📈 Rata-rata Skor Empati per Anggota")

        df_avg_empati = df_filtered.groupby('Nama')['Skor Empati'].mean().reset_index()
        df_avg_empati = df_avg_empati.dropna().sort_values('Skor Empati', ascending=True)

        if not df_avg_empati.empty:
            fig_trend = px.bar(
                df_avg_empati,
                x='Skor Empati',
                y='Nama',
                orientation='h',
                text='Skor Empati',
                template="plotly_white",
                color='Skor Empati',
                color_continuous_scale=px.colors.sequential.Purples
            )
            fig_trend.update_traces(
                texttemplate='%{text:.1f}',
                textposition='inside',
                # PERBAIKAN: tanpa spasi setelah "%" — format Plotly harus %{x}, bukan % {x}
                hovertemplate="<b>%{y}</b><br>Rata-rata Skor: %{x:.1f}<extra></extra>"
            )
            fig_trend.update_layout(coloraxis_showscale=False, xaxis_title="Skor Empati (1-100)", yaxis_title="")
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Belum ada data skor empati untuk visualisasi tren.")

    # --- ROW 3: TABEL DATA ---
    st.markdown("---")
    st.subheader("📄 Catatan Refleksi & Feedback AI Terbaru")

    tabel_tampil = df_filtered[['Timestamp', 'Nama', 'Judul Buku', 'Halaman', 'Skor Empati', 'Feedback AI']].sort_values('Timestamp', ascending=False)

    st.dataframe(
        tabel_tampil,
        use_container_width=True,
        hide_index=True
    )

else:
    st.warning("⚠️ Koneksi data gagal. Periksa kembali URL CSV Google Sheets di Secrets.")
