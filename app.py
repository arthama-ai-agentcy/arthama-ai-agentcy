
import os
import json
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
from google import genai
from google.genai import types


# ============================================================
# ARTHAMA AI AGENCY — MASTER PROFESSIONAL SYSTEM
# ============================================================

APP_NAME = "Arthama AI Agency"
APP_VERSION = "1.0.0"

# Gunakan ID database lama yang sebelumnya sudah berfungsi.
DEFAULT_SHEET_ID = "1UmTUxXTPpOIj_La59KC62VrMyQNsLgd-kdIRGTk7qsY"

DEFAULT_WEBAPP_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbyLAeTxCerquzVtH4QSd87nAWNEkT-jT774uIONUMgxnEjvDJlVD1FmF6Tu3NmsL_-fXg/exec"
)

# Model mengikuti permintaan pemilik proyek.
GEMINI_MODEL = "gemini-3.8-flash"

DIVISIONS = {
    "AI Director": (
        "Direktur AI Arthama. Susun strategi, prioritaskan pekerjaan, "
        "koordinasikan divisi, dan berikan keputusan operasional yang terukur."
    ),
    "AI Marketing": (
        "Spesialis marketing. Buat strategi pemasaran, konten media sosial, "
        "copywriting, promosi, branding, SEO, dan kampanye pemasaran."
    ),
    "AI Sales": (
        "Spesialis penjualan. Buat strategi follow-up prospek, penawaran, "
        "skrip WhatsApp, analisis kebutuhan pelanggan, dan strategi closing."
    ),
    "AI Research": (
        "Analis riset. Teliti informasi yang diberikan, bandingkan alternatif, "
        "identifikasi asumsi, risiko, dan data yang masih perlu diverifikasi."
    ),
    "AI Customer Care": (
        "Spesialis layanan pelanggan. Susun jawaban yang ramah, profesional, "
        "jelas, solutif, dan sesuai kebutuhan pelanggan."
    ),
    "AI Analyst": (
        "Analis bisnis. Analisis data, prospek, performa, anggaran, "
        "estimasi biaya, margin, serta peluang dan risiko bisnis."
    ),
}

PROSPECT_COLUMNS = [
    "tanggalMasuk",
    "namaKlien",
    "whatsapp",
    "perusahaan",
    "kebutuhanAcara",
    "tanggalAcara",
    "jumlahPeserta",
    "budget",
    "statusProspek",
    "tindakLanjut",
    "catatan",
]


# ============================================================
# CONFIGURATION
# ============================================================

def get_config(name, default=""):
    """Ambil konfigurasi dari Streamlit Secrets atau environment."""
    try:
        value = st.secrets.get(name, None)
        if value is not None:
            return str(value)
    except Exception:
        pass

    return os.getenv(name, default)


def get_gemini_key():
    return get_config("GEMINI_API_KEY")


def get_webapp_url():
    return get_config("ARTHAMA_WEBAPP_URL", DEFAULT_WEBAPP_URL)


def get_api_token():
    return get_config("ARTHAMA_API_TOKEN")


def get_sheet_id():
    return get_config("GOOGLE_SHEET_ID", DEFAULT_SHEET_ID)


# ============================================================
# GEMINI AI
# ============================================================

def ask_gemini(department, task, business_context=""):
    """Kirim tugas ke Gemini dan kembalikan jawaban teks."""
    api_key = get_gemini_key()

    if not api_key:
        return (
            "GEMINI_API_KEY belum ditemukan. Tambahkan API key pada "
            "Streamlit Secrets. Jangan menuliskan API key di kode publik."
        )

    if department not in DIVISIONS:
        department = "AI Director"

    system_instruction = f"""
Anda adalah bagian dari {APP_NAME}.

DIVISI:
{department}

TANGGUNG JAWAB:
{DIVISIONS[department]}

ATURAN KERJA:
1. Gunakan bahasa Indonesia yang profesional dan mudah dipahami.
2. Berikan solusi yang praktis dan dapat dilaksanakan.
3. Jangan mengarang data, harga, hasil riset, atau status integrasi.
4. Bedakan fakta, estimasi, asumsi, dan rekomendasi.
5. Jika informasi kurang, jelaskan apa yang perlu dikonfirmasi.
6. Susun jawaban dengan judul dan daftar jika membantu.
7. Jangan mengklaim sudah melakukan tindakan di aplikasi eksternal
   jika tindakan tersebut belum benar-benar dilakukan.

KONTEKS BISNIS:
{business_context or "Belum ada konteks bisnis tambahan."}
"""

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=task,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.4,
            ),
        )

        answer = getattr(response, "text", None)

        if answer:
            return answer

        return "Gemini tidak mengembalikan teks. Silakan coba lagi."

    except Exception as exc:
        message = str(exc)
        return (
            "Permintaan ke Gemini gagal.\n\n"
            f"Detail: {message}\n\n"
            "Periksa API key, akses model, kuota, dan nama model "
            "yang tersedia pada akun Gemini API Anda."
        )


# ============================================================
# GOOGLE SHEETS CONNECTOR
# ============================================================

def sheets_request(action, data=None):
    """
    Memanggil Apps Script yang sudah digunakan proyek.
    Apps Script harus memeriksa ARTHAMA_API_TOKEN.
    """
    url = get_webapp_url()
    token = get_api_token()

    if not url:
        return {
            "success": False,
            "message": "ARTHAMA_WEBAPP_URL belum dikonfigurasi.",
        }

    if not token:
        return {
            "success": False,
            "message": "ARTHAMA_API_TOKEN belum dikonfigurasi.",
        }

    payload = {
        "action": action,
        "token": token,
    }

    if data is not None:
        payload["data"] = data

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        try:
            result = response.json()
        except ValueError:
            return {
                "success": False,
                "message": (
                    "Respons Apps Script bukan JSON. "
                    "Periksa URL deployment dan izin akses Web App."
                ),
            }

        if not isinstance(result, dict):
            return {
                "success": False,
                "message": "Format respons database tidak sesuai.",
            }

        if result.get("success") is False:
            return result

        return result

    except requests.RequestException as exc:
        return {
            "success": False,
            "message": f"Koneksi Google Sheets gagal: {exc}",
        }


def load_prospects():
    """Membaca data prospek dari database yang terhubung."""
    result = sheets_request("list")

    if result.get("success") is not True:
        return pd.DataFrame(), result.get(
            "message", "Data prospek belum berhasil dibaca."
        )

    rows = result.get("rows", [])

    if not rows:
        return pd.DataFrame(), "Database kosong."

    headers = [str(item).strip() for item in rows[0]]
    records = rows[1:]

    if not any(headers):
        return pd.DataFrame(), "Header database belum tersedia."

    normalized_records = []

    for row in records:
        normalized_records.append(
            list(row[:len(headers)])
            + [""] * max(0, len(headers) - len(row))
        )

    frame = pd.DataFrame(
        normalized_records,
        columns=headers,
    )

    return frame, None


def save_prospect(form_data):
    """Menambahkan satu prospek melalui Apps Script."""
    result = sheets_request("add", form_data)

    if result.get("success") is True:
        return True, "Prospek berhasil dikirim ke database."

    return False, result.get(
        "message", "Prospek belum berhasil disimpan."
    )


# ============================================================
# SESSION STATE
# ============================================================

if "ai_history" not in st.session_state:
    st.session_state.ai_history = []

if "last_prospects" not in st.session_state:
    st.session_state.last_prospects = pd.DataFrame()


# ============================================================
# STREAMLIT LAYOUT
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    [data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,0.25);
        padding: 14px;
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🤖 Arthama AI Agency")
st.caption(
    "Master Professional System · Dashboard, divisi AI, "
    "database prospek, dan status integrasi"
)

with st.sidebar:
    st.header("Master Command Center")

    page = st.radio(
        "Pilih menu",
        [
            "Dashboard",
            "AI Command Center",
            "Database Prospek",
            "Tambah Prospek",
            "Integrasi & Keamanan",
            "Riwayat AI",
        ],
    )

    st.divider()
    st.caption(f"Versi aplikasi: {APP_VERSION}")
    st.caption(f"Model yang dikonfigurasi: {GEMINI_MODEL}")


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":
    st.subheader("Ringkasan Operasional")

    gemini_ready = bool(get_gemini_key())
    database_configured = bool(get_webapp_url() and get_api_token())

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Divisi AI",
        len(DIVISIONS),
    )

    col2.metric(
        "Gemini API",
        "API key tersedia" if gemini_ready else "Belum dikonfigurasi",
    )

    col3.metric(
        "Database",
        "Konfigurasi tersedia"
        if database_configured
        else "Perlu konfigurasi",
    )

    st.info(
        "Status konfigurasi bukan bukti bahwa layanan berhasil terhubung. "
        "Gunakan menu Integrasi & Keamanan untuk melakukan pemeriksaan."
    )

    st.markdown("### Divisi yang tersedia")

    for name, description in DIVISIONS.items():
        with st.expander(name):
            st.write(description)

    st.markdown("### Alur kerja")
    st.write(
        "1. Pilih divisi pada AI Command Center.\n"
        "2. Masukkan tugas atau kebutuhan bisnis.\n"
        "3. Tinjau hasil AI sebelum digunakan.\n"
        "4. Kelola prospek melalui database jika koneksi berhasil."
    )


# ============================================================
# AI COMMAND CENTER
# ============================================================

elif page == "AI Command Center":
    st.subheader("AI Command Center")

    department = st.selectbox(
        "Pilih divisi AI",
        list(DIVISIONS.keys()),
    )

    business_context = st.text_area(
        "Konteks bisnis (opsional)",
        placeholder=(
            "Contoh: Arthama Management menyediakan jasa wisata, "
            "event organizer, outbound, gathering, dan sewa villa."
        ),
        height=100,
    )

    task = st.text_area(
        "Instruksi atau tugas",
        placeholder=(
            "Tuliskan tugas yang ingin dikerjakan oleh divisi AI..."
        ),
        height=180,
    )

    if st.button("Jalankan AI", type="primary", use_container_width=True):
        if not task.strip():
            st.warning("Masukkan tugas terlebih dahulu.")
        else:
            with st.spinner(f"{department} sedang bekerja..."):
                answer = ask_gemini(
                    department,
                    task.strip(),
                    business_context.strip(),
                )

            st.markdown("### Hasil")
            st.markdown(answer)

            st.session_state.ai_history.insert(
                0,
                {
                    "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "divisi": department,
                    "tugas": task.strip(),
                    "hasil": answer,
                },
            )

            st.download_button(
                "Unduh hasil sebagai TXT",
                data=answer,
                file_name="arthama_ai_result.txt",
                mime="text/plain",
            )


# ============================================================
# DATABASE PROSPEK
# ============================================================

elif page == "Database Prospek":
    st.subheader("Database Prospek")

    if st.button("Muat Ulang Data", type="primary"):
        with st.spinner("Mengambil data dari Google Sheets..."):
            frame, error = load_prospects()
            st.session_state.last_prospects = frame

        if error:
            st.warning(error)

    frame = st.session_state.last_prospects

    if frame.empty:
        st.info(
            "Belum ada data yang dimuat. Tekan Muat Ulang Data "
            "untuk membaca Google Sheets."
        )
    else:
        st.metric("Baris data terbaca", len(frame))
        st.dataframe(
            frame,
            use_container_width=True,
            hide_index=True,
        )

        csv_data = frame.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            "Ekspor data CSV",
            data=csv_data,
            file_name="arthama_prospek.csv",
            mime="text/csv",
        )


# ============================================================
# TAMBAH PROSPEK
# ============================================================

elif page == "Tambah Prospek":
    st.subheader("Tambah Prospek Baru")

    with st.form("prospect_form"):
        nama = st.text_input("Nama klien *")
        whatsapp = st.text_input("Nomor WhatsApp")
        perusahaan = st.text_input("Nama perusahaan")
        kebutuhan = st.text_area("Kebutuhan acara *")

        tanggal_acara = st.date_input(
            "Tanggal acara",
            value=None,
        )

        jumlah = st.number_input(
            "Jumlah peserta",
            min_value=0,
            step=1,
        )

        budget = st.text_input(
            "Budget",
            placeholder="Contoh: Rp25.000.000",
        )

        status = st.selectbox(
            "Status prospek",
            [
                "Prospek Baru",
                "Sudah Dihubungi",
                "Menunggu Konfirmasi",
                "Penawaran Dikirim",
                "Deal",
                "Tidak Lanjut",
            ],
        )

        tindak_lanjut = st.text_input("Tindak lanjut")
        catatan = st.text_area("Catatan tambahan")

        submitted = st.form_submit_button(
            "Simpan Prospek",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not nama.strip() or not kebutuhan.strip():
            st.error("Nama klien dan kebutuhan acara wajib diisi.")
        else:
            form_data = {
                "tanggalMasuk": datetime.now().strftime("%Y-%m-%d"),
                "namaKlien": nama.strip(),
                "whatsapp": whatsapp.strip(),
                "perusahaan": perusahaan.strip(),
                "kebutuhanAcara": kebutuhan.strip(),
                "tanggalAcara": (
                    tanggal_acara.isoformat()
                    if tanggal_acara
                    else ""
                ),
                "jumlahPeserta": int(jumlah),
                "budget": budget.strip(),
                "statusProspek": status,
                "tindakLanjut": tindak_lanjut.strip(),
                "catatan": catatan.strip(),
            }

            with st.spinner("Mengirim prospek ke Google Sheets..."):
                success, message = save_prospect(form_data)

            if success:
                st.success(message)
            else:
                st.error(message)


# ============================================================
# INTEGRASI & KEAMANAN
# ============================================================

elif page == "Integrasi & Keamanan":
    st.subheader("Integrasi & Keamanan")

    st.write(
        "Halaman ini memeriksa konfigurasi dasar. "
        "Status terhubung hanya ditampilkan setelah ada hasil pemeriksaan."
    )

    st.markdown("### 1. Gemini API")

    if st.button("Periksa Gemini API", key="test_gemini"):
        with st.spinner("Menguji akses Gemini..."):
            test_answer = ask_gemini(
                "AI Director",
                "Balas hanya dengan teks: KONEKSI GEMINI BERHASIL",
            )

        if "KONEKSI GEMINI BERHASIL" in test_answer:
            st.success("Gemini berhasil memberikan respons.")
        else:
            st.error("Pengujian Gemini belum berhasil.")
            st.code(test_answer)

    st.markdown("### 2. Google Sheets melalui Apps Script")

    if st.button("Periksa Google Sheets", key="test_sheets"):
        with st.spinner("Memeriksa koneksi database..."):
            result = sheets_request("list")

        if result.get("success") is True:
            st.success("Apps Script merespons dan aksi list berhasil.")
            st.write(
                f"Jumlah baris yang diterima: "
                f"{len(result.get('rows', []))}"
            )
        else:
            st.error("Koneksi database belum berhasil.")
            st.write(result.get("message", "Kesalahan tidak diketahui."))

    st.markdown("### 3. Layanan eksternal")

    integrations = [
        ("Google Sheets", "Menggunakan Apps Script dan token API."),
        ("Gmail", "Memerlukan integrasi Google OAuth."),
        ("WhatsApp Business", "Memerlukan API atau penyedia resmi."),
        ("Instagram / Facebook", "Memerlukan Meta OAuth dan izin yang sesuai."),
        ("TikTok", "Memerlukan autentikasi dan akses API yang sesuai."),
    ]

    for service, requirement in integrations:
        with st.expander(service):
            st.write(requirement)
            st.caption(
                "Belum diverifikasi oleh aplikasi ini. "
                "Jangan menganggap layanan telah terhubung."
            )

    st.markdown("### Keamanan")
    st.write(
        "- Simpan API key dan token pada Streamlit Secrets.\n"
        "- Jangan memasukkan rahasia ke kode publik GitHub.\n"
        "- Batasi akses editor repositori dan Google Sheets.\n"
        "- Jangan membagikan token API melalui chat.\n"
        "- Periksa izin deployment Apps Script secara berkala."
    )


# ============================================================
# RIWAYAT AI
# ============================================================

elif page == "Riwayat AI":
    st.subheader("Riwayat Pekerjaan AI")

    history = st.session_state.ai_history

    if not history:
        st.info(
            "Belum ada pekerjaan AI pada sesi aplikasi ini. "
            "Riwayat ini belum disimpan permanen ke Google Sheets."
        )
    else:
        for index, item in enumerate(history):
            with st.expander(
                f"{item['waktu']} · {item['divisi']}"
            ):
                st.markdown("**Tugas**")
                st.write(item["tugas"])

                st.markdown("**Hasil**")
                st.markdown(item["hasil"])

        if st.button("Hapus Riwayat Sesi"):
            st.session_state.ai_history = []
            st.rerun()

st.divider()
st.caption(
    "Arthama AI Agency · Master Professional System · "
    "Tinjau hasil AI sebelum mengambil keputusan bisnis."
)
