"""
KawanBaca Dashboard – Flask Backend
=========================================
Fetches reading-log data from a public Google Sheet (CSV export),
processes it with Pandas, and serves it as JSON to the frontend.
"""

import time
from flask import Flask, jsonify, send_from_directory
import pandas as pd
from config import SHEET_CSV_URL, DEBUG, PORT, CACHE_TIMEOUT

# ---------------------------------------------------------------------------
# Flask App
# ---------------------------------------------------------------------------
app = Flask(__name__, static_folder="static", static_url_path="")

# ---------------------------------------------------------------------------
# Simple In-Memory Cache
# ---------------------------------------------------------------------------
_cache = {"df": None, "col_map": None, "ts": 0}


def _detect_columns(df):
    """Map logical column roles to actual column names by keyword search."""
    col_map = {}
    for col in df.columns:
        lower = col.strip().lower()
        if "nama" in lower or "name" in lower:
            col_map["nama"] = col
        elif "halaman" in lower or "page" in lower or "progress" in lower:
            col_map["halaman"] = col
        elif "skor" in lower or "score" in lower:
            col_map["skor"] = col
    return col_map


def _fetch_dataframe():
    """Download the Google Sheet CSV and return (DataFrame, col_map)."""
    now = time.time()
    if _cache["df"] is not None and (now - _cache["ts"]) < CACHE_TIMEOUT:
        return _cache["df"], _cache["col_map"]

    try:
        df = pd.read_csv(SHEET_CSV_URL)
    except Exception as exc:
        app.logger.error("Failed to fetch Google Sheet: %s", exc)
        if _cache["df"] is not None:
            return _cache["df"], _cache["col_map"]
        return pd.DataFrame(), {}

    # ── Normalise column names (strip whitespace) ──────────────────────
    df.columns = df.columns.str.strip()

    # ── Detect columns BEFORE any type coercion ───────────────────────
    col_map = _detect_columns(df)

    # ── Parse the timestamp column (first column) ─────────────────────
    timestamp_col = df.columns[0]
    df["_ts"] = pd.to_datetime(df[timestamp_col], dayfirst=True, errors="coerce")

    # ── Coerce only the numeric columns we need ───────────────────────
    for key in ("halaman", "skor"):
        real_col = col_map.get(key)
        if real_col and real_col in df.columns:
            df[real_col] = pd.to_numeric(df[real_col], errors="coerce")

    _cache["df"] = df
    _cache["col_map"] = col_map
    _cache["ts"] = now
    return df, col_map


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Serve the main dashboard page."""
    return send_from_directory("static", "index.html")


@app.route("/api/dashboard-data")
def dashboard_data():
    """Return all dashboard metrics and chart series as JSON."""
    df, col_map = _fetch_dataframe()

    if df.empty:
        return jsonify({
            "metrics": {
                "total_laporan": 0,
                "total_halaman": 0,
                "anggota_partisipasi": 0,
                "rata_rata_skor": 0,
            },
            "charts": {
                "tren_skor": {"labels": [], "data": []},
                "tren_laporan": {"labels": [], "data": []},
            },
        })

    # ── Metrics ────────────────────────────────────────────────────────
    total_laporan = int(len(df))

    halaman_col = col_map.get("halaman")
    total_halaman = int(df[halaman_col].sum()) if halaman_col and halaman_col in df.columns else 0

    nama_col = col_map.get("nama")
    anggota_partisipasi = int(df[nama_col].nunique()) if nama_col and nama_col in df.columns else 0

    skor_col = col_map.get("skor")
    if skor_col and skor_col in df.columns and df[skor_col].notna().any():
        rata_rata_skor = round(float(df[skor_col].mean()), 2)
    else:
        rata_rata_skor = 0

    # ── Weekly trends ──────────────────────────────────────────────────
    tren_skor_labels = []
    tren_skor_data = []
    tren_laporan_labels = []
    tren_laporan_data = []

    if "_ts" in df.columns and df["_ts"].notna().any():
        df_sorted = df.sort_values("_ts")

        # Weekly average empathy score
        if skor_col and skor_col in df.columns:
            weekly_skor = (
                df_sorted.set_index("_ts")[skor_col]
                .resample("W").mean().dropna()
            )
            tren_skor_labels = [d.strftime("%d %b") for d in weekly_skor.index]
            tren_skor_data = [round(float(v), 2) for v in weekly_skor.values]

        # Weekly report count
        weekly_count = df_sorted.set_index("_ts").resample("W").size()
        weekly_count = weekly_count[weekly_count > 0]
        tren_laporan_labels = [d.strftime("%d %b") for d in weekly_count.index]
        tren_laporan_data = [int(v) for v in weekly_count.values]

    # ── Response ───────────────────────────────────────────────────────
    payload = {
        "metrics": {
            "total_laporan": total_laporan,
            "total_halaman": total_halaman,
            "anggota_partisipasi": anggota_partisipasi,
            "rata_rata_skor": rata_rata_skor,
        },
        "charts": {
            "tren_skor": {"labels": tren_skor_labels, "data": tren_skor_data},
            "tren_laporan": {"labels": tren_laporan_labels, "data": tren_laporan_data},
        },
    }
    return jsonify(payload)


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"  * KawanBaca Dashboard running at http://localhost:{PORT}")
    app.run(debug=DEBUG, port=PORT)
