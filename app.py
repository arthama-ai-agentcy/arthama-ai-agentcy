import os
import json
from datetime import date, datetime

import pandas as pd
import requests
import streamlit as st

# =========================================================
# ARTHAMA MANAGEMENT — AI AGENCY
# File: app.py
# =========================================================
st.set_page_config(
    page_title="Arthama Management | AI Agency",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Secrets / connection helpers ----------
def get_secret(name: str, default: str = "") -> str:
    """Read Streamlit secrets safely, then environment variables."""
    try:
        value = st.secrets.get(name, default)
        if value:
            return str(value).strip()
    except Exception:
        pass
    return os.getenv(name, default).strip()


def arthama_api(action: str, data=None):
    """Call the existing Arthama Apps Script connector."""
    url = get_secret("ARTHAMA_WEBAPP_URL")
    token = get_secret("ARTHAMA_API_TOKEN")
    if not url or not token:
        raise RuntimeError(
            "Koneksi Google Sheets belum disetel. Tambahkan "
            "ARTHAMA_WEBAPP_URL dan ARTHAMA_API_TOKEN di Streamlit Secrets."
        )
    payload = {"action": action, "token": token}
    if data is not None:
        payload["data"] = data
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    try:
        result = response.json()
    except ValueError as exc:
        raise RuntimeError(
            f"Respons konektor bukan JSON (HTTP {response.status_code}): "
            f"{response.text[:250]}"
        ) from exc
    if isinstance(result, dict) and str(result.get("status", "")).lower() == "error":
        raise RuntimeError(str(result.get("message", "Konektor mengembalikan error.")))
    return result


def get_gemini_client():
    api_key = get_secret("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY belum ada di Streamlit Secrets. "
            "Jangan tempel API key ke kode atau chat."
        )
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except ImportError as exc:
        raise RuntimeError(
            "Pustaka google-genai belum terpasang. Periksa requirements.txt "
            "lalu tunggu aplikasi selesai reboot."
        ) from exc


def ask_gemini(prompt: str, department: str = "Asisten Arthama") -> str:
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Instruksi belum diisi.")
    client = get_gemini_client()
    model = get_secret("GEMINI_MODEL", "gemini-2.5-flash")
    system_text = (
        "Kamu adalah asisten profesional Arthama Management, penyedia jasa "
        "wisata, villa/resort, event planner, MICE, outbound, team building, "
        "gathering, dan perjalanan di Indonesia. "
        f"Kamu sedang bekerja untuk divisi {department}. "
        "Jawab dalam bahasa Indonesia yang jelas, praktis, terstruktur, dan "
        "siap dipakai. Jangan mengarang data, harga pasar, kontak, hasil riset, "
        "atau tindakan yang belum dilakukan. Untuk harga, bedakan estimasi dan "
        "harga terverifikasi. Jika data kurang, sebutkan asumsi yang digunakan."
    )
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt.strip(),
            config={
                "system_instruction": system_text,
                "temperature": 0.5,
            },
        )
        answer = getattr(response, "text", None)
        if not answer or not answer.strip():
            raise RuntimeError("AI tidak memberikan teks jawaban. Coba instruksi lain.")
        return answer.strip()
    except Exception as exc:
        message = str(exc)
        low = message.lower()
        if "429" in low or "quota" in low or "resource_exhausted" in low:
            raise RuntimeError(
                "Kuota Gemini sedang habis atau batas pemakaian tercapai. "
                "Tunggu reset kuota atau cek batas penggunaan di Google AI Studio. "
                "Kode aplikasi tidak dapat melewati batas kuota."
            ) from exc
        if "404" in low or "not found" in low or "model" in low and "unsupported" in low:
            raise RuntimeError(
                f"Model '{model}' tidak ditemukan atau tidak tersedia untuk API key ini. "
                "Periksa nama model yang persis tersedia di Google AI Studio. "
                "Bisa diatur lewat GEMINI_MODEL di Streamlit Secrets."
            ) from exc
        if "403" in low or "permission" in low or "api key" in low:
            raise RuntimeError(
                "Akses Gemini ditolak. Periksa API key dan akses model di Google AI Studio."
            ) from exc
        if "503" in low or "unavailable" in low:
            raise RuntimeError(
                "Layanan Gemini sedang sibuk/tidak tersedia. Coba lagi beberapa saat."
            ) from exc
        raise RuntimeError(f"Permintaan AI gagal: {message[:500]}") from exc


# ---------- Style ----------
st.markdown(
    """ <style> :root { color-scheme: dark; } .stApp { background: linear-gradient(135deg,#071323 0%,#0b1e37 52%,#101d35 100%); color: #f4f7fb; } [data-testid="stSidebar"] { background: #081629; border-right: 1px solid #25415f; } h1,h2,h3,h4 { color:#f5f8ff !important; letter-spacing:-.02em; } p, li, label, [data-testid="stMarkdownContainer"] { color:#e0eaf7; } [data-testid="stCaptionContainer"] { color:#b6c8df !important; } [data-testid="stMetric"] { background:rgba(23,48,78,.9); border:1px solid #315372; border-radius:15px; padding:15px; } [data-testid="stMetricValue"] { color:#ffffff !important; } div.stButton > button, div.stDownloadButton > button, button[kind="primary"] { border-radius:10px; border:1px solid #438bff; background:linear-gradient(90deg,#1d63dc,#117e9e); color:#fff; font-weight:650; min-height:2.6rem; } div.stButton > button:hover, div.stDownloadButton > button:hover { border-color:#7ceaff; color:#fff; } [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea, [data-testid="stNumberInput"] input { color:#f8fbff !important; background:#10243d !important; } [data-baseweb="select"] > div { background:#10243d; color:#f8fbff; border-color:#42617f; } .arthama-panel { background:rgba(17,37,64,.92); border:1px solid #2c4d6d; border-radius:16px; padding:18px; margin:8px 0 14px 0; } .muted { color:#b6c8df; font-size:.92rem; } .tag { display:inline-block; border:1px solid #3c7397; color:#b7f4ff; border-radius:999px; padding:4px 10px; font-size:.78rem; margin:2px 5px 2px 0; } hr { border-color:#29425d; } </style> """,
    unsafe_allow_html=True,
)

# ---------- Initial state ----------
if "leads" not in st.session_state:
    st.session_state.leads = pd.DataFrame([
        {"Perusahaan": "PT Guhring Indonesia", "Kota": "Bekasi", "Potensi": "Corporate outing / team building", "Status": "Perlu follow-up", "Follow-up": "2026-10-30", "Estimasi (Rp)": 25000000, "Kontak": "", "Catatan": "Data contoh; verifikasi sebelum dihubungi."},
        {"Perusahaan": "PT Tigaraksa Satria Tbk", "Kota": "Jakarta", "Potensi": "Family gathering", "Status": "Prospek baru", "Follow-up": "2026-10-29", "Estimasi (Rp)": 40000000, "Kontak": "", "Catatan": "Data contoh; verifikasi sebelum dihubungi."},
    ])
if "content" not in st.session_state:
    st.session_state.content = pd.DataFrame([
        {"Tanggal": str(date.today()), "Kanal": "Instagram + Facebook", "Konten": "Promo Inflatable Games Team Building", "Status": "Draft"},
        {"Tanggal": str(date.today()), "Kanal": "Instagram", "Konten": "Paket Lembang Bandung 2D1N", "Status": "Rencana"},
        {"Tanggal": str(date.today()), "Kanal": "Facebook", "Konten": "Promo villa weekday satu jutaan", "Status": "Rencana"},
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
        {"Tugas": "Tinjau prospek prioritas", "Divisi": "AI Sales", "Prioritas": "Tinggi", "Status": "Menunggu tindakan manusia"},
        {"Tugas": "Siapkan konten promosi berikutnya", "Divisi": "AI Marketing", "Prioritas": "Sedang", "Status": "Siap dikerjakan"},
        {"Tugas": "Verifikasi data calon klien", "Divisi": "AI Research", "Prioritas": "Sedang", "Status": "Perlu riset"},
    ]
if "ai_history" not in st.session_state:
    st.session_state.ai_history = []

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🤖 ARTHAMA")
    st.caption("MANAGEMENT · AI AGENCY")
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
        label_visibility="visible",
    )
    st.markdown("---")
    st.markdown("<span class='tag'>AI READY*</span><span class='tag'>HUMAN APPROVAL</span>", unsafe_allow_html=True)
    st.caption("*AI aktif jika API key, model, dan kuota tersedia.")
    if st.button("Tes koneksi Google Sheets", use_container_width=True):
        try:
            result = arthama_api("list")
            st.success("Konektor merespons.")
            st.session_state["sheet_test_result"] = result
        except Exception as exc:
            st.error(str(exc))

st.markdown("# ARTHAMA MANAGEMENT — AI AGENCY")
st.markdown("Ruang kerja terpadu untuk pemasaran, penjualan, dan operasional.")
st.markdown("<span class='tag'>BLUE FUTURE OFFICE</span><span class='tag'>LOW-COST FIRST</span><span class='tag'>APPROVAL BEFORE ACTION</span>", unsafe_allow_html=True)

# ---------- Command Center ----------
if page == "Command Center":
    st.markdown("## 🛰️ Command Center")
    st.markdown(
        "<div class='arthama-panel'><b>Selamat datang di kantor virtual Arthama.</b><br>"
        "<span class='muted'>Gunakan modul di sebelah kiri. Data demo ditandai sebagai contoh; "
        "tidak berarti akun sosial atau email sudah terhubung.</span></div>",
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Prospek lokal", len(st.session_state.leads))
    c2.metric("Rencana konten", len(st.session_state.content))
    c3.metric("Tugas terbuka", sum("selesai" not in str(x.get("Status", "")).lower() for x in st.session_state.tasks))
    c4.metric("Koneksi manual", sum(v == "Terhubung (manual)" for v in st.session_state.connections.values()))
    st.markdown("### Denah divisi")
    departments = [
        ("🧭", "AI Director", "Prioritas kerja, pembagian tugas, dan ringkasan."),
        ("📣", "AI Marketing", "Caption, iklan, kalender, dan ide promosi."),
        ("🎯", "AI Sales", "Penawaran, follow-up, dan pipeline prospek."),
        ("🔎", "AI Research", "Rencana riset target perusahaan dan pasar."),
        ("💬", "AI Customer Care", "Respons pelanggan dan formulir kebutuhan."),
        ("📊", "AI Analyst", "Analisis data CRM dan konten yang tersedia."),
    ]
    cols = st.columns(3)
    for i, (emoji, name, desc) in enumerate(departments):
        with cols[i % 3]:
            st.markdown(
                f"<div class='arthama-panel'><h3>{emoji} {name}</h3><span class='muted'>{desc}</span></div>",
                unsafe_allow_html=True,
            )
    st.markdown("### Prioritas tugas")
    st.dataframe(pd.DataFrame(st.session_state.tasks), use_container_width=True, hide_index=True)
    if "sheet_test_result" in st.session_state:
        with st.expander("Hasil tes konektor Google Sheets"):
            st.json(st.session_state["sheet_test_result"])

# ---------- Divisi Robot AI ----------
elif page == "Divisi Robot AI":
    st.markdown("## 🤖 Divisi Robot AI")
    st.info("Pilih divisi, tulis kebutuhan, lalu tekan tombol proses. Hasil dibuat AI jika Gemini aktif; tidak ada email/pesan yang dikirim otomatis.")
    department_options = {
        "AI Director": "Membantu menyusun prioritas, SOP, pembagian tugas, dan ringkasan manajemen.",
        "AI Marketing": "Menyusun strategi promosi, caption, iklan, kalender konten, dan brief visual.",
        "AI Sales": "Menyusun email penawaran, skrip follow-up, proposal, dan strategi pipeline.",
        "AI Research": "Membuat kerangka riset target perusahaan, kriteria prospek, dan daftar data yang perlu diverifikasi.",
        "AI Customer Care": "Menyusun balasan pelanggan, pertanyaan kualifikasi, dan penanganan keberatan.",
        "AI Analyst": "Menganalisis data yang diberikan, membuat ringkasan KPI, dan rekomendasi."
    }
    chosen_department = st.selectbox("Pilih divisi", list(department_options.keys()))
    st.caption(department_options[chosen_department])
    with st.form("ai_work_form", clear_on_submit=False):
        ai_task = st.text_area(
            "Instruksi kerja",
            height=180,
            placeholder=(
                "Contoh: Buatkan caption promosi paket gathering 2D1N untuk HRD "
                "perusahaan di Jabodetabek. Sertakan headline, manfaat, CTA, dan hashtag."
            ),
        )
        ai_context = st.text_area(
            "Konteks tambahan (opsional)",
            height=90,
            placeholder="Masukkan harga, kapasitas, tanggal, tujuan, atau data yang benar-benar sudah diketahui.",
        )
        run_ai = st.form_submit_button("🚀 Jalankan divisi AI", type="primary", use_container_width=True)
    if run_ai:
        if not ai_task.strip():
            st.warning("Instruksi kerja harus diisi terlebih dahulu.")
        else:
            full_prompt = (
                f"Instruksi:\n{ai_task.strip()}\n\n"
                f"Konteks dari pengguna:\n{ai_context.strip() or 'Tidak ada konteks tambahan.'}\n\n"
                "Buat hasil yang siap digunakan. Beri judul dan langkah praktis bila sesuai. "
                "Jangan mengklaim sudah melakukan tindakan eksternal."
            )
            with st.spinner(f"{chosen_department} sedang menyusun hasil..."):
                try:
                    answer = ask_gemini(full_prompt, chosen_department)
                    st.session_state.ai_history.insert(0, {
                        "waktu": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "divisi": chosen_department,
                        "instruksi": ai_task.strip(),
                        "jawaban": answer,
                    })
                    st.success("Hasil berhasil dibuat.")
                except Exception as exc:
                    st.error(str(exc))
    if st.session_state.ai_history:
        st.markdown("### Hasil kerja AI")
        latest = st.session_state.ai_history[0]
        st.markdown(f"**Divisi:** {latest['divisi']} · **Waktu:** {latest['waktu']}")
        st.markdown(latest["jawaban"])
        st.download_button(
            "⬇️ Unduh hasil sebagai TXT",
            data=(f"DIVISI: {latest['divisi']}\nWAKTU: {latest['waktu']}\n\nINSTRUKSI:\n{latest['instruksi']}\n\nHASIL:\n{latest['jawaban']}").encode("utf-8"),
            file_name="arthama_hasil_ai.txt",
            mime="text/plain",
        )
        with st.expander("Riwayat hasil sesi ini"):
            for item in st.session_state.ai_history[:10]:
                st.markdown(f"**{item['waktu']} — {item['divisi']}**")
                st.write(item["instruksi"])
                st.markdown(item["jawaban"])
                st.markdown("---")

# ---------- Sales CRM ----------
elif page == "Sales CRM":
    st.markdown("## 🎯 Sales CRM")
    st.caption("CRM lokal sesi ini dapat diedit dan diunduh. Tombol sinkronisasi hanya dipakai bila konektor Apps Script yang sudah ada benar-benar cocok.")
    crm_tab, add_tab, sync_tab = st.tabs(["Data prospek", "Tambah prospek", "Google Sheets"])
    with crm_tab:
        edited = st.data_editor(
            st.session_state.leads,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="crm_editor",
        )
        st.session_state.leads = edited
        st.download_button(
            "⬇️ Unduh CRM CSV",
            data=st.session_state.leads.to_csv(index=False).encode("utf-8-sig"),
            file_name="arthama_sales_crm.csv",
            mime="text/csv",
        )
    with add_tab:
        with st.form("add_lead_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            company = c1.text_input("Nama perusahaan / calon klien")
            city = c2.text_input("Kota")
            contact = c1.text_input("Kontak publik (opsional)")
            potential = c2.text_input("Kebutuhan / potensi layanan")
            lead_status = st.selectbox(
                "Status",
                ["Prospek baru", "Riset awal", "Penawaran disiapkan", "Penawaran terkirim",
                 "Menunggu respons", "Tertarik", "Survei", "DP masuk", "Selesai", "Tidak lanjut"],
            )
            followup = st.date_input("Tanggal follow-up", value=date.today())
            amount = st.number_input("Estimasi nilai proyek (Rp)", min_value=0, step=1000000)
            notes = st.text_area("Catatan")
            add_submit = st.form_submit_button("Simpan prospek", type="primary")
        if add_submit:
            if not company.strip():
                st.error("Nama perusahaan/calon klien wajib diisi.")
            else:
                new_row = {
                    "Perusahaan": company.strip(),
                    "Kota": city.strip(),
                    "Potensi": potential.strip(),
                    "Status": lead_status,
                    "Follow-up": str(followup),
                    "Estimasi (Rp)": int(amount),
                    "Kontak": contact.strip(),
                    "Catatan": notes.strip(),
                }
                st.session_state.leads = pd.concat(
                    [st.session_state.leads, pd.DataFrame([new_row])],
                    ignore_index=True,
                )
                st.success("Prospek tersimpan di sesi aplikasi. Unduh CSV untuk salinan lokal.")
    with sync_tab:
        st.warning(
            "Sebelum menulis ke Google Sheets, pastikan Apps Script menerima format data yang sama. "
            "Tombol ini tidak mengubah struktur sheet."
        )
        if st.button("Baca data dari Google Sheets", key="crm_read_sheet"):
            try:
                result = arthama_api("list")
                st.session_state["crm_sheet_result"] = result
                st.success("Konektor merespons. Periksa struktur data sebelum mengimpor.")
            except Exception as exc:
                st.error(str(exc))
        if "crm_sheet_result" in st.session_state:
            st.json(st.session_state["crm_sheet_result"])
        st.caption("Untuk mencegah salah tulis pada database yang sudah berisi data, penulisan otomatis ke Sheet sengaja tidak diaktifkan di versi ini.")

# ---------- Studio Konten ----------
elif page == "Studio Konten":
    st.markdown("## 🎨 Studio Konten")
    st.caption("Buat brief dan kalender konten. Penyimpanan saat ini berlangsung selama sesi; publikasi ke media sosial belum otomatis.")
    tab_calendar, tab_create, tab_ai = st.tabs(["Kalender", "Brief baru", "Buat dengan AI"])
    with tab_calendar:
        edited_content = st.data_editor(
            st.session_state.content,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="content_editor",
        )
        st.session_state.content = edited_content
        st.download_button(
            "⬇️ Unduh kalender CSV",
            data=st.session_state.content.to_csv(index=False).encode("utf-8-sig"),
            file_name="arthama_kalender_konten.csv",
            mime="text/csv",
        )
    with tab_create:
        with st.form("new_content_form", clear_on_submit=True):
            topic = st.text_input("Tema konten", placeholder="Contoh: Promo villa weekday satu jutaan")
            channels = st.multiselect("Kanal", ["Instagram", "Facebook", "TikTok", "WhatsApp"], default=["Instagram", "Facebook"])
            objective = st.selectbox("Tujuan", ["Mendapatkan reservasi", "Mendapatkan pertanyaan harga", "Membangun kepercayaan", "Mendapatkan klien perusahaan"])
            audience = st.text_input("Target audiens", placeholder="HRD, GA, keluarga, panitia gathering")
            publish_date = st.date_input("Tanggal rencana", value=date.today())
            save_content = st.form_submit_button("Simpan brief")
        if save_content:
            if not topic.strip():
                st.error("Tema konten wajib diisi.")
            else:
                row = {
                    "Tanggal": str(publish_date),
                    "Kanal": " + ".join(channels) if channels else "Belum ditentukan",
                    "Konten": f"{topic.strip()} | Tujuan: {objective} | Target: {audience.strip()}",
                    "Status": "Brief baru",
                }
                st.session_state.content = pd.concat([st.session_state.content, pd.DataFrame([row])], ignore_index=True)
                st.success("Brief ditambahkan ke kalender sesi ini.")
    with tab_ai:
        ai_content_request = st.text_area(
            "Jelaskan konten yang ingin dibuat",
            height=120,
            placeholder="Contoh: Buat 3 caption promo gathering perusahaan, gaya profesional dan tidak berlebihan.",
        )
        if st.button("Buat konsep konten dengan AI", type="primary"):
            if not ai_content_request.strip():
                st.warning("Isi kebutuhan konten terlebih dahulu.")
            else:
                with st.spinner("AI sedang menyusun konsep..."):
                    try:
                        result = ask_gemini(ai_content_request, "AI Marketing")
                        st.session_state["last_content_ai"] = result
                        st.markdown(result)
                    except Exception as exc:
                        st.error(str(exc))
        if st.session_state.get("last_content_ai"):
            st.download_button(
                "⬇️ Unduh konsep konten TXT",
                data=st.session_state["last_content_ai"].encode("utf-8"),
                file_name="arthama_konsep_konten.txt",
                mime="text/plain",
            )

# ---------- Koneksi Akun ----------
elif page == "Koneksi Akun":
    st.markdown("## 🔌 Koneksi Akun")
    st.warning("Status di sini adalah catatan manual, bukan bukti login atau otorisasi ke layanan eksternal.")
    account_details = {
        "Gmail": ("arthamamanagement@gmail.com", "Email pusat; integrasi pengiriman memerlukan koneksi resmi."),
        "Instagram": ("@arthamamanagement", "Akun sosial; publikasi API memerlukan izin dan tipe akun yang sesuai."),
        "Facebook Page": ("@arthamavillapuncak", "Pastikan Page dan izin pengelola sesuai."),
        "TikTok": ("@arthamamanagement", "Publikasi otomatis tergantung akses API yang disetujui."),
        "Metricool": ("", "Penjadwalan dilakukan melalui proses otorisasi resmi Metricool."),
        "Google Sheets": ("Database calon klien Arthama", "Konektor Apps Script tersedia jika Secrets benar."),
        "WhatsApp Business": ("087868239249", "Gunakan izin penerima dan platform resmi untuk automasi."),
    }
    options = ["Belum dihubungkan", "Direncanakan", "Terhubung (manual)"]
    for service, (account, description) in account_details.items():
        with st.container(border=True):
            left, right = st.columns([3, 2])
            with left:
                st.markdown(f"### {service}")
                if account:
                    st.write(f"**Akun:** {account}")
                st.caption(description)
            with right:
                current = st.session_state.connections.get(service, options[0])
                if current not in options:
                    current = options[0]
                choice = st.selectbox("Status pencatatan", options, index=options.index(current), key=f"connection_select_{service}")
                if st.button("Simpan status", key=f"connection_save_{service}"):
                    st.session_state.connections[service] = choice
                    st.success("Status pencatatan diperbarui.")
    st.markdown("### Tes koneksi Google Sheets")
    if st.button("Tes konektor sekarang", type="primary"):
        try:
            data = arthama_api("list")
            st.success("Konektor memberi respons.")
            st.json(data)
        except Exception as exc:
            st.error(str(exc))

# ---------- Pengaturan & Keamanan ----------
elif page == "Pengaturan & Keamanan":
    st.markdown("## 🛡️ Pengaturan & Keamanan")
    st.markdown(
        """ <div class='arthama-panel'> <h3>Prinsip keamanan</h3> <ul> <li>API key disimpan di Streamlit Secrets, bukan di app.py.</li> <li>Jangan kirim kata sandi, OTP, atau recovery code ke aplikasi.</li> <li>Gunakan persetujuan manusia sebelum mengirim penawaran atau pesan.</li> <li>Batasi data prospek yang dikumpulkan dan periksa akurasinya.</li> <li>Integrasi sosial harus memakai otorisasi resmi dan menghormati aturan platform.</li> </ul> </div> """,
        unsafe_allow_html=True,
    )
    st.markdown("### Konfigurasi yang terdeteksi")
    st.write("Gemini API key:", "Tersedia" if get_secret("GEMINI_API_KEY") else "Belum disetel")
    st.write("Model Gemini:", get_secret("GEMINI_MODEL", "gemini-2.5-flash"))
    st.write("Apps Script URL:", "Tersedia" if get_secret("ARTHAMA_WEBAPP_URL") else "Belum disetel")
    st.write("Token konektor:", "Tersedia" if get_secret("ARTHAMA_API_TOKEN") else "Belum disetel")
    st.markdown("### Batas fungsi saat ini")
    st.dataframe(pd.DataFrame([
        {"Modul": "Command Center", "Status": "Aktif; angka lokal/demo"},
        {"Modul": "Divisi Robot AI", "Status": "Memanggil Gemini jika key, model, dan kuota tersedia"},
        {"Modul": "Sales CRM", "Status": "Edit lokal, tambah prospek, ekspor CSV; baca Sheets opsional"},
        {"Modul": "Studio Konten", "Status": "Kalender lokal, brief, ekspor, dan konsep AI"},
        {"Modul": "Koneksi Akun", "Status": "Catatan status; bukan login OAuth"},
        {"Modul": "Publikasi otomatis", "Status": "Belum aktif"},
        {"Modul": "Pengiriman email/WhatsApp", "Status": "Belum aktif"},
    ]), use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("ARTHAMA MANAGEMENT · AI AGENCY | Versi kerja · Data lokal sesi aplikasi kecuali integrasi yang dites.")
