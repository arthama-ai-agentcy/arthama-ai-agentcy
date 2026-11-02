
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
APP_VERSION = "1.1.0"

DEFAULT_SHEET_ID = "1UmTUxXTPpOIj_La59KC62VrMyQNsLgd-kdIRGTk7qsY"

DEFAULT_WEBAPP_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbyLAeTxCerquzVtH4QSd87nAWNEkT-jT774uIONUMgxnEjvDJlVD1FmF6Tu3NmsL_-fXg/exec"
)

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

# Nama divisi yang dikirim ke n8n Switch.
N8N_DIVISIONS = {
    "AI Director": "director",
    "AI Marketing": "marketing",
    "AI Sales": "sales",
    "AI Research": "research",
    "AI Customer Care": "customer_care",
    "AI Analyst": "analyst",
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
# STREAMLIT PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


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


def get_n8n_url():
    return get_config("N8N_WEBHOOK_URL")


# ============================================================
# N8N CONNECTOR
# ============================================================

def send_n8n_event(department, event="ai_task_started"):
    """
    Mengirim event minimal ke n8n.
    Tidak mengirim isi tugas, hasil AI, data pelanggan,
    API key Gemini, atau token Google Sheets.
    """

    webhook_url = get_n8n_url()

    if not webhook_url:
        return {
            "success": False,
            "message": "N8N_WEBHOOK_URL belum dikonfigurasi.",
        }

    division_code = N8N_DIVISIONS.get(department)

    if not division_code:
        return {
            "success": False,
            "message": "Nama divisi belum memiliki kode n8n.",
        }

    payload = {
        "division": division_code,
        "event": event,
        "source": APP_NAME,
        "version": APP_VERSION,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=20,
        )

        response.raise_for_status()

        try:
            result = response.json()
        except ValueError:
            result = {"message": response.text[:500]}

        return {
            "success": True,
            "status_code": response.status_code,
            "message": "Webhook n8n menerima permintaan.",
            "response": result,
        }

    except requests.RequestException as exc:
        return {
            "success": False,
            "message": f"Koneksi n8n gagal: {exc}",
        }


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
        return (
            "Permintaan ke Gemini gagal.\n\n"
            f"Detail: {str(exc)}\n\n"
            "Periksa API key, akses model, kuota, dan nama model "
            "yang tersedia pada akun Gemini API Anda."
        )


# ============================================================
# GOOGLE SHEETS CONNECTOR
# ============================================================

def sheets_request(action, data=None):
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
# STREAMLIT STYLE
# ARTHAMA PROFESSIONAL BLUE & GOLD THEME
# Hanya mengubah desain visual.
# ============================================================

st.markdown(
    """
    <style>

    /* =================================
       GLOBAL BACKGROUND
    ================================= */

    .stApp {
        background: linear-gradient(
            145deg,
            #f4f7fc 0%,
            #eaf1fa 55%,
            #f8faff 100%
        );
        color: #172b4d;
    }

    .block-container {
        padding-top: 1.7rem;
        padding-bottom: 2.5rem;
        max-width: 1450px;
    }

    h1, h2, h3 {
        color: #102f5b !important;
        font-weight: 750 !important;
        letter-spacing: -0.4px;
    }

    p, label {
        color: #344966;
    }

    /* =================================
       SIDEBAR
    ================================= */

    [data-testid="stSidebar"] {
        background: linear-gradient(
            180deg,
            #102f5b 0%,
            #174b82 55%,
            #10345e 100%
        );
        border-right: 3px solid #d5ad55;
    }

    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.25);
    }

    [data-testid="stSidebar"] [role="radiogroup"] label {
        background: rgba(255,255,255,0.08);
        border-radius: 9px;
        padding: 9px 12px;
        margin-bottom: 5px;
        transition: 0.2s ease;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: rgba(255,255,255,0.19);
    }

    /* =================================
       MAIN HEADER
    ================================= */

    [data-testid="stAppViewBlockContainer"] h1 {
        border-bottom: 3px solid #d5ad55;
        padding-bottom: 12px;
    }

    /* =================================
       METRIC CARDS
    ================================= */

    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #dce6f2;
        border-left: 4px solid #2474bd;
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 4px 14px rgba(16,47,91,0.07);
    }

    [data-testid="stMetricLabel"] {
        color: #58708e !important;
        font-weight: 600;
    }

    [data-testid="stMetricValue"] {
        color: #123d70 !important;
        font-weight: 750;
    }

    /* =================================
       BUTTONS
    ================================= */

    .stButton > button,
    .stDownloadButton > button,
    .stFormSubmitButton > button {
        background: linear-gradient(
            100deg,
            #174b82,
            #2479bd
        );
        color: #ffffff !important;
        border: none;
        border-radius: 10px;
        padding: 10px 18px;
        font-weight: 650;
        box-shadow: 0 3px 9px rgba(23,75,130,0.18);
        transition: 0.2s ease;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover,
    .stFormSubmitButton > button:hover {
        background: linear-gradient(
            100deg,
            #10345e,
            #1d639f
        );
        border: none;
        transform: translateY(-1px);
    }

    /* =================================
       INPUT FIELDS
    ================================= */

    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input,
    .stDateInput input {
        background: #ffffff !important;
        border: 1px solid #cbd9e9 !important;
        border-radius: 9px !important;
        color: #172b4d !important;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color: #2479bd !important;
        box-shadow: 0 0 0 2px rgba(36,121,189,0.12);
    }

    /* =================================
       SELECT BOX
    ================================= */

    [data-baseweb="select"] > div {
        background: #ffffff;
        border-radius: 9px;
        border-color: #cbd9e9;
    }

    /* =================================
       EXPANDER
    ================================= */

    [data-testid="stExpander"] {
        background: #ffffff;
        border: 1px solid #dce6f2;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(16,47,91,0.04);
    }

    [data-testid="stExpander"] summary {
        color: #174b82;
        font-weight: 650;
    }

    /* =================================
       ALERTS
    ================================= */

    [data-testid="stAlert"] {
        border-radius: 10px;
    }

    /* =================================
       DATAFRAME
    ================================= */

    [data-testid="stDataFrame"] {
        border: 1px solid #dce6f2;
        border-radius: 12px;
        overflow: hidden;
    }

    /* =================================
       TABS
    ================================= */

    [data-baseweb="tab-list"] {
        gap: 8px;
    }

    [data-baseweb="tab"] {
        color: #174b82;
        font-weight: 600;
    }

    /* =================================
       DIVIDER
    ================================= */

    hr {
        border-color: #d5e0ed;
    }

    /* =================================
       FOOTER
    ================================= */

    [data-testid="stCaptionContainer"] {
        color: #71839a;
    }

    /* =================================
       RESPONSIVE MOBILE
    ================================= */

    @media (max-width: 768px) {
        .block-container {
            padding: 1rem 0.8rem 2rem;
        }

        h1 {
            font-size: 1.65rem !important;
        }

        [data-testid="stMetric"] {
            padding: 12px;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


st.title("🤖 Arthama AI Agency")
st.caption(
    "Master Professional System · Dashboard, divisi AI, "
    "database prospek, dan integrasi n8n"
)


# ============================================================
# SIDEBAR
# ============================================================

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
    st.caption(f"Model: {GEMINI_MODEL}")


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":
    st.subheader("Ringkasan Operasional")

    gemini_ready = bool(get_gemini_key())
    database_configured = bool(
        get_webapp_url() and get_api_token()
    )
    n8n_ready = bool(get_n8n_url())

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Divisi AI", len(DIVISIONS))

    col2.metric(
        "Gemini API",
        "API key tersedia" if gemini_ready else "Belum dikonfigurasi",
    )

    col3.metric(
        "Google Sheets",
        "Konfigurasi tersedia"
        if database_configured else "Perlu konfigurasi",
    )

    col4.metric(
        "n8n",
        "URL tersedia" if n8n_ready else "Belum dikonfigurasi",
    )

    st.info(
        "Status konfigurasi bukan bukti layanan berhasil terhubung. "
        "Gunakan menu Integrasi & Keamanan untuk menguji koneksi."
    )

    st.markdown("### Divisi yang tersedia")

    for name, description in DIVISIONS.items():
        with st.expander(name):
            st.write(description)

    st.markdown("### Alur kerja")
    st.write(
        "1. Pilih divisi pada AI Command Center.\n"
        "2. Tugas dikerjakan oleh Gemini.\n"
        "3. Informasi event divisi dikirim ke n8n.\n"
        "4. Kelola prospek melalui Google Sheets."
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
        placeholder="Tuliskan tugas yang ingin dikerjakan oleh divisi AI...",
        height=180,
    )

    if st.button(
        "Jalankan AI",
        type="primary",
        use_container_width=True,
    ):
        if not task.strip():
            st.warning("Masukkan tugas terlebih dahulu.")

        else:
            with st.spinner(f"{department} sedang bekerja..."):
                answer = ask_gemini(
                    department,
                    task.strip(),
                    business_context.strip(),
                )

                n8n_result = send_n8n_event(
                    department,
                    event="ai_task_completed",
                )

            st.markdown("### Hasil")
            st.markdown(answer)

            if n8n_result.get("success"):
                st.success(
                    "Event divisi berhasil dikirim ke n8n."
                )
            else:
                st.warning(
                    "Hasil Gemini tersedia, tetapi pengiriman event "
                    f"ke n8n gagal: {n8n_result.get('message')}"
                )

            st.session_state.ai_history.insert(
                0,
                {
                    "waktu": datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "divisi": department,
                    "tugas": task.strip(),
                    "hasil": answer,
                    "n8n": (
                        "Terkirim"
                        if n8n_result.get("success")
                        else "Gagal"
                    ),
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

        csv_data = frame.to_csv(
            index=False
        ).encode("utf-8-sig")

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
            st.error(
                "Nama klien dan kebutuhan acara wajib diisi."
            )

        else:
            form_data = {
                "tanggalMasuk": datetime.now().strftime("%Y-%m-%d"),
                "namaKlien": nama.strip(),
                "whatsapp": whatsapp.strip(),
                "perusahaan": perusahaan.strip(),
                "kebutuhanAcara": kebutuhan.strip(),
                "tanggalAcara": (
                    tanggal_acara.isoformat()
                    if tanggal_acara else ""
                ),
                "jumlahPeserta": int(jumlah),
                "budget": budget.strip(),
                "statusProspek": status,
                "tindakLanjut": tindak_lanjut.strip(),
                "catatan": catatan.strip(),
            }

            with st.spinner(
                "Mengirim prospek ke Google Sheets..."
            ):
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

    st.markdown("### 1. Gemini API")

    if st.button(
        "Periksa Gemini API",
        key="test_gemini",
    ):
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

    st.divider()
    st.markdown("### 2. Google Sheets melalui Apps Script")

    if st.button(
        "Periksa Google Sheets",
        key="test_sheets",
    ):
        with st.spinner("Memeriksa koneksi database..."):
            result = sheets_request("list")

        if result.get("success") is True:
            st.success(
                "Apps Script merespons dan aksi list berhasil."
            )
            st.write(
                "Jumlah baris yang diterima: "
                f"{len(result.get('rows', []))}"
            )
        else:
            st.error("Koneksi database belum berhasil.")
            st.write(
                result.get(
                    "message",
                    "Kesalahan tidak diketahui.",
                )
            )

    st.divider()
    st.markdown("### 3. n8n Automation")

    if not get_n8n_url():
        st.warning(
            "N8N_WEBHOOK_URL belum ditemukan di Streamlit Secrets."
        )
    else:
        st.success("URL webhook n8n sudah dikonfigurasi.")

        if st.button(
            "Periksa Koneksi n8n",
            key="test_n8n",
            type="primary",
        ):
            with st.spinner("Menghubungi webhook n8n..."):
                n8n_result = send_n8n_event(
                    "AI Marketing",
                    event="connection_test",
                )

            if n8n_result.get("success"):
                st.success(
                    "Webhook n8n berhasil menerima permintaan."
                )
                st.write(
                    "HTTP Status:",
                    n8n_result.get("status_code"),
                )
                st.json(n8n_result.get("response", {}))
            else:
                st.error(
                    n8n_result.get(
                        "message",
                        "Koneksi n8n gagal.",
                    )
                )

    st.caption(
        "Pemeriksaan ini menguji respons HTTP webhook. "
        "Respons sukses belum membuktikan semua proses otomatis "
        "di dalam workflow sudah selesai."
    )

    st.divider()
    st.markdown("### 4. Layanan eksternal")

    integrations = [
        (
            "Google Sheets",
            "Menggunakan Apps Script dan token API.",
        ),
        (
            "Gmail",
            "Memerlukan integrasi Google OAuth.",
        ),
        (
            "WhatsApp Business",
            "Memerlukan API atau penyedia resmi.",
        ),
        (
            "Instagram / Facebook",
            "Memerlukan Meta OAuth dan izin yang sesuai.",
        ),
        (
            "TikTok",
            "Memerlukan autentikasi dan akses API yang sesuai.",
        ),
    ]

    for service, requirement in integrations:
        with st.expander(service):
            st.write(requirement)
            st.caption(
                "Belum diverifikasi oleh aplikasi ini."
            )

    st.divider()
    st.markdown("### Keamanan")

    st.write(
        "- Simpan API key dan token pada Streamlit Secrets.\n"
        "- Jangan memasukkan rahasia ke kode publik GitHub.\n"
        "- Batasi akses editor repositori dan Google Sheets.\n"
        "- Jangan membagikan token API melalui chat.\n"
        "- Webhook n8n saat ini belum memakai autentikasi.\n"
        "- Jangan mengirim data pelanggan melalui webhook "
        "sebelum autentikasi dan perlindungan akses diaktifkan."
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
        for item in history:
            with st.expander(
                f"{item['waktu']} · {item['divisi']}"
            ):
                st.markdown("**Tugas**")
                st.write(item["tugas"])

                st.markdown("**Hasil**")
                st.markdown(item["hasil"])

                st.caption(
                    f"Status event n8n: {item.get('n8n', 'Tidak diketahui')}"
                )

        if st.button("Hapus Riwayat Sesi"):
            st.session_state.ai_history = []
            st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Arthama AI Agency · Master Professional System · "
    "Tinjau hasil AI sebelum mengambil keputusan bisnis."
)
