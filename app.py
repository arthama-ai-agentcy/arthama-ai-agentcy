import streamlit as st
import pandas as pd
from datetime import date, datetime

import requests

import google.generativeai as genai

# Menghubungkan Gemini dengan API key dari Streamlit Secrets
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def tanya_gemini(pertanyaan):
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(pertanyaan)
    return response.text

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
            f"Respons bukan JSON. "
            f"HTTP {response.status_code}; "
            f"Isi respons: {response.text[:300]}"
        )
st.set_page_config(
    page_title="Arthama Management — AI Agency",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

if st.sidebar.button("🔌 Tes Koneksi Google Sheets"):
    try:
        hasil = arthama_api("list")
        st.sidebar.success("Koneksi berhasil!")
        st.write("Hasil tes koneksi:")
        st.json(hasil)
    except Exception as e:
        st.sidebar.error("Koneksi gagal.")
        st.error(str(e))
# ---------- Theme ----------
st.markdown("""
<style>
:root { --navy:#081426; --blue:#2478ff; --cyan:#44d7e8; --ink:#17233b; }
.stApp { background: linear-gradient(135deg, #071323 0%, #0b1e37 48%, #101d35 100%); color: #eef5ff; }
[data-testid="stSidebar"] { background: #091629; border-right: 1px solid #203755; }
h1,h2,h3 { color: #f3f8ff !important; }
p, label, .stMarkdown, [data-testid="stMetricLabel"] { color: #d4e1f5; }
div[data-testid="stMetric"] { background: rgba(20,43,72,.78); padding: 16px; border: 1px solid #254567; border-radius: 16px; }
div[data-testid="stMetricValue"] { color: #ffffff; }
div.stButton > button { border-radius: 10px; border: 1px solid #3c8bff; background: linear-gradient(90deg,#1d63dc,#168eae); color:white; font-weight:600; }
div.stButton > button:hover { border-color:#6de4ff; color:white; }
.panel { background: rgba(17,37,64,.86); border:1px solid #254567; border-radius:18px; padding:18px 20px; margin-bottom:12px; }
.small { color:#a9bdd8; font-size: .88rem; }
.pill { display:inline-block; border:1px solid #2f668f; color:#9cecf4; border-radius:999px; padding:3px 10px; font-size:.78rem; margin-right:5px; }
.robot { font-size:2rem; }
hr { border-color:#25405e; }
</style>
""", unsafe_allow_html=True)

# ---------- Demo data / session state ----------
if "leads" not in st.session_state:
    st.session_state.leads = pd.DataFrame([
        {"Perusahaan":"PT Guhring Indonesia","Kota":"Bekasi","Potensi":"Corporate outing / team building","Status":"Email terkirim","Follow-up":"2026-10-30","Estimasi (Rp)":25000000},
        {"Perusahaan":"PT Tigaraksa Satria Tbk","Kota":"Jakarta","Potensi":"Family gathering","Status":"Prospek baru","Follow-up":"2026-10-29","Estimasi (Rp)":40000000},
        {"Perusahaan":"Cargill Indonesia","Kota":"Jakarta","Potensi":"Meeting & team building","Status":"Riset awal","Follow-up":"2026-11-02","Estimasi (Rp)":30000000},
        {"Perusahaan":"PT Summarecon Agung Tbk","Kota":"Bekasi","Potensi":"Employee gathering","Status":"Prospek baru","Follow-up":"2026-11-03","Estimasi (Rp)":50000000},
        {"Perusahaan":"PT Misuba Guna Indonesia","Kota":"Bogor","Potensi":"Outbound","Status":"Riset awal","Follow-up":"2026-11-04","Estimasi (Rp)":20000000},
    ])
if "content" not in st.session_state:
    st.session_state.content = pd.DataFrame([
        {"Tanggal":"2026-10-27","Kanal":"Instagram + Facebook","Konten":"Promo Inflatable Games Team Building","Status":"Draft / perlu konfirmasi"},
        {"Tanggal":"2026-10-29","Kanal":"Instagram","Konten":"Paket Lembang Bandung 2D1N","Status":"Rencana"},
        {"Tanggal":"2026-10-31","Kanal":"Facebook","Konten":"Promo villa weekday satu jutaan","Status":"Rencana"},
    ])
if "connections" not in st.session_state:
    st.session_state.connections = {
        "Gmail": "Belum dihubungkan",
        "Instagram": "Belum dihubungkan",
        "Facebook Page": "Belum dihubungkan",
        "TikTok": "Belum dihubungkan",
        "Metricool": "Belum dihubungkan",
        "Google Sheets": "Belum dihubungkan",
        "WhatsApp Business": "Belum dihubungkan",
    }
if "tasks" not in st.session_state:
    st.session_state.tasks = [
        {"Tugas":"Cek respons penawaran PT Guhring Indonesia","Divisi":"AI Sales","Prioritas":"Tinggi","Status":"Menunggu tindakan manusia"},
        {"Tugas":"Siapkan caption paket Lembang","Divisi":"AI Marketing","Prioritas":"Sedang","Status":"Siap dikerjakan"},
        {"Tugas":"Lengkapi kontak publik prospek","Divisi":"AI Research","Prioritas":"Sedang","Status":"Perlu riset"},
    ]

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🤖 ARTHAMA")
    st.markdown("<span class='small'>MANAGEMENT · AI AGENCY</span>", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio(
        "RUANG KERJA",
        ["Command Center", "Divisi Robot AI", "Sales CRM", "Studio Konten", "Koneksi Akun", "Pengaturan & Keamanan"],
        label_visibility="visible",
    )
    st.markdown("---")
    st.markdown("<span class='pill'>PROTOTIPE</span> <span class='pill'>MODE AMAN</span>", unsafe_allow_html=True)
    st.caption("Data contoh tersimpan selama sesi aplikasi. Belum tersambung ke akun eksternal.")

# ---------- Header ----------
st.markdown("# ARTHAMA MANAGEMENT — AI AGENCY")
st.markdown("**Kantor virtual untuk pemasaran, penjualan, dan operasional bisnis.**")
st.markdown("<span class='pill'>BLUE FUTURE OFFICE</span><span class='pill'>HUMAN APPROVAL</span><span class='pill'>LOW-COST FIRST</span>", unsafe_allow_html=True)

if page == "Command Center":
    st.markdown("## 🛰️ Command Center")
    st.markdown("<div class='panel'><b>Selamat datang di kantor virtual Arthama.</b><br><span class='small'>Pantau pekerjaan, prospek, konten, dan koneksi layanan dari satu dashboard. Angka di bawah merupakan data demo awal, bukan aktivitas live dari akun eksternal.</span></div>", unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Prospek tercatat", len(st.session_state.leads), "+5 contoh")
    c2.metric("Konten terencana", len(st.session_state.content), "rencana demo")
    c3.metric("Tugas terbuka", len([t for t in st.session_state.tasks if "selesai" not in t["Status"].lower()]), "perlu ditinjau")
    c4.metric("Koneksi aktif", sum(v == "Terhubung (manual)" for v in st.session_state.connections.values()), "belum live")
    st.markdown("### 🏢 Denah divisi")
    cols = st.columns(3)
    rooms = [
        ("🧭","AI Director","Mengatur prioritas, pembagian tugas, dan laporan."),
        ("📣","AI Marketing","Menyusun caption, kalender konten, dan konsep promo."),
        ("🎯","AI Sales","Mengelola prospek, penawaran, dan tahapan penjualan."),
        ("🔎","AI Research","Mencari perusahaan dan informasi bisnis publik."),
        ("💬","AI Customer Care","Menyiapkan balasan untuk calon pelanggan."),
        ("📊","AI Analyst","Menganalisis hasil kampanye setelah data tersedia."),
    ]
    for i,(emoji,title,desc) in enumerate(rooms):
        with cols[i%3]:
            st.markdown(f"<div class='panel'><div class='robot'>{emoji}</div><h3>{title}</h3><span class='small'>{desc}</span></div>", unsafe_allow_html=True)
    st.markdown("### 📌 Prioritas berikutnya")
    st.dataframe(pd.DataFrame(st.session_state.tasks), use_container_width=True, hide_index=True)
    st.info("Prototipe ini belum menjalankan robot secara mandiri. Modul saat ini adalah ruang kerja, pencatatan, dan simulasi alur. Integrasi nyata harus disambungkan dan diuji satu per satu.")


elif page == "AI Sales Agent":
    st.markdown("## 🤖 AI Sales Agent Arthama")
    st.caption(
        "Asisten AI untuk membantu penawaran dan penjualan Arthama Management."
    )

    pertanyaan = st.text_area(
        "Apa yang ingin kamu kerjakan?",
        placeholder=(
            "Contoh: Buatkan pesan WhatsApp penawaran "
            "paket gathering untuk perusahaan 100 peserta."
        )
    )

    if st.button("✨ Tanya Gemini", type="primary"):
        if pertanyaan.strip():
            try:
                with st.spinner("Gemini sedang menyusun jawaban..."):
                    jawaban = tanya_gemini(pertanyaan)

                st.markdown("### Hasil dari Gemini")
                st.write(jawaban)

            except Exception as e:
                st.error("Gemini belum bisa memberikan jawaban.")
                st.caption(
                    "Periksa nama model, kuota gratis, dan pengaturan API key."
                )
        else:
            st.warning("Masukkan pertanyaan terlebih dahulu.")


elif page == "Sales CRM":
    st.markdown("## 🎯 Sales CRM — Database Prospek")
    st.caption(
        "Database prospek Arthama Management yang terhubung "
        "ke Google Sheets."
    )

    # Baca database dari Google Sheets
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

                # Pertahankan jumlah kolom sesuai header dari Sheet
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
                    columns=headers
                )

                st.success(
                    f"Koneksi aktif. Data terbaca: {len(df)} baris."
                )

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

                st.download_button(
                    "⬇️ Unduh database CSV",
                    df.to_csv(index=False).encode("utf-8-sig"),
                    "arthama_database_prospek.csv",
                    "text/csv"
                )
            else:
                st.warning("Google Sheets belum berisi data.")

    except Exception as e:
        st.error("Gagal mengambil database Google Sheets.")
        st.code(str(e))

    st.divider()
    st.markdown("### ➕ Tambah prospek baru")
    st.caption(
        "Isi informasi calon klien. Data akan dikirim ke Google Sheets."
    )

    with st.form("add_lead_permanent"):
        nama = st.text_input("Nama klien")
        whatsapp = st.text_input("Nomor WhatsApp")
        perusahaan = st.text_input("Nama perusahaan")
        kebutuhan = st.text_input("Kebutuhan acara")
        tanggal_acara = st.date_input(
            "Tanggal acara",
            value=date.today()
        )
        jumlah = st.number_input(
            "Jumlah peserta",
            min_value=0,
            step=1
        )
        budget = st.text_input(
            "Budget (contoh: Rp15.000.000)"
        )
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
                "Tidak lanjut"
            ]
        )
        tindak_lanjut = st.text_input(
            "Tindak lanjut berikutnya"
        )
        catatan = st.text_area("Catatan")

        submitted = st.form_submit_button(
            "💾 Simpan ke Google Sheets"
        )

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
                    "catatan": catatan.strip()
                }

                try:
                    hasil_simpan = arthama_api(
                        "add",
                        data_prospek
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
                    st.error(
                        "Gagal menyimpan prospek. "
                        "Periksa koneksi Apps Script."
                    )
                    st.code(str(e))

elif page == "Studio Konten":
    st.markdown("## 🎨 Studio Konten")
    st.caption("Perencanaan konten; publikasi belum otomatis. Jangan menganggap status rencana sebagai posting terjadwal di platform.")
    edited = st.data_editor(st.session_state.content, num_rows="dynamic", use_container_width=True, key="content_editor")
    st.session_state.content = edited
    st.download_button("⬇️ Unduh kalender konten CSV", st.session_state.content.to_csv(index=False).encode("utf-8-sig"), "arthama_kalender_konten.csv", "text/csv")
    st.markdown("### Buat brief konten baru")
    with st.form("content_brief"):
        topic = st.text_input("Tema promosi", placeholder="Contoh: Paket gathering perusahaan 2D1N")
        channel = st.multiselect("Kanal", ["Instagram","Facebook","TikTok"], default=["Instagram","Facebook"])
        goal = st.selectbox("Tujuan", ["Mendapatkan pertanyaan harga","Mendapatkan reservasi","Membangun kepercayaan","Mencari klien perusahaan"])
        audience = st.text_input("Target audiens", placeholder="HRD, GA, panitia gathering, keluarga")
        if st.form_submit_button("Simpan brief"):
            if topic.strip():
                newrow = pd.DataFrame([{"Tanggal":str(date.today()),"Kanal":" + ".join(channel),"Konten":topic.strip()+" | Tujuan: "+goal+" | Target: "+audience,"Status":"Brief baru"}])
                st.session_state.content = pd.concat([st.session_state.content,newrow],ignore_index=True)
                st.success("Brief konten tersimpan selama sesi ini.")
                st.rerun()
            else:
                st.error("Tema promosi harus diisi.")

elif page == "Koneksi Akun":
    st.markdown("## 🔌 Koneksi Akun")
    st.warning("Keamanan: jangan masukkan kata sandi, kode OTP, token API, atau recovery code ke formulir ini. Prototipe ini belum membuat koneksi sungguhan.")
    details = {
        "Gmail":"Email pusat, draf penawaran, dan pengingat. Integrasi resmi/OAuth atau Apps Script diperlukan.",
        "Instagram":"Publikasi dan insight memerlukan akun profesional, izin Meta, dan integrasi yang didukung.",
        "Facebook Page":"Penjadwalan dan insight memerlukan akses Page dan koneksi platform yang sah.",
        "TikTok":"Integrasi tergantung dukungan platform dan izin aplikasi yang tersedia.",
        "Metricool":"Hubungkan lewat proses otorisasi resmi Metricool; jadwal harus dikonfirmasi di Metricool.",
        "Google Sheets":"Bisa menjadi CRM utama; integrasi perlu Google Apps Script atau OAuth/API.",
        "WhatsApp Business":"Gunakan aplikasi untuk balasan manual; otomatisasi outbound memerlukan platform/API resmi dan persetujuan penerima.",
    }
    for service, description in details.items():
        with st.container(border=True):
            left,right = st.columns([3,2])
            with left:
                st.markdown(f"### {service}")
                st.caption(description)
            with right:
                current = st.session_state.connections.get(service, "Belum dihubungkan")
                st.write(f"Status: **{current}**")
                choice = st.selectbox("Status pencatatan", ["Belum dihubungkan","Direncanakan","Terhubung (manual)"], index=["Belum dihubungkan","Direncanakan","Terhubung (manual)"].index(current), key=f"conn_{service}")
                if st.button(f"Simpan status {service}", key=f"save_{service}"):
                    st.session_state.connections[service] = choice
                    st.success("Status lokal diperbarui; ini bukan autentikasi ke layanan.")
    st.markdown("### Urutan koneksi yang disarankan")
    st.write("1. Email pusat → 2. Google Sheets CRM → 3. Meta/Instagram → 4. Metricool → 5. TikTok → 6. WhatsApp API bila diperlukan.")

elif page == "Pengaturan & Keamanan":
    st.markdown("## 🛡️ Pengaturan & Keamanan")
    st.markdown("""
    <div class='panel'>
    <h3>Prinsip keamanan</h3>
    <ul>
      <li>Jangan simpan kata sandi akun sosial di aplikasi prototipe.</li>
      <li>Gunakan OAuth atau halaman otorisasi resmi saat integrasi tersedia.</li>
      <li>Aktifkan autentikasi dua faktor pada akun penting.</li>
      <li>Mulai dengan persetujuan manusia sebelum email atau pesan dikirim.</li>
      <li>Hormati opt-out dan jangan mengirim pesan WhatsApp tanpa izin yang sesuai.</li>
      <li>Simpan data prospek seperlunya dan batasi aksesnya.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("### Status kemampuan")
    st.dataframe(pd.DataFrame([
        {"Fitur":"Dashboard dan navigasi","Status":"Berfungsi dalam prototipe"},
        {"Fitur":"Tambah/edit CRM","Status":"Berfungsi selama sesi aplikasi"},
        {"Fitur":"Ekspor CSV","Status":"Berfungsi"},
        {"Fitur":"Kalender dan brief konten","Status":"Berfungsi selama sesi aplikasi"},
        {"Fitur":"Login multi-pengguna","Status":"Belum tersedia"},
        {"Fitur":"Simpan data permanen / database","Status":"Belum tersedia"},
        {"Fitur":"Publikasi media sosial otomatis","Status":"Belum terintegrasi"},
        {"Fitur":"Kirim email / WhatsApp otomatis","Status":"Belum terintegrasi"},
        {"Fitur":"Robot AI bekerja mandiri di background","Status":"Belum tersedia"},
    ]), use_container_width=True, hide_index=True)
    st.caption("Saran untuk versi berikutnya: simpan data ke Google Sheets, lalu tambahkan OAuth dan automasi terukur. Jangan menambahkan kredensial langsung ke kode.")

st.markdown("---")
st.markdown("<div class='small'>ARTHAMA MANAGEMENT · AI AGENCY | Prototype v0.1 · Local/demo data only</div>", unsafe_allow_html=True)
