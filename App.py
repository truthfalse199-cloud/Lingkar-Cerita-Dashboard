import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Lingkar Cerita Dashboard",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

.stApp {
        background: linear-gradient(135deg, #eef2fb 0%, #f3eefc 45%, #fdf1f5 100%);
}
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stMetric"] {
        background-color: rgba(74, 144, 226, 0.14) !important;
        border-left: 5px solid rgba(74, 144, 226, 0.8);
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stMetric"] {
        background-color: rgba(220, 100, 60, 0.14) !important;
        border-left: 5px solid rgba(220, 100, 60, 0.8);
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stMetric"] {
        background-color: rgba(76, 175, 80, 0.14) !important;
        border-left: 5px solid rgba(76, 175, 80, 0.8);
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(4) div[data-testid="stMetric"] {
        background-color: rgba(155, 89, 182, 0.14) !important;
        border-left: 5px solid rgba(155, 89, 182, 0.8);
    }
    div[data-testid="stMetric"] {
        border-radius: 12px !important;
        padding: 20px 25px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.03) !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 13px !important;
        color: #495057 !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 26px !important;
        color: #212529 !important;
        font-weight: 800 !important;
    }
    .element-container:has(iframe) {
        background-color: rgba(255, 255, 255, 0.75) !important;
        padding: 15px !important;
        border-radius: 14px !important;
        border: 1px solid rgba(233, 236, 239, 0.8) !important;
    }
    hr { margin-top: 2rem; margin-bottom: 2rem; border-color: #e9ecef; }
    </style>
    """, unsafe_allow_html=True)

st.title("📖 Dashboard Komunitas Lingkar Cerita")
st.markdown("Ringkasan aktivitas & keterlibatan membaca komunitas secara agregat.")
st.markdown("---")

try:
    SHEET_CSV_URL = st.secrets["sheet_csv_url_publik"]
except (KeyError, FileNotFoundError):
    st.error(
        "URL Google Sheets belum diatur. Tambahkan `sheet_csv_url_publik` di "
        "Settings > Secrets (Streamlit Cloud) atau `.streamlit/secrets.toml` lokal."
    )
    st.stop()

KOLOM_DIHARAPKAN = [
    'Timestamp', 'Nama Anggota', 'Judul Buku & Penulis',
    'Progress Membaca (Halaman Terakhir)', 'Refleksi atau Afeksi setelah membaca',
    'Skor Empati AI', 'Analisis & Feedback AI'
]


@st.cache_data(ttl=300)
def load_data():
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        if len(df.columns) != len(KOLOM_DIHARAPKAN):
            st.warning(
                f"Jumlah kolom di sheet ({len(df.columns)}) tidak sesuai dugaan "
                f"({len(KOLOM_DIHARAPKAN)}). Cek lagi tab 'Publik' di Sheets."
            )
            return None
        df.columns = KOLOM_DIHARAPKAN
        # PENTING: format tanggal di sheet adalah locale Indonesia (tanggal duluan,
        # DD/MM/YYYY) — dayfirst=True wajib, kalau tidak bulan & tanggal akan tertukar
        # (bug yang sama seperti yang pernah kita perbaiki di bot.js)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], dayfirst=True, errors='coerce')
        df['Skor Empati AI'] = pd.to_numeric(df['Skor Empati AI'], errors='coerce')
        df['Progress Membaca (Halaman Terakhir)'] = pd.to_numeric(df['Progress Membaca (Halaman Terakhir)'], errors='coerce')
        return df
    except Exception:
        return None


df = load_data()

if df is not None and not df.empty:
    total_laporan = len(df)
    total_halaman = int(df['Progress Membaca (Halaman Terakhir)'].sum(skipna=True)) if df['Progress Membaca (Halaman Terakhir)'].notna().any() else 0
    jumlah_anggota = df['Nama Anggota'].nunique()
    rata_skor = df['Skor Empati AI'].mean()
    rata_skor_text = f"{rata_skor:.1f}/100" if pd.notna(rata_skor) else "Belum ada data"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📚 Total Laporan", f"{total_laporan}")
    c2.metric("🔥 Total Halaman Komunitas", f"{total_halaman} hlm")
    c3.metric("👥 Anggota Berpartisipasi", f"{jumlah_anggota} orang")
    c4.metric("🧠 Rata-rata Skor Keterlibatan", rata_skor_text)

    st.markdown("---")

    df_valid = df.dropna(subset=['Timestamp']).copy()

    if not df_valid.empty:
        df_valid['MingguPeriod'] = df_valid['Timestamp'].dt.to_period('W')
        df_valid['Minggu'] = df_valid['MingguPeriod'].apply(lambda p: p.start_time.strftime('%d %b'))

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 Tren skor keterlibatan komunitas")
            tren_skor = (
                df_valid.groupby(['MingguPeriod', 'Minggu'])['Skor Empati AI']
                .mean().reset_index().sort_values('MingguPeriod')
            )
            if tren_skor['Skor Empati AI'].notna().any():
                fig1 = px.line(tren_skor, x='Minggu', y='Skor Empati AI', markers=True, template="plotly_white")
                fig1.update_layout(yaxis_title="Skor rata-rata (1-100)", xaxis_title="")
                fig1.update_traces(line_color='#7F77DD', marker_color='#7F77DD')
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("Belum cukup data untuk tren skor.")

        with col2:
            st.subheader("📊 Jumlah laporan per minggu")
            tren_laporan = (
                df_valid.groupby(['MingguPeriod', 'Minggu']).size()
                .reset_index(name='Jumlah Laporan').sort_values('MingguPeriod')
            )
            fig2 = px.bar(tren_laporan, x='Minggu', y='Jumlah Laporan', template="plotly_white",
                          color_discrete_sequence=['#1D9E75'])
            fig2.update_layout(xaxis_title="", yaxis_title="Jumlah laporan")
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Belum ada data dengan tanggal valid untuk ditampilkan sebagai tren.")

    st.markdown("---")
    st.caption(
        "Data ditampilkan secara agregat untuk menjaga privasi anggota — "
        "detail refleksi, judul buku, dan progres personal tidak ditampilkan publik."
    )

else:
    st.warning("⚠️ Data belum tersedia atau koneksi ke Google Sheets gagal.")
