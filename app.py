from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
import re
from datetime import datetime
import io
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ganti-secret-key-ini-sebelum-deploy")

DB_NAME = "/tmp/attendance.db"

# Ganti password admin default ini sebelum deploy (atau set env var ADMIN_PASSWORD)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

KELAS_LABEL = "Pendidikan Akuntansi 2026 - Kelas C"

GMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@gmail\.com$", re.IGNORECASE)
NIM_REGEX = re.compile(r"^\d{10}$")


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS absensi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gmail TEXT NOT NULL,
            nama TEXT NOT NULL,
            nim TEXT NOT NULL,
            tanggal TEXT NOT NULL,
            jam TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Hadir'
        )
        """
    )
    conn.commit()
    conn.close()


@app.route("/")
def index():
    return render_template("index.html", kelas_label=KELAS_LABEL)


@app.route("/submit", methods=["POST"])
def submit():
    gmail = request.form.get("gmail", "").strip().lower()
    nama = request.form.get("nama", "").strip()
    nim = request.form.get("nim", "").strip()

    errors = []
    if not gmail or not GMAIL_REGEX.match(gmail):
        errors.append("Gmail tidak valid. Gunakan format namaanda@gmail.com")
    if not nama:
        errors.append("Nama wajib diisi")
    if not nim or not NIM_REGEX.match(nim):
        errors.append("NIM harus tepat 10 digit angka (tanpa huruf/spasi)")

    old = {"gmail": gmail, "nama": nama, "nim": nim}

    if errors:
        return render_template("index.html", kelas_label=KELAS_LABEL, errors=errors, old=old)

    now = datetime.now()
    tanggal = now.strftime("%Y-%m-%d")
    jam = now.strftime("%H:%M:%S")

    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM absensi WHERE (nim = ? OR gmail = ?) AND tanggal = ?",
        (nim, gmail, tanggal),
    ).fetchone()

    if existing:
        conn.close()
        errors.append(
            f"Anda (NIM {existing['nim']}) sudah tercatat absen hari ini pukul {existing['jam']}. "
            "Tidak bisa absen dua kali dalam satu hari."
        )
        return render_template("index.html", kelas_label=KELAS_LABEL, errors=errors, old=old)

    conn.execute(
        "INSERT INTO absensi (gmail, nama, nim, tanggal, jam, status) VALUES (?, ?, ?, ?, ?, ?)",
        (gmail, nama, nim, tanggal, jam, "Hadir"),
    )
    conn.commit()
    conn.close()

    return render_template(
        "index.html", kelas_label=KELAS_LABEL, success=True, nama=nama, jam=jam, tanggal=tanggal
    )


@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        return render_template("admin_login.html", error="Password salah, coba lagi.")
    return render_template("admin_login.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    tanggal = request.args.get("tanggal", datetime.now().strftime("%Y-%m-%d"))

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM absensi WHERE tanggal = ? ORDER BY jam ASC", (tanggal,)
    ).fetchall()
    conn.close()

    return render_template(
        "admin.html",
        kelas_label=KELAS_LABEL,
        rows=rows,
        tanggal=tanggal,
        total=len(rows),
    )


@app.route("/admin/export")
def admin_export():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    tanggal = request.args.get("tanggal", datetime.now().strftime("%Y-%m-%d"))

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM absensi WHERE tanggal = ? ORDER BY jam ASC", (tanggal,)
    ).fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Rekap Absensi"

    # Judul di baris 1 (merged)
    ws.merge_cells("A1:G1")
    title_cell = ws["A1"]
    title_cell.value = f"Absensi {KELAS_LABEL} - {tanggal}"
    title_cell.font = Font(bold=True, size=13, color="FFFFFF")
    title_cell.fill = PatternFill(start_color="0D3B78", end_color="0D3B78", fill_type="solid")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 26

    # Header kolom di baris 3
    headers = ["No", "Nama", "NIM", "Gmail", "Tanggal", "Jam", "Status"]
    header_row = 3
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=header_row, column=col_idx, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="1565C0", end_color="1565C0", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Data
    for i, row in enumerate(rows, start=1):
        r = header_row + i
        values = [i, row["nama"], row["nim"], row["gmail"], row["tanggal"], row["jam"], row["status"]]
        for col_idx, val in enumerate(values, start=1):
            cell = ws.cell(row=r, column=col_idx, value=val)
            cell.alignment = Alignment(horizontal="center" if col_idx in (1, 3, 5, 6, 7) else "left")
            if i % 2 == 0:
                cell.fill = PatternFill(start_color="E8F1FC", end_color="E8F1FC", fill_type="solid")

    # Lebar kolom otomatis
    widths = [5, 24, 14, 26, 12, 10, 10]
    for col_idx, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = w

    # Baris total di bawah
    total_row = header_row + len(rows) + 2
    ws.cell(row=total_row, column=1, value="Total Hadir:").font = Font(bold=True)
    ws.cell(row=total_row, column=2, value=len(rows)).font = Font(bold=True)

    mem = io.BytesIO()
    wb.save(mem)
    mem.seek(0)

    filename = f"absensi_akuntansi2026C_{tanggal}.xlsx"
    return send_file(
        mem,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename,
    )


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin_login"))


import os
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
￼Enter
