
import os
import io
import csv
import json
import time
import requests
import streamlit as st
from datetime import datetime

# ============================================================
# ARTHAMA AI AGENCY
# Aplikasi bisnis: AI Assistant, Sales CRM, Studio Konten
# ============================================================

st.set_page_config(
    page_title="Arthama AI Agency",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_NAME = "ARTHAMA AI AGENCY"
APP_VERSION = "2.0.0"

# ------------------------------------------------------------
# 1. DESAIN DAN TEMA
# ------------------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: #f4f7fb;
        color: #172033;
    }

    [data-testid="stSidebar"] {
        background: #101d36;
    }

    [data-testid="stSidebar"] * {
        color: #f4f7fb;
    }

    [data-testid="stSidebar"] .stRadio label {
        font-size: 15px;
        font-weight: 500;
    }

    h1, h2, h3 {
        color: #14284b;
        letter-spacing: -0.4px;
    }

    p, li, label, .stMarkdown {
        line-height: 1.65;
    }

    .hero {
        padding: 28px;
        border-radius: 20px;
        background: linear-gradient(120deg, #11274b, #174d86);
        color: white;
        margin-bottom: 22px;
    }

    .hero h1 {
        color: white;
        font-size: 30px;
        margin-bottom: 8px;
    }

    .hero p {
        color: #e3edff;
        font-size: 15px;
        margin-bottom: 0;
    }

    .section-card {
        padding: 20px;
        border-radius: 16px;
        background: white;
        border: 1px solid #e2e8f0;
        margin-bottom: 16px;
    }

    .small-muted {
        color: #65748b;
        font-size: 13px;
    }

    .status-pill {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 20px;
        background: #e8f2ff;
        color: #174d86;
        font-size: 12px;
        font-weight: 700;
    }

    div[data-testid="stMetric"] {
        background: white;
        padding: 17px;
        border: 1px solid #e2e8f0;
        border-radius: 15px;
    }

    div[data-testid="stMetricLabel"] {
        color: #65748b;
    }

    .stButton button {
        border-radius: 10px;
        font-weight: 600;
        min-height: 42px;
    }

    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"] {
        border-radius: 10px;
    }

    [data-testid="stAlert"] {
        border-radius: 12px;
    }

    footer {
        visibility: hidden;
    }

    @media (max-width: 768px) {
        .hero {
            padding: 20px;
        }
        .hero h1 {
            font-size: 24px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# 2. KONFIGURASI RAHASIA
# ------------------------------------------------------------

def secret_value(name, default=""):
    """Membaca Streamlit Secrets dengan aman."""
    try:
        value = st.secrets.get(name, default)
        return str(value).strip() if value is not None else default
    except Exception:
        return os.getenv(name, default).strip()


# ------------------------------------------------------------
# 3. STATE APLIKASI
# ------------------------------------------------------------

if "ai_history" not in st.session_state:
    st.session_state.ai_history = []

if "content_result" not in st.session_state:
    st.session_state.content_result = ""

if "crm_last_result" not in st.session_state:
    st.session_state.crm_last_result = None

if "connection_test_result" not in st.session_state:
    st.session_state.connection_test_result = None


# ------------------------------------------------------------
# 4. GEMINI AI
# ------------------------------------------------------------

SYSTEM_INSTRUCTION = """
Kamu adalah Arthama AI, asisten bisnis profesional Arthama Management
di Indonesia.

Tugas:
- Membantu strategi pemasaran dan penjualan.
- Membuat penawaran paket wisata, outbound, gathering, meeting dan event.
- Menyusun proposal, rundown, caption, naskah iklan dan ide konten.
- Membantu layanan pelanggan dan pengembangan bisnis.
- Membantu perencanaan anggaran jika data biaya tersedia.

Aturan:
- Jawab dalam bahasa Indonesia yang jelas, profesional, dan praktis.
- Gunakan judul, poin, tabel teks, dan langkah kerja bila sesuai.
- Jangan mengarang hasil pencarian, data aktual, harga vendor,
  transaksi, atau tindakan yang belum dilakukan.
- Bedakan angka yang diberikan pengguna dari estimasi.
- Jika data belum lengkap, jelaskan asumsi secara terbuka.
- Untuk perhitungan, tampilkan rumus dan hasilnya.
"""

def tanya_gemini(pertanyaan):
    """Mengirim pertanyaan ke Gemini dan mengembalikan teks jawaban."""
    if not isinstance(pertanyaan, str) or not pertanyaan.strip():
        raise ValueError("Pertanyaan tidak boleh kosong.")

    api_key = secret_value("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY belum tersedia. Periksa Streamlit Secrets."
        )

    # Model dapat diubah melalui Streamlit Secrets: GEMINI_MODEL
    model = secret_value("GEMINI_MODEL", "gemini-2.5-flash")

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError(
            "Library google-genai belum terpasang. "
            "Periksa requirements.txt lalu restart aplikasi."
        ) from exc

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=60000),
    )

    response = client.models.generate_content(
        model=model,
        contents=pertanyaan.strip(),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.7,
            max_output_tokens=4096,
        ),
    )

    jawaban = getattr(response, "text", None)
    if not jawaban or not jawaban.strip():
        raise RuntimeError(
            "Gemini tidak memberikan teks jawaban. Coba pertanyaan lain."
        )

    return jawaban.strip()


def tampilkan_error_ai(error):
    """Menampilkan petunjuk yang lebih berguna untuk error Gemini."""
    pesan = str(error)
    lower = pesan.lower()

    if any(x in lower for x in ["429", "quota", "resource_exhausted"]):
        st.error("Kuota atau batas permintaan Gemini sedang tercapai.")
        st.markdown(
            """
            **Yang bisa dilakukan:**
            1. Periksa penggunaan dan kuota di Google AI Studio.
            2. Tunggu sampai batas permintaan diperbarui.
            3. Periksa apakah model yang digunakan memiliki kuota.
            4. Jangan mengirim pertanyaan berulang kali dalam waktu singkat.
            """
        )
    elif any(x in lower for x in ["503", "unavailable", "overloaded"]):
        st.error("Layanan Gemini sedang tidak tersedia atau sibuk.")
        st.info("Coba kembali beberapa saat lagi.")
    elif any(x in lower for x in ["401", "403", "api key", "permission"]):
        st.error("Kunci API atau izin akses Gemini bermasalah.")
        st.info(
            "Periksa GEMINI_API_KEY di Streamlit Secrets. "
            "Jangan membagikan kunci API di chat atau kode publik."
        )
    elif any(x in lower for x in ["404", "not found"]):
        st.error("Model Gemini tidak ditemukan atau tidak tersedia.")
        st.info(
            "Periksa nama model yang benar di Google AI Studio, "
            "lalu atur nilai GEMINI_MODEL di Streamlit Secrets."
        )
    elif any(x in lower for x in ["timeout", "timed out"]):
        st.error("Permintaan AI melewati batas waktu.")
        st.info("Coba pertanyaan yang lebih singkat atau ulangi nanti.")
    else:
        st.error("Terjadi kesalahan saat menghubungi layanan AI.")
        with st.expander("Detail teknis"):
            st.code(pesan[:1500])


# ------------------------------------------------------------
# 5. KONEKTOR GOOGLE SHEETS / CRM
# ------------------------------------------------------------

def arthama_api(action, data=None):
    """
    Menghubungkan aplikasi ke Apps Script yang sudah digunakan.
    Mempertahankan format action/token/data.
    """
    url = secret_value("ARTHAMA_WEBAPP_URL")
    token = secret_value("ARTHAMA_API_TOKEN")

    if not url:
        raise RuntimeError(
            "ARTHAMA_WEBAPP_URL belum tersedia di Streamlit Secrets."
        )
    if not token:
        raise RuntimeError(
            "ARTHAMA_API_TOKEN belum tersedia di Streamlit Secrets."
        )

    payload = {
        "action": action,
        "token": token,
    }
    if data is not None:
        payload["data"] = data

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
    except requests.Timeout as exc:
        raise RuntimeError(
            "Koneksi CRM timeout. Silakan coba kembali."
        ) from exc
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Koneksi CRM gagal: {exc}"
        ) from exc

    try:
        result = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "Respons CRM bukan JSON. Isi respons: "
            + response.text[:300]
        ) from exc

    if isinstance(result, dict):
        if result.get("status") == "error" or result.get("success") is False:
            raise RuntimeError(
                str(result.get("message", "CRM mengembalikan error."))
            )

    return result


def ekstrak_data_crm(result):
    """Mencoba membaca beberapa format respons Apps Script."""
    if isinstance(result, list):
        return result

    if isinstance(result, dict):
        for key in ("data", "rows", "records", "clients", "result"):
            value = result.get(key)
            if isinstance(value, list):
                return value

    return []


def tampilkan_data_crm(data):
    """Menampilkan data CRM dalam tabel Streamlit."""
    import pandas as pd

    if not data:
        st.info(
            "Belum ada data yang bisa ditampilkan, atau format respons "
            "belum dikenali. Periksa respons konektor sebelum mengubah "
            "struktur database."
        )
        return

    try:
        df = pd.DataFrame(data)
        if df.empty:
            st.info("Data CRM masih kosong.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button(
                "Unduh data CRM CSV",
                data=df.to_csv(index=False).encode("utf-8-sig"),
                file_name="arthama_crm_export.csv",
                mime="text/csv",
                use_container_width=True,
            )
    except Exception as exc:
        st.warning("Data diterima, tetapi gagal ditampilkan sebagai tabel.")
        st.code(str(exc))


# ------------------------------------------------------------
# 6. SIDEBAR / NAVIGASI
# ------------------------------------------------------------

with st.sidebar:
    st.markdown("# 🤖 ARTHAMA")
    st.caption("AI Agency & Business Management")
    st.divider()

    page = st.radio(
        "MENU UTAMA",
        [
            "Command Center",
            "Divisi Robot AI",
            "Sales CRM",
            "Studio Konten",
            "Koneksi Akun",
            "Pengaturan & Keamanan",
        ],
        key="main_navigation",
    )

    st.divider()
    st.caption(f"Versi aplikasi {APP_VERSION}")
    st.caption("Arthama Management")
    st.caption("Sistem kerja internal")


# ------------------------------------------------------------
# 7. HEADER HALAMAN
# ------------------------------------------------------------

def header(judul, deskripsi):
    st.markdown(
        f"""
        <div class="hero">
            <h1>{judul}</h1>
            <p>{deskripsi}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------
# 8. COMMAND CENTER
# ------------------------------------------------------------

if page == "Command Center":
    header(
        "Command Center",
        "Pusat kendali operasional dan produktivitas Arthama Management.",
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Modul Aplikasi", "6")
    with col2:
        st.metric("Asisten AI", "Gemini")
    with col3:
        st.metric("Database CRM", "Google Sheets")

    st.subheader("Selamat datang di Arthama AI Agency")
    st.write(
        "Gunakan dashboard ini untuk membantu pekerjaan pemasaran, "
        "menyusun konten, mengelola calon klien, dan merencanakan event."
    )

    a, b = st.columns(2)
    with a:
        st.markdown(
            """
            <div class="section-card">
                <h3>🤖 Divisi Robot AI</h3>
                <p>
                Asisten untuk ide bisnis, strategi pemasaran, penawaran,
                rundown acara, dan analisis berdasarkan data yang diberikan.
                </p>
                </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Buka Divisi Robot AI", use_container_width=True):
            st.session_state.main_navigation = "Divisi Robot AI"
            st.rerun()

    with b:
        st.markdown(
            """
            <div class="section-card">
                <h3>📊 Sales CRM</h3>
                <p>
                Melihat data calon klien dan menambahkan prospek baru
                melalui konektor Google Sheets yang telah dikonfigurasi.
                </p>
                </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Buka Sales CRM", use_container_width=True):
            st.session_state.main_navigation = "Sales CRM"
            st.rerun()

    st.subheader("Alur kerja yang disarankan")
    st.markdown(
        """
        1. Gunakan **Divisi Robot AI** untuk membuat strategi atau draft.
        2. Gunakan **Studio Konten** untuk menyusun materi pemasaran.
        3. Catat prospek melalui **Sales CRM**.
        4. Periksa **Koneksi Akun** jika layanan tidak tersambung.
        """
    )


# ------------------------------------------------------------
# 9. DIVISI ROBOT AI
# ------------------------------------------------------------

elif page == "Divisi Robot AI":
    header(
        "Divisi Robot AI",
        "Asisten kerja untuk pemasaran, penjualan, event, dan pengembangan bisnis.",
    )

    st.info(
        "Jawaban AI adalah bantuan otomatis. Periksa kembali harga, "
        "perhitungan, jadwal, dan informasi penting sebelum dikirim "
        "kepada klien."
    )

    contoh = st.selectbox(
        "Pilih contoh kebutuhan (opsional)",
        [
            "Tulis pertanyaan sendiri",
            "Buat penawaran outbound perusahaan",
            "Susun rundown gathering 2 hari 1 malam",
            "Buat strategi pemasaran villa weekday",
            "Buat follow-up WhatsApp untuk calon klien",
            "Analisis harga dan estimasi keuntungan paket wisata",
        ],
    )

    contoh_prompt = {
        "Buat penawaran outbound perusahaan":
            "Bantu buat penawaran outbound perusahaan. Tanyakan data "
            "yang masih kurang sebelum menentukan harga.",
        "Susun rundown gathering 2 hari 1 malam":
            "Susun contoh rundown gathering 2 hari 1 malam yang profesional. "
            "Tandai bagian yang perlu disesuaikan dengan lokasi dan waktu.",
        "Buat strategi pemasaran villa weekday":
            "Buat strategi pemasaran villa weekday dengan anggaran terbatas, "
            "CTA yang jelas, dan langkah yang bisa dikerjakan dari HP.",
        "Buat follow-up WhatsApp untuk calon klien":
            "Buat pesan follow-up WhatsApp yang sopan, profesional, "
            "tidak memaksa, dan mengajak calon klien memberikan kepastian.",
        "Analisis harga dan estimasi keuntungan paket wisata":
            "Bantu menghitung harga jual dan keuntungan paket wisata. "
            "Minta rincian biaya, jumlah peserta, dan komponen paket "
            "jika datanya belum diberikan.",
    }

    if contoh != "Tulis pertanyaan sendiri":
        st.caption("Contoh kebutuhan:")
        st.write(contoh_prompt[contoh])

    pertanyaan = st.text_area(
        "Apa yang ingin kamu kerjakan?",
        placeholder=(
            "Contoh: Buatkan strategi mendapatkan 10 calon klien gathering "
            "perusahaan dalam 30 hari dengan anggaran terbatas."
        ),
        height=150,
        key="ai_question",
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        jalankan = st.button(
            "✨ Proses dengan AI",
            type="primary",
            use_container_width=True,
        )
    with col2:
        if st.button("Hapus riwayat", use_container_width=True):
            st.session_state.ai_history = []
            st.rerun()

    if jalankan:
        prompt_final = pertanyaan.strip()

        if not prompt_final and contoh != "Tulis pertanyaan sendiri":
            prompt_final = contoh_prompt[contoh]

        if not prompt_final:
            st.warning("Masukkan pertanyaan terlebih dahulu.")
        else:
            with st.spinner("AI sedang menyusun jawaban..."):
                try:
                    jawaban = tanya_gemini(prompt_final)
                    st.session_state.ai_history.append(
                        {
                            "waktu": datetime.now().strftime("%d-%m-%Y %H:%M"),
                            "pertanyaan": prompt_final,
                            "jawaban": jawaban,
                        }
                    )
                    st.session_state.ai_last_answer = jawaban
                    st.success("Jawaban berhasil dibuat.")
                except Exception as exc:
                    tampilkan_error_ai(exc)

    if st.session_state.get("ai_last_answer"):
        st.subheader("Hasil jawaban AI")
        st.markdown(st.session_state.ai_last_answer)
        st.download_button(
            "Unduh jawaban sebagai TXT",
            data=st.session_state.ai_last_answer.encode("utf-8"),
            file_name="arthama_jawaban_ai.txt",
            mime="text/plain",
            use_container_width=True,
        )

    if st.session_state.ai_history:
        with st.expander("Riwayat pertanyaan sesi ini"):
            for i, item in enumerate(
                reversed(st.session_state.ai_history), start=1
            ):
                st.markdown(f"**{i}. {item['waktu']}**")
                st.write(item["pertanyaan"])
                with st.expander("Lihat jawaban"):
                    st.markdown(item["jawaban"])


# ------------------------------------------------------------
# 10. SALES CRM
# ------------------------------------------------------------

elif page == "Sales CRM":
    header(
        "Sales CRM",
        "Kelola calon klien melalui konektor Google Sheets yang sudah ada.",
    )

    st.warning(
        "Modul ini menggunakan action `list` dan `add` pada Apps Script "
        "yang telah dikonfigurasi. Kolom baru tidak ditambahkan ke database "
        "secara otomatis."
    )

    tab1, tab2 = st.tabs(["📋 Data Calon Klien", "➕ Tambah Calon Klien"])

    with tab1:
        st.subheader("Data CRM")
        if st.button("Muat / segarkan data CRM", type="primary"):
            with st.spinner("Mengambil data dari Google Sheets..."):
                try:
                    result = arthama_api("list")
                    st.session_state.crm_last_result = result
                    st.success("Respons CRM berhasil diterima.")
                except Exception as exc:
                    st.error(f"Gagal mengambil data CRM: {exc}")

        result = st.session_state.crm_last_result
        if result is not None:
            with st.expander("Lihat respons asli konektor"):
                st.json(result)
            data = ekstrak_data_crm(result)
            tampilkan_data_crm(data)

    with tab2:
        st.subheader("Tambah prospek baru")

        with st.form("crm_add_form", clear_on_submit=False):
            nama = st.text_input("Nama calon klien *")
            perusahaan = st.text_input("Perusahaan / instansi")
            telepon = st.text_input("Nomor WhatsApp")
            email = st.text_input("Email")
            kebutuhan = st.text_area(
                "Kebutuhan acara / produk",
                placeholder="Contoh: gathering perusahaan, outbound, villa...",
            )
            tanggal = st.text_input(
                "Tanggal acara",
                placeholder="Contoh: 20-12-2026 atau belum ditentukan",
            )
            peserta = st.text_input(
                "Jumlah peserta",
                placeholder="Contoh: 100 orang",
            )
            budget = st.text_input(
                "Estimasi anggaran",
                placeholder="Contoh: Rp500.000/orang",
            )
            catatan = st.text_area("Catatan tambahan")
            submit = st.form_submit_button(
                "Simpan ke CRM",
                type="primary",
                use_container_width=True,
            )

        if submit:
            if not nama.strip():
                st.error("Nama calon klien wajib diisi.")
            else:
                # Format data ini mengikuti pola connector yang sudah ada.
                # Pastikan Apps Script menerima nama field berikut.
                payload = {
                    "nama": nama.strip(),
                    "perusahaan": perusahaan.strip(),
                    "telepon": telepon.strip(),
                    "email": email.strip(),
                    "kebutuhan": kebutuhan.strip(),
                    "tanggal_acara": tanggal.strip(),
                    "jumlah_peserta": peserta.strip(),
                    "budget": budget.strip(),
                    "catatan": catatan.strip(),
                    "sumber": "Arthama AI Agency",
                    "waktu_input": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

                try:
                    with st.spinner("Mengirim data ke CRM..."):
                        result = arthama_api("add", payload)
                    st.success("Permintaan tambah data dikirim ke konektor.")
                    st.json(result)
                    st.caption(
                        "Pastikan respons konektor menyatakan berhasil, "
                        "lalu segarkan data CRM untuk memverifikasi baris baru."
                    )
                except Exception as exc:
                    st.error(f"Gagal menambahkan calon klien: {exc}")


# ------------------------------------------------------------
# 11. STUDIO KONTEN
# ------------------------------------------------------------

elif page == "Studio Konten":
    header(
        "Studio Konten",
        "Buat materi promosi dan komunikasi pemasaran secara lebih terstruktur.",
    )

    jenis = st.selectbox(
        "Jenis konten",
        [
            "Caption Instagram",
            "Konten Facebook",
            "Pesan promosi WhatsApp",
            "Naskah video pendek",
            "Prompt video AI",
            "Deskripsi produk / paket wisata",
            "Follow-up calon klien",
            "Artikel SEO website",
        ],
    )

    brand = st.selectbox(
        "Brand / layanan",
        [
            "Arthama Management",
            "Robinson Cisarua",
            "Villa / penginapan",
            "Paket wisata",
            "Outbound / gathering",
            "Brand lainnya",
        ],
    )

    target = st.text_input(
        "Target audiens",
        placeholder="Contoh: HRD, perusahaan, keluarga, sekolah",
    )
    produk = st.text_area(
        "Informasi produk dan penawaran",
        placeholder=(
            "Masukkan harga, fasilitas, lokasi, tanggal, keunggulan, "
            "dan kontak yang memang ingin dicantumkan."
        ),
        height=130,
    )
    gaya = st.selectbox(
        "Gaya komunikasi",
        [
            "Profesional dan meyakinkan",
            "Ramah dan tidak terlalu menjual",
            "Premium dan elegan",
            "Ceria dan energik",
            "Singkat dan langsung",
        ],
    )
    cta = st.text_input(
        "Ajakan tindakan (CTA)",
        value="Hubungi kami untuk informasi dan reservasi.",
    )

    if st.button("Buat konten", type="primary", use_container_width=True):
        if not produk.strip():
            st.warning("Isi informasi produk terlebih dahulu.")
        else:
            prompt = f"""
Buat materi konten pemasaran untuk Arthama Management atau layanan terkait.

Jenis konten: {jenis}
Brand/layanan: {brand}
Target audiens: {target or "Belum ditentukan"}
Informasi produk:
{produk}

Gaya komunikasi: {gaya}
CTA yang diinginkan: {cta}

Ketentuan:
- Gunakan bahasa Indonesia yang alami dan profesional.
- Jangan menambah harga, fasilitas, diskon, alamat, atau klaim
  yang tidak tercantum dalam informasi produk.
- Buat hasil siap disalin dan digunakan.
- Sesuaikan panjang dan format dengan jenis konten.
- Untuk naskah video, sertakan urutan visual dan voice-over.
- Untuk prompt video AI, jelaskan gerakan kamera, subjek,
  pencahayaan, suasana, dan teks yang harus tampil dengan jelas.
- Untuk artikel SEO, buat judul, meta description, heading,
  dan isi yang mudah dibaca.
"""
            with st.spinner("Studio Konten sedang bekerja..."):
                try:
                    hasil = tanya_gemini(prompt)
                    st.session_state.content_result = hasil
                    st.success("Konten berhasil dibuat.")
                except Exception as exc:
                    tampilkan_error_ai(exc)

    if st.session_state.content_result:
        st.subheader("Hasil Studio Konten")
        st.markdown(st.session_state.content_result)
        st.download_button(
            "Unduh konten sebagai TXT",
            data=st.session_state.content_result.encode("utf-8"),
            file_name="arthama_studio_konten.txt",
            mime="text/plain",
            use_container_width=True,
        )
        if st.button("Kosongkan hasil konten"):
            st.session_state.content_result = ""
            st.rerun()


# ------------------------------------------------------------
# 12. KONEKSI AKUN
# ------------------------------------------------------------

elif page == "Koneksi Akun":
    header(
        "Koneksi Akun",
        "Ringkasan akun kerja dan pemeriksaan konektivitas layanan.",
    )

    st.subheader("Akun dan kanal bisnis")

    akun = [
        ("Gmail", "arthamamanagement@gmail.com", "Email bisnis"),
        ("Instagram", "arthamamanagement", "Kanal media sosial"),
        ("Facebook", "arthamavillapuncak", "Kanal media sosial"),
        ("TikTok", "arthamamanagement", "Kanal media sosial"),
        ("WhatsApp", "087868239249", "Kontak bisnis"),
        ("Google Sheets", "Database calon klien Arthama", "CRM"),
        ("Metricool", "Akun pemasaran", "Perencanaan media sosial"),
    ]

    for nama_akun, identitas, fungsi in akun:
        with st.container(border=True):
            kiri, kanan = st.columns([3, 1])
            with kiri:
                st.markdown(f"**{nama_akun}**")
                st.write(identitas)
                st.caption(fungsi)
            with kanan:
                st.caption("Status akun")
                st.write("Belum diverifikasi")

    st.caption(
        "Daftar di atas merupakan informasi akun yang dicatat dalam aplikasi. "
        "Ini bukan bukti bahwa OAuth, API, atau sinkronisasi otomatis "
        "telah aktif."
    )

    st.divider()
    st.subheader("Tes koneksi CRM")

    st.write(
        "Tes ini mengirim action `list` ke Apps Script yang sudah disiapkan. "
        "Tidak melakukan perubahan data."
    )

    if st.button("Tes koneksi Google Sheets", type="primary"):
        with st.spinner("Memeriksa koneksi CRM..."):
            try:
                result = arthama_api("list")
                st.session_state.connection_test_result = {
                    "success": True,
                    "time": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                    "result": result,
                }
            except Exception as exc:
                st.session_state.connection_test_result = {
                    "success": False,
                    "time": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                    "error": str(exc),
                }

    hasil_tes = st.session_state.connection_test_result
    if hasil_tes:
        st.caption(f"Waktu tes: {hasil_tes['time']}")
        if hasil_tes["success"]:
            st.success("Konektor merespons permintaan list.")
            with st.expander("Detail respons"):
                st.json(hasil_tes["result"])
        else:
            st.error("Tes koneksi gagal.")
            st.code(hasil_tes["error"])

    st.divider()
    st.subheader("Tes layanan Gemini")
    st.write(
        "Tes ini mengirim satu permintaan singkat ke Gemini dan dapat "
        "menggunakan kuota API."
    )

    if st.button("Tes Gemini AI"):
        with st.spinner("Memeriksa layanan Gemini..."):
            try:
                jawaban = tanya_gemini(
                    "Jawab singkat dalam bahasa Indonesia: "
                    "Koneksi AI Arthama sedang diuji."
                )
                st.success("Gemini berhasil memberikan respons.")
                st.write(jawaban)
            except Exception as exc:
                tampilkan_error_ai(exc)


# ------------------------------------------------------------
# 13. PENGATURAN DAN KEAMANAN
# ------------------------------------------------------------

elif page == "Pengaturan & Keamanan":
    header(
        "Pengaturan & Keamanan",
        "Periksa konfigurasi aplikasi dan lindungi akses layanan.",
    )

    st.subheader("Status konfigurasi")

    konfigurasi = [
        ("GEMINI_API_KEY", bool(secret_value("GEMINI_API_KEY"))),
        ("GEMINI_MODEL", bool(secret_value("GEMINI_MODEL", "gemini-2.5-flash"))),
        ("ARTHAMA_WEBAPP_URL", bool(secret_value("ARTHAMA_WEBAPP_URL"))),
        ("ARTHAMA_API_TOKEN", bool(secret_value("ARTHAMA_API_TOKEN"))),
    ]

    for nama, tersedia in konfigurasi:
        kiri, kanan = st.columns([3, 1])
        kiri.write(nama)
        if tersedia:
            kanan.success("Tersedia")
        else:
            kanan.error("Belum diatur")

    st.caption(
        "Aplikasi hanya menampilkan apakah konfigurasi tersedia. "
        "Nilai rahasia tidak ditampilkan."
    )

    st.divider()
    st.subheader("Cara mengatur Streamlit Secrets")

    st.markdown(
        """
        Buka dashboard Streamlit, pilih aplikasi, kemudian buka
        **Settings → Secrets**. Pastikan formatnya seperti berikut:

        ```toml
        GEMINI_API_KEY = "ISI_API_KEY_DI_DASHBOARD"
        GEMINI_MODEL = "gemini-2.5-flash"
        ARTHAMA_WEBAPP_URL = "ISI_URL_APPS_SCRIPT"
        ARTHAMA_API_TOKEN = "ISI_TOKEN_YANG_SAMA_DENGAN_APPS_SCRIPT"
        ```

        Ganti nilai contoh dengan konfigurasi yang benar milikmu.
        Jangan menaruh API key atau token di file Python publik.
        """
    )

    st.divider()
    st.subheader("Praktik keamanan")
    st.markdown(
        """
        - Jangan menyimpan API key di kode yang diunggah ke repository publik.
        - Jangan membagikan token Apps Script atau kredensial akun.
        - Batasi akses editor repository dan dashboard Streamlit.
        - Pertahankan backup aplikasi dan database sebelum perubahan besar.
        - Uji penambahan data CRM menggunakan data percobaan yang jelas.
        - Periksa kuota Gemini di Google AI Studio jika permintaan gagal.
        """
    )

    st.divider()
    st.subheader("Informasi aplikasi")
    st.write(f"Nama aplikasi: {APP_NAME}")
    st.write(f"Versi: {APP_VERSION}")
    st.write("Platform: Streamlit")
    st.write("Database CRM: Google Sheets melalui Apps Script")


# ------------------------------------------------------------
# 14. FOOTER
# ------------------------------------------------------------

st.divider()
st.caption(
    f"{APP_NAME} • Versi {APP_VERSION} • "
    "Gunakan data dan hasil AI dengan verifikasi yang sesuai."
)
