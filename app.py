import os
import json
from datetime import date, datetime

import pandas as pd
import requests
import streamlit as st

# =====================================================
# ARTHAMA MANAGEMENT — AI AGENCY
# =====================================================

st.set_page_config(
    page_title="Arthama Management | AI Agency",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_secret(name, default=""):
    """Membaca konfigurasi rahasia dengan aman."""
    try:
        value = st.secrets.get(name, default)
        if value:
            return str(value).strip()
    except Exception:
        pass

    return os.getenv(name, default).strip()


def arthama_api(action, data=None):
    """Mengakses konektor Apps Script Arthama."""
    url = get_secret("ARTHAMA_WEBAPP_URL")
    token = get_secret("ARTHAMA_API_TOKEN")

    if not url or not token:
        raise RuntimeError(
            "Koneksi Apps Script belum dikonfigurasi "
            "di Streamlit Secrets."
        )

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
        result = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "Respons Apps Script bukan JSON yang valid."
        ) from exc

    if (
        isinstance(result, dict)
        and str(result.get("status", "")).lower() == "error"
    ):
        raise RuntimeError(
            result.get("message", "Koneksi Apps Script gagal.")
        )

    return result


def get_gemini_client():
    """Membuat klien Gemini dari API key rahasia."""
    api_key = get_secret("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY belum diatur di Streamlit Secrets."
        )

    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except ImportError as exc:
        raise RuntimeError(
            "Paket google-genai belum terpasang. "
            "Periksa requirements.txt."
        ) from exc


def ask_gemini(prompt, department="Asisten Arthama"):
    """Menjalankan Gemini 3.8 Flash."""
    if not prompt or not prompt.strip():
        raise ValueError("Instruksi AI belum diisi.")

    client = get_gemini_client()
    model = get_secret(
        "GEMINI_MODEL",
        "gemini-3.8-flash",
    )

    instruction = (
        "Kamu adalah asisten profesional Arthama Management, "
        "penyedia jasa wisata, villa dan resort, event planner, "
        "MICE, outbound, gathering, team building, serta perjalanan "
        "wisata di Indonesia. "
        f"Kamu bertugas pada divisi {department}. "
        "Jawab dalam bahasa Indonesia yang jelas, praktis, dan "
        "terstruktur. Jangan mengarang data, harga, kontak, hasil "
        "riset, atau tindakan yang belum dilakukan. "
        "Bedakan estimasi dengan data terverifikasi."
    )

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt.strip(),
            config={
                "system_instruction": instruction,
                "temperature": 0.5,
            },
        )

        answer = getattr(response, "text", None)

        if not answer or not answer.strip():
            raise RuntimeError(
                "Gemini tidak menghasilkan jawaban."
            )

        return answer.strip()

    except Exception as exc:
        message = str(exc)
        lower = message.lower()

        if "429" in lower or "quota" in lower:
            raise RuntimeError(
                "Kuota Gemini habis atau batas pemakaian tercapai. "
                "Periksa kuota di Google AI Studio."
            ) from exc

        if "404" in lower or "not found" in lower:
            raise RuntimeError(
                f"Model {model} tidak ditemukan atau tidak tersedia "
                "untuk API key ini. Periksa nama model di Google AI Studio."
            ) from exc

        if "403" in lower or "permission" in lower:
            raise RuntimeError(
                "Akses Gemini ditolak. Periksa API key dan izin model."
            ) from exc

        if "503" in lower or "unavailable" in lower:
            raise RuntimeError(
                "Gemini sedang tidak tersedia. Coba lagi nanti."
            ) from exc

        raise RuntimeError(
            f"Permintaan Gemini gagal: {message[:300]}"
        ) from exc


# =====================================================
# TAMPILAN
# =====================================================

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(
            135deg,
            #071323,
            #0b1e37,
            #101d35
        );
        color: #f4f7fb;
    }

    [data-testid="stSidebar"] {
        background: #081629;
        border-right: 1px solid #25415f;
    }

    h1, h2, h3, h4 {
        color: #f5f8ff !important;
    }

    p, li, label {
        color: #e0eaf7;
    }

    [data-testid="stMetric"] {
        background: #17304e;
        border: 1px solid #315372;
        border-radius: 12px;
        padding: 14px;
    }

    div.stButton > button {
        border-radius: 10px;
        background: #1d63dc;
        color: white;
        font-weight: 600;
        min-height: 42px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🤖 Arthama Management")
st.subheader("AI Agency Command Center")
st.caption(
    "Pusat kerja AI untuk pemasaran, penjualan, riset, "
    "pelayanan pelanggan, dan analisis bisnis."
)
