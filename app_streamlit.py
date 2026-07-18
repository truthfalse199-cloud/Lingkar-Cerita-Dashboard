import streamlit as st
import pandas as pd
import json
import time

st.set_page_config(
    page_title="KawanBaca Dashboard",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── Configuration ──────────────────────────────────────────────────────────
try:
    SHEET_CSV_URL = st.secrets["sheet_csv_url_publik"]
except (KeyError, FileNotFoundError):
    st.error(
        "URL Google Sheets belum diatur. Tambahkan `sheet_csv_url_publik` di "
        "Settings > Secrets (Streamlit Cloud) atau `.streamlit/secrets.toml` lokal."
    )
    st.stop()

# ─── Load & Process Data ────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_dashboard_data():
    try:
        df = pd.read_csv(SHEET_CSV_URL)
    except Exception as exc:
        return None

    # Normalise columns
    df.columns = df.columns.str.strip()
    
    # Detect columns
    col_map = {}
    for col in df.columns:
        lower = col.lower()
        if "nama" in lower or "name" in lower:
            col_map["nama"] = col
        elif "halaman" in lower or "page" in lower or "progress" in lower:
            col_map["halaman"] = col
        elif "skor" in lower or "score" in lower or "empati" in lower:
            col_map["skor"] = col

    timestamp_col = df.columns[0]
    df["_ts"] = pd.to_datetime(df[timestamp_col], dayfirst=True, errors="coerce")

    # Coerce numeric columns
    for key in ("halaman", "skor"):
        real_col = col_map.get(key)
        if real_col and real_col in df.columns:
            df[real_col] = pd.to_numeric(df[real_col], errors="coerce")

    # Compute Metrics
    total_laporan = int(len(df))
    
    halaman_col = col_map.get("halaman")
    total_halaman = int(df[halaman_col].sum()) if halaman_col and halaman_col in df.columns else 0

    nama_col = col_map.get("nama")
    anggota_partisipasi = int(df[nama_col].nunique()) if nama_col and nama_col in df.columns else 0

    skor_col = col_map.get("skor")
    rata_rata_skor = round(float(df[skor_col].mean()), 2) if skor_col and skor_col in df.columns and df[skor_col].notna().any() else 0

    # Weekly charts
    tren_skor_labels = []
    tren_skor_data = []
    tren_laporan_labels = []
    tren_laporan_data = []

    if "_ts" in df.columns and df["_ts"].notna().any():
        df_sorted = df.sort_values("_ts")
        if skor_col and skor_col in df.columns:
            weekly_skor = df_sorted.set_index("_ts")[skor_col].resample("W").mean().dropna()
            tren_skor_labels = [d.strftime("%d %b") for d in weekly_skor.index]
            tren_skor_data = [round(float(v), 2) for v in weekly_skor.values]

        weekly_count = df_sorted.set_index("_ts").resample("W").size()
        weekly_count = weekly_count[weekly_count > 0]
        tren_laporan_labels = [d.strftime("%d %b") for d in weekly_count.index]
        tren_laporan_data = [int(v) for v in weekly_count.values]

    return {
        "metrics": {
            "total_laporan": total_laporan,
            "total_halaman": total_halaman,
            "anggota_partisipasi": anggota_partisipasi,
            "rata_rata_skor": rata_rata_skor,
        },
        "charts": {
            "tren_skor": {"labels": tren_skor_labels, "data": tren_skor_data},
            "tren_laporan": {"labels": tren_laporan_labels, "data": tren_laporan_data},
        }
    }

# ─── Load Frontend Resources ────────────────────────────────────────────────
def read_static_file(filename):
    with open(f"static/{filename}", "r", encoding="utf-8") as f:
        return f.read()

# ─── Render ─────────────────────────────────────────────────────────────────
data = get_dashboard_data()

if data is not None:
    # Ambil file HTML, CSS, JS asli kita
    html_template = read_static_file("index.html")
    css_content = read_static_file("style.css")
    js_content = read_static_file("app.js")
    chartjs_local = read_static_file("chart.umd.min.js")

    # Modifikasi HTML untuk menyematkan CSS & JS secara inline, 
    # dan menyuntikkan data dari Python ke Javascript
    data_json_str = json.dumps(data)
    
    # Ganti pemanggilan eksternal css dan js dengan inline
    html_ready = html_template.replace(
        '<link rel="stylesheet" href="/style.css" />',
        f'<style>{css_content}</style>'
    )
    
    # Ganti CDN Chart.js dengan library lokal
    html_ready = html_ready.replace(
        '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>',
        f'<script>{chartjs_local}</script>'
    )
    
    # Kita suntikkan variabel global `stData` ke JS
    custom_script = f"""
    <script>
      window.stData = {data_json_str};
    </script>
    """
    
    # JS pengganti untuk membaca `window.stData` ketimbang fetch '/api/dashboard-data'
    js_content_modified = js_content.replace(
        "async function loadDashboard() {",
        """async function loadDashboard() {
    overlay.classList.remove("hidden");
    try {
      const json = window.stData;"""
    ).replace(
        "const res  = await fetch(\"/api/dashboard-data\");\n      if (!res.ok) throw new Error(`HTTP ${res.status}`);\n      const json = await res.json();",
        ""
    ).replace(
        'btnRefresh.addEventListener("click", loadDashboard);',
        'btnRefresh.addEventListener("click", () => { window.location.reload(); });' # Refresh mere-load ulang page streamlit
    )

    html_ready = html_ready.replace(
        '<script src="/app.js"></script>',
        f"{custom_script}<script>{js_content_modified}</script>"
    )

    # Embed aplikasi premium ke dalam iframe Streamlit dengan tinggi responsif
    st.components.v1.html(html_ready, height=850, scrolling=True)
else:
    st.warning("⚠️ Gagal memuat data dari Google Sheets. Pastikan URL benar dan sheet sudah dipublikasikan.")
