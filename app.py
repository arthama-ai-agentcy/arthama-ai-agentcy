
import streamlit as st
import pandas as pd
from datetime import date
import requests
from google import genai


# ---------- KONFIGURASI HALAMAN ----------
st.set_page_config(
    page_title="Arthama Management — AI Agency",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------- KONEKSI GEMINI ----------
def tanya_gemini(pertanyaan):
    client = genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=pertanyaan,
    )
    return response.text


# ---------- KONEKSI GOOGLE SHEETS ----------
def arthama_api(action, data=None):
    url = st.secrets["ARTHAMA_WEBAPP_URL"]
    token = st.secrets["ARTHAMA_API_TOKEN"]

    payload = {
        "action": action,
        "token": token,
    }

    if data is not None:
        payload["data"] = data

    response = requests.post(
        url,
        json=payload,
        timeout=30,
    )
    response.raise_for_status()

    try:
        return response.json()
    except ValueError:
        raise RuntimeError(
            f"Respons bukan JSON. HTTP {response.status_code}; "
            f"Isi respons: {response.text[:300]}"
        )


# ---------- TEMA ----------
st.markdown("""
<style>
:root {
    --navy: #081426;
    --blue: #2478ff;
    --cyan: #44d7e8;
}
.stApp {
    background: linear-gradient(
        135deg, #071323 0%, #0b1e37 48%, #101d35 100%
    );
    color: #eef5ff;
}
[data-testid="stSidebar"] {
    background: #091629;
    border-right: 1px solid #203755;
}
h1, h2, h3 {
    color: #f3f8ff !important;
}
p, label, .stMarkdown {
    color: #d4e1f5;
}
div[data-testid="stMetric"] {
    background: rgba(20,43,72,.78);
    padding: 16px;
    border: 1px solid #254567;
    border-radius: 16px;
}
div[data-testid="stMetricValue"] {
    color: #ffffff;
}
div.stButton > button {
    border-radius: 10px;
    border: 1px solid #3c8bff;
    background: linear-gradient(90deg,#1d63dc,#168eae);
    color: white;
    font-weight: 600;
}
.panel {
    background: rgba(17,37,64,.86);
    border: 1px solid #254567;
    border-radius: 18px;
    padding: 18px 20px;
    margin-bottom: 12px;
}
.small {
    color: #a9bdd8;
    font-size: .88rem;
}
.pill {
    display: inline-block;
    border: 1px solid #2f668f;
    color: #9cecf4;
    border-radius: 999px;
    padding: 3px 10px;
    font-size: .78rem;
    margin-right: 5px;
}
.robot {
    font-size: 2rem;
}
hr {
    border-color: #25405e;
}
</style>
""", unsafe_allow_html=True)


# ---------- DATA DEMO ----------
if "leads" not in st.session_state:
    st.session_state.leads = pd.DataFrame([
        {
            "Perusahaan": "PT Guhring Indonesia",
            "Kota": "Bekasi",
            "Potensi": "Corporate outing / team building",
            "Status": "Email terkirim",
            "Follow-up": "2026-10-30",
            "Estimasi (Rp)": 25000000,
        },
        {
            "Perusahaan": "PT Tigaraksa Satria Tbk",
            "Kota": "Jakarta",
            "Potensi": "Family gathering",
            "Status": "Prospek baru",
            "Follow-up": "2026-10-29",
            "Estimasi (Rp)": 40000000,
        },
        {
            "Perusahaan": "Cargill Indonesia",
            "Kota": "Jakarta",
            "Potensi": "Meeting & team building",
            "Status": "Riset awal",
            "Follow-up": "2026-11-02",
            "Estimasi (Rp)": 30000000,
        },
        {
            "Perusahaan": "PT Summarecon Agung Tbk",
            "Kota": "Bekasi",
            "Potensi": "Employee gathering",
            "Status": "Prospek baru",
            "Follow-up": "2026-11-03",
            "Estimasi (Rp)": 50000000,
        },
        {
            "Perusahaan": "PT Misuba Guna Indonesia",
            "Kota": "Bogor",
            "Potensi": "Outbound",
            "Status": "Riset awal",
            "Follow-up": "2026-11-04",
            "Estimasi (Rp)": 20000000,
        },
    ])

if "content" not in st.session_state:
    st.session_state.content = pd.DataFrame([
        {
            "Tanggal": "2026-10-27",
            "Kanal": "Instagram + Facebook",
            "Konten": "Promo Inflatable Games Team Building",
            "Status": "Draft / perlu konfirmasi",
        },
        {
            "Tanggal": "2026-10-29",
            "Kanal": "Instagram",
            "Konten": "Paket Lembang Bandung 2D1N",
            "Status": "Rencana",
        },
        {
            "Tanggal": "2026-10-31",
            "Kanal": "Facebook",
            "Konten": "Promo villa weekday satu jutaan",
            "Status": "Rencana",
        },
    ])

if "connections" not in st.session_state:
    st.session_state.connections = {}

if "tasks" not in st.session_state:
    st.session_state.tasks = [
        {
            "Tugas": "Cek respons penawaran PT Guhring Indonesia",
            "Divisi": "AI Sales",
            "Prioritas": "Tinggi",
            "Status": "Menunggu tindakan manusia",
        },
        {
            "Tugas": "Siapkan caption paket Lembang",
            "Divisi": "AI Marketing",
            "Prioritas": "Sedang",
            "Status": "Siap dikerjakan",
        },
        {
            "Tugas": "Lengkapi kontak publik prospek",
            "Divisi": "AI Research",
            "Prioritas": "Sedang",
            "Status": "Perlu riset",
        },
    ]


# ---------- SIDEBAR / NAVIGASI ----------
with st.sidebar:
    st.markdown("## 🤖 ARTHAMA")
    st.markdown(
        "<span class='small'>MANAGEMENT · AI AGENCY</span>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    page = st.radio(
        "RUANG KERJA",
        [
            "Command Center",
            "Divisi Robot AI",
            "Sales CRM",
            "Studio Konten",
            "Koneksi Akun",
            "Pengaturan & Keamanan",
        ],
    )

    st.markdown("---")
    st.markdown(
        "<span class='pill'>PROTOTIPE</span> "
        "<span class='pill'>MODE AMAN</span>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Integrasi eksternal hanya aktif jika telah disiapkan "
        "dan diuji secara resmi."
    )

    if st.button("🔌 Tes Koneksi Google Sheets"):
        try:
            hasil_tes = arthama_api("list")
            st.success("Permintaan berhasil dijalankan.")
            st.json(hasil_tes)
        except Exception:
            st.error(
                "Tes gagal. Periksa konfigurasi dan koneksi."
            )


# ---------- HEADER ----------
st.markdown("# ARTHAMA MANAGEMENT — AI AGENCY")
st.markdown(
    "**Kantor virtual untuk pemasaran, penjualan, dan operasional bisnis.**"
)
st.markdown(
    "<span class='pill'>BLUE FUTURE OFFICE</span>"
    "<span class='pill'>HUMAN APPROVAL</span>"
    "<span class='pill'>LOW-COST FIRST</span>",
    unsafe_allow_html=True,
)


# ==================================================
# 1. COMMAND CENTER
# ==================================================
if page == "Command Center":
    st.markdown("## 🛰️ Command Center")
    st.markdown(
        "<div class='panel'><b>Selamat datang di kantor virtual Arthama.</b>"
        "<br><span class='small'>Pantau prospek, konten, tugas, dan "
        "kesiapan koneksi. Angka demo bukan aktivitas live.</span></div>",
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Prospek demo", len(st.session_state.leads))
    c2.metric("Konten terencana", len(st.session_state.content))
    c3.metric("Tugas terbuka", len(st.session_state.tasks))
    c4.metric(
        "Status tercatat terhubung",
        sum(
            v == "Terhubung (manual)"
            for v in st.session_state.connections.values()
        ),
    )

    st.markdown("### 🏢 Denah divisi")
    rooms = [
        ("🧭", "AI Director", "Prioritas dan pembagian tugas."),
        ("📣", "AI Marketing", "Caption dan konsep promosi."),
        ("🎯", "AI Sales", "Prospek dan tahapan penjualan."),
        ("🔎", "AI Research", "Riset informasi bisnis publik."),
        ("💬", "AI Customer Care", "Persiapan balasan pelanggan."),
        ("📊", "AI Analyst", "Analisis data yang tersedia."),
    ]

    cols = st.columns(3)
    for i, (emoji, title, desc) in enumerate(rooms):
        with cols[i % 3]:
            st.markdown(
                f"<div class='panel'><div class='robot'>{emoji}</div>"
                f"<h3>{title}</h3><span class='small'>{desc}</span></div>",
                unsafe_allow_html=True,
            )

    st.markdown("### 📌 Daftar tugas")
    st.dataframe(
        pd.DataFrame(st.session_state.tasks),
        use_container_width=True,
        hide_index=True,
    )


# ==================================================
# 2. DIVISI ROBOT AI
# ==================================================
elif page == "Divisi Robot AI":
    st.markdown("## 🤖 AI Sales Agent Arthama")
    st.caption(
        "Asisten AI untuk membantu penawaran dan penjualan Arthama Management."
    )

    pertanyaan = st.text_area(
        "Apa yang ingin kamu kerjakan?",
        placeholder=(
            "Contoh: Buat pesan WhatsApp penawaran "
            "gathering untuk perusahaan 100 peserta."
        ),
        key="pertanyaan_ai_arthama",
    )

    if st.button("✨ Tanya Gemini", type="primary"):
        if not pertanyaan.strip():
            st.warning("Masukkan pertanyaan terlebih dahulu.")
        else:
            try:
                with st.spinner("Gemini sedang menyusun jawaban..."):
                    jawaban = tanya_gemini(pertanyaan)

                if jawaban:
                    st.markdown("### Hasil dari Gemini")
                    st.write(jawaban)
                else:
                    st.warning("Gemini tidak mengembalikan jawaban.")

            except Exception as e:
                pesan_error = str(e)

                if "503" in pesan_error or "UNAVAILABLE" in pesan_error:
                    st.warning(
                        "Server Gemini sedang sibuk. Coba lagi nanti."
                    )
                elif "429" in pesan_error or "RESOURCE_EXHAUSTED" in pesan_error:
                    st.warning(
                        "Kuota Gemini tercapai. Tunggu hingga kuota tersedia."
                    )
                else:
                    st.error("Gemini gagal memberikan jawaban.")
                    st.code(
                        f"{type(e).__name__}: {pesan_error}"
                    )


# ==================================================
# 3. SALES CRM — GOOGLE SHEETS
# ==================================================
elif page == "Sales CRM":
    st.markdown("## 🎯 Sales CRM — Database Prospek")
    st.caption(
        "Data dibaca dan ditambahkan melalui konektor Google Sheets "
        "yang sudah disiapkan."
    )

    try:
        hasil = arthama_api("list")

        if not hasil.get("success"):
            st.error("Database belum berhasil dibaca.")
            st.json(hasil)
        else:
            rows = hasil.get("rows", [])

            if rows:
                headers = [str(h).strip() for h in rows[0]]
                data_rows = rows[1:]
                jumlah_kolom = len(headers)
                data_bersih = []

                for row_data in data_rows:
                    row_data = list(row_data)
                    row_data += [""] * max(
                        0, jumlah_kolom - len(row_data)
                    )
                    data_bersih.append(row_data[:jumlah_kolom])

                df = pd.DataFrame(
                    data_bersih,
                    columns=headers,
                )

                st.success(
                    f"Koneksi berhasil. Data terbaca: {len(df)} baris."
                )
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                )
                st.download_button(
                    "⬇️ Unduh database CSV",
                    df.to_csv(index=False).encode("utf-8-sig"),
                    "arthama_database_prospek.csv",
                    "text/csv",
                )
            else:
                st.warning("Google Sheets belum berisi data.")

    except Exception as e:
        st.error("Gagal mengambil database Google Sheets.")
        st.code(str(e))

    st.divider()
    st.markdown("### ➕ Tambah prospek baru")

    with st.form("add_lead_permanent"):
        nama = st.text_input("Nama klien")
        whatsapp = st.text_input("Nomor WhatsApp")
        perusahaan = st.text_input("Nama perusahaan")
        kebutuhan = st.text_input("Kebutuhan acara")
        tanggal_acara = st.date_input(
            "Tanggal acara",
            value=date.today(),
        )
        jumlah = st.number_input(
            "Jumlah peserta",
            min_value=0,
            step=1,
        )
        budget = st.text_input("Budget (contoh: Rp15.000.000)")
        status = st.selectbox(
            "Status prospek",
            [
                "Prospek baru",
                "Riset awal",
                "Sudah dihubungi",
                "Menunggu respons",
                "Tertarik",
                "Survei",
                "DP masuk",
                "Tidak lanjut",
            ],
        )
        tindak_lanjut = st.text_input("Tindak lanjut berikutnya")
        catatan = st.text_area("Catatan")

        submitted = st.form_submit_button("💾 Simpan ke Google Sheets")

        if submitted:
            if not nama.strip() and not perusahaan.strip():
                st.error(
                    "Isi minimal nama klien atau nama perusahaan."
                )
            else:
                data_prospek = {
                    "tanggalMasuk": str(date.today()),
                    "namaKlien": nama.strip(),
                    "whatsapp": whatsapp.strip(),
                    "perusahaan": perusahaan.strip(),
                    "kebutuhanAcara": kebutuhan.strip(),
                    "tanggalAcara": str(tanggal_acara),
                    "jumlahPeserta": int(jumlah),
                    "budget": budget.strip(),
                    "statusProspek": status,
                    "tindakLanjut": tindak_lanjut.strip(),
                    "catatan": catatan.strip(),
                }

                try:
                    hasil_simpan = arthama_api(
                        "add",
                        data_prospek,
                    )

                    if hasil_simpan.get("success"):
                        st.success(
                            "Prospek berhasil dikirim ke Google Sheets."
                        )
                        st.rerun()
                    else:
                        st.error(
                            "Data belum dikonfirmasi tersimpan."
                        )
                        st.json(hasil_simpan)

                except Exception as e:
                    st.error("Gagal menyimpan prospek.")
                    st.code(str(e))


# ==================================================
# 4. STUDIO KONTEN
# ==================================================
elif page == "Studio Konten":
    st.markdown("## 🎨 Studio Konten")
    st.caption(
        "Perencanaan konten. Publikasi otomatis belum diaktifkan."
    )

    edited = st.data_editor(
        st.session_state.content,
        num_rows="dynamic",
        use_container_width=True,
        key="content_editor",
    )
    st.session_state.content = edited

    st.download_button(
        "⬇️ Unduh kalender konten CSV",
        st.session_state.content.to_csv(
            index=False
        ).encode("utf-8-sig"),
        "arthama_kalender_konten.csv",
        "text/csv",
    )

    st.markdown("### Buat brief konten baru")
    with st.form("content_brief"):
        topic = st.text_input(
            "Tema promosi",
            placeholder="Paket gathering perusahaan 2D1N",
        )
        channel = st.multiselect(
            "Kanal",
            ["Instagram", "Facebook", "TikTok"],
            default=["Instagram", "Facebook"],
        )
        goal = st.selectbox(
            "Tujuan",
            [
                "Mendapatkan pertanyaan harga",
                "Mendapatkan reservasi",
                "Membangun kepercayaan",
                "Mencari klien perusahaan",
            ],
        )
        audience = st.text_input(
            "Target audiens",
            placeholder="HRD, GA, panitia gathering, keluarga",
        )

        if st.form_submit_button("Simpan brief"):
            if topic.strip():
                newrow = pd.DataFrame([{
                    "Tanggal": str(date.today()),
                    "Kanal": " + ".join(channel),
                    "Konten": (
                        topic.strip()
                        + " | Tujuan: " + goal
                        + " | Target: " + audience
                    ),
                    "Status": "Brief baru",
                }])

                st.session_state.content = pd.concat(
                    [st.session_state.content, newrow],
                    ignore_index=True,
                )
                st.success("Brief tersimpan selama sesi ini.")
                st.rerun()
            else:
                st.error("Tema promosi harus diisi.")


# ==================================================
# 5. KONEKSI AKUN — MENU TERPISAH
# ==================================================
elif page == "Koneksi Akun":
    st.markdown("## 🔌 Koneksi Akun")
    st.info(
        "Informasi akun resmi Arthama Management. "
        "Status pencatatan bukan verifikasi koneksi otomatis."
    )

    details = {
        "Gmail": {
            "description": "Email resmi untuk komunikasi dan penawaran.",
            "account": "arthamamanagement@gmail.com",
            "url": "https://mail.google.com/",
        },
        "Instagram": {
            "description": "Akun promosi dan dokumentasi kegiatan.",
            "account": "@arthamamanagement",
            "url": "https://www.instagram.com/arthamamanagement/",
        },
        "Facebook Page": {
            "description": "Halaman promosi dan komunikasi pelanggan.",
            "account": "arthamavillapuncak",
            "url": "https://www.facebook.com/arthamavillapuncak",
        },
        "TikTok": {
            "description": "Video promosi dan dokumentasi kegiatan.",
            "account": "@arthamamanagement",
            "url": "https://www.tiktok.com/@arthamamanagement",
        },
        "Metricool": {
            "description": "Pengelolaan dan penjadwalan konten.",
            "account": "Belum diatur",
            "url": "https://metricool.com/",
        },
        "Google Sheets": {
            "description": "Database utama calon klien.",
            "account": "Database CRM sudah digunakan",
            "url": None,
        },
        "WhatsApp Business": {
            "description": "Kontak komunikasi dan reservasi pelanggan.",
            "account": "087868239249",
            "url": "https://wa.me/6287868239249",
        },
    }

    status_options = [
        "Belum diperiksa",
        "Direncanakan",
        "Terhubung (manual)",
    ]

    for service, item in details.items():
        with st.container(border=True):
            st.markdown(f"### {service}")
            st.caption(item["description"])
            st.write(f"**Akun:** {item['account']}")

            if item["url"]:
                st.markdown(f"[Buka {service}]({item['url']})")

            if service == "Google Sheets":
                st.success(
                    "Database CRM tetap menggunakan konektor yang sudah ada."
                )

            current = st.session_state.connections.get(
                service,
                "Belum diperiksa",
            )
            if current not in status_options:
                current = "Belum diperiksa"

            choice = st.selectbox(
                "Status pencatatan",
                status_options,
                index=status_options.index(current),
                key=f"conn_{service}",
            )

            if st.button(
                f"Simpan status {service}",
                key=f"save_{service}",
            ):
                st.session_state.connections[service] = choice
                st.success(
                    "Status pencatatan diperbarui. "
                    "Koneksi eksternal belum diverifikasi otomatis."
                )

    st.markdown("### 📋 Tahapan integrasi")
    st.write("1. Pertahankan koneksi Google Sheets yang sudah berjalan.")
    st.write("2. Evaluasi integrasi Gmail.")
    st.write("3. Evaluasi integrasi resmi Meta untuk Instagram dan Facebook.")
    st.write("4. Periksa opsi integrasi TikTok dan Metricool.")
    st.write("5. Evaluasi WhatsApp Business Platform jika diperlukan.")

    st.caption(
        "Status pencatatan saat ini menggunakan session state Streamlit; "
        "status dapat hilang saat sesi berakhir."
    )


# ==================================================
# 6. PENGATURAN & KEAMANAN
# ==================================================
elif page == "Pengaturan & Keamanan":
    st.markdown("## 🛡️ Pengaturan & Keamanan")

    st.markdown("""
    <div class='panel'>
    <h3>Prinsip keamanan</h3>
    <ul>
      <li>Jangan simpan kata sandi akun sosial di kode aplikasi.</li>
      <li>Gunakan OAuth atau otorisasi resmi untuk integrasi.</li>
      <li>Aktifkan autentikasi dua faktor pada akun penting.</li>
      <li>Minta persetujuan manusia sebelum pesan dikirim.</li>
      <li>Hormati persetujuan penerima dan permintaan berhenti.</li>
      <li>Batasi akses ke data prospek.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Status kemampuan")
    st.dataframe(
        pd.DataFrame([
            {
                "Fitur": "Dashboard dan navigasi",
                "Status": "Prototipe",
            },
            {
                "Fitur": "CRM Google Sheets",
                "Status": "Menggunakan konektor yang sudah tersedia",
            },
            {
                "Fitur": "Ekspor CSV",
                "Status": "Tersedia",
            },
            {
                "Fitur": "Kalender dan brief konten",
                "Status": "Data sesi aplikasi",
            },
            {
                "Fitur": "Login multi-pengguna",
                "Status": "Belum tersedia",
            },
            {
                "Fitur": "Publikasi media sosial otomatis",
                "Status": "Belum terintegrasi",
            },
            {
                "Fitur": "Email / WhatsApp otomatis",
                "Status": "Belum terintegrasi",
            },
            {
                "Fitur": "Robot AI berjalan mandiri",
                "Status": "Belum tersedia",
            },
        ]),
        use_container_width=True,
        hide_index=True,
    )


# ---------- FOOTER ----------
st.markdown("---")
st.markdown(
    "<div class='small'>ARTHAMA MANAGEMENT · AI AGENCY | "
    "Prototype v0.1 · Local data</div>",
    unsafe_allow_html=True,
)
