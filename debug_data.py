"""
Debug script – test Google Sheet access & column detection
"""
import os
import sys

# Try loading .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[WARN] python-dotenv not installed, reading env vars directly.")

from config import SHEET_CSV_URL

print("=" * 60)
print("DEBUG: Lingkar Cerita Dashboard – Data Check")
print("=" * 60)

# 1. Check URL
print(f"\n[1] SHEET_CSV_URL = {SHEET_CSV_URL}")
if "YOUR_SHEET_ID" in SHEET_CSV_URL:
    print("    ❌ URL masih berisi placeholder 'YOUR_SHEET_ID'!")
    print("    → Buat file .env dan isi SHEET_CSV_URL dengan URL CSV asli.")
    sys.exit(1)
else:
    print("    ✅ URL sudah dikonfigurasi.")

# 2. Try fetching
import pandas as pd

print("\n[2] Mengambil data dari Google Sheet...")
try:
    df = pd.read_csv(SHEET_CSV_URL)
    print(f"    ✅ Berhasil! Jumlah baris: {len(df)}, Jumlah kolom: {len(df.columns)}")
except Exception as e:
    print(f"    ❌ GAGAL mengambil data: {e}")
    print("    → Pastikan Sheet sudah di-publish: File > Share > Publish to web > CSV")
    sys.exit(1)

# 3. Show columns
print(f"\n[3] Nama kolom yang ditemukan:")
for i, col in enumerate(df.columns):
    print(f"    [{i}] '{col}'")

# 4. Check column detection (same logic as app.py)
print("\n[4] Deteksi kolom otomatis:")
col_map = {}
for col in df.columns:
    lower = col.strip().lower()
    if "nama" in lower or "name" in lower:
        col_map["nama"] = col
    elif "halaman" in lower or "page" in lower:
        col_map["halaman"] = col
    elif "skor" in lower or "score" in lower or "empati" in lower:
        col_map["skor"] = col

if col_map.get("nama"):
    print(f"    ✅ Kolom Nama     → '{col_map['nama']}'")
else:
    print("    ❌ Kolom Nama TIDAK DITEMUKAN (cari keyword: 'nama', 'name')")

if col_map.get("halaman"):
    print(f"    ✅ Kolom Halaman  → '{col_map['halaman']}'")
else:
    print("    ❌ Kolom Halaman TIDAK DITEMUKAN (cari keyword: 'halaman', 'page')")

if col_map.get("skor"):
    print(f"    ✅ Kolom Skor     → '{col_map['skor']}'")
else:
    print("    ❌ Kolom Skor TIDAK DITEMUKAN (cari keyword: 'skor', 'score', 'empati')")

# 5. Check timestamp
print(f"\n[5] Parsing timestamp dari kolom pertama: '{df.columns[0]}'")
ts = pd.to_datetime(df[df.columns[0]], dayfirst=True, errors="coerce")
valid = ts.notna().sum()
print(f"    Timestamp valid: {valid} / {len(ts)}")
if valid == 0:
    print("    ❌ Tidak ada timestamp valid! Periksa format tanggal di kolom pertama.")
else:
    print(f"    ✅ Contoh: {ts.dropna().iloc[0]}")

# 6. Show first 5 rows
print(f"\n[6] 5 baris pertama:")
print(df.head().to_string(index=False))

print("\n" + "=" * 60)
print("Selesai. Jika ada ❌, perbaiki masalah tersebut lalu jalankan ulang.")
print("=" * 60)
