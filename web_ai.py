import streamlit as st
from google import genai
from google.genai import types
import datetime

st.set_page_config(page_title="Jarvis AI Web", page_icon="🤖")
st.title("🤖 Jarvis - Asisten AI Pribadi Gua")
st.caption("Sekarang Jarvis udah punya ingatan dan bisa Googling!")

API_KEY = st.secrets["Your_API_Key"]

# ==========================================
# 1. BIKIN CLIENT DAN MEMORI DI SESSION STATE (FIXED)
# ==========================================
# BARU: Simpan client di session state biar gak ketutup pas Streamlit melakukan rerun
if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=API_KEY)

if "chat_session" not in st.session_state:
    tanggal_asli = datetime.datetime.now().strftime("%A, %d %B %Y")
    # Sekarang kita panggil create() lewat client yang ada di session state
    st.session_state.chat_session = st.session_state.client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=f"Hari ini tanggal {tanggal_asli}. Lo adalah Jarvis, asisten gue yang asik dan santai.",
            tools=[{"google_search": {}}]
        )
    )

if "histori_layar" not in st.session_state:
    st.session_state.histori_layar = []

# ==========================================
# 2. TAMPILIN HISTORI CHAT DI WEB
# ==========================================
for pesan in st.session_state.histori_layar:
    with st.chat_message(pesan["role"]):
        st.markdown(pesan["teks"])

# ==========================================
# 3. KOTAK INPUT ALA CHATGPT
# ==========================================
pertanyaan = st.chat_input("Ketik pertanyaan lu di sini bro...")

if pertanyaan:
    st.session_state.histori_layar.append({"role": "user", "teks": pertanyaan})
    with st.chat_message("user"):
        st.markdown(pertanyaan)

    with st.chat_message("assistant"):
        with st.spinner("Jarvis lagi mikir..."):
            try:
                respons = st.session_state.chat_session.send_message(pertanyaan)
                st.markdown(respons.text)
                st.session_state.histori_layar.append({"role": "assistant", "teks": respons.text})

            except Exception as e:
                st.error(f"Waduh bro, server ngambek: {e}")