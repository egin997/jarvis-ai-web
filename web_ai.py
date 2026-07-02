import streamlit as st
from google import genai
from google.genai import types
import datetime

# 1. Konfigurasi Halaman & Tema Dasar
st.set_page_config(page_title="Jarvis AI", page_icon="🤖", layout="centered")

# Mengambil API Key dari Secret Cloud lo kemarin
API_KEY = st.secrets["Your_API_Key"]

# 2. Inisialisasi Client & Chat Session di Session State
if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=API_KEY)

if "chat_session" not in st.session_state:
    tanggal_asli = datetime.datetime.now().strftime("%A, %d %B %Y")
    st.session_state.chat_session = st.session_state.client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=f"Hari ini tanggal {tanggal_asli}. Lo adalah Jarvis, asisten AI pribadi gue yang asik, gaul, cerdas, dan santai.",
            tools=[{"google_search": {}}] 
        )
    )

if "histori_layar" not in st.session_state:
    st.session_state.histori_layar = []

# ==========================================
# 3. SIDEBAR (MENU SAMPING)
# ==========================================
with st.sidebar:
    st.title("⚙️ Jarvis Control")
    st.write("Platform AI Engineer Pribadi Egin.")
    st.divider()
    
    # Tombol sakti buat hapus ingatan AI / Reset Chat
    if st.button("🗑️ Hapus Obrolan (Reset)", use_container_width=True):
        st.session_state.histori_layar = []
        # Bikin sesi chat baru biar ingatannya beneran kehapus
        st.session_state.chat_session = st.session_state.client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction="Lo adalah Jarvis, asisten gue yang asik dan santai.",
                tools=[{"google_search": {}}] 
            )
        )
        st.rerun()

# ==========================================
# 4. AREA UTAMA (TAMPILAN CHAT)
# ==========================================
st.title("🤖 Jarvis Assistant")

# JIKA CHAT MASIH KOSONG, TAMPILKAN WELCOME CARDS ALA GEMINI
if not st.session_state.histori_layar:
    st.write("Halo bro! Gue Jarvis. Ada yang bisa gue bantu hari ini?")
    
    # Bikin 3 kolom kartu saran
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("💡 **Eksplor Ide**\n\nKasih gue ide bisnis modal kecil dong.")
    with col2:
        st.info("✈️ **Rencana Jalan**\n\nBikin itinerary liburan ke Bali 3 hari.")
    with col3:
        st.info("⚽ **Update Berita**\n\nSiapa yang menang pertandingan bola semalem?")

# TAMPILKAN HISTORI CHAT PAKE AVATAR KEREN
for pesan in st.session_state.histori_layar:
    avatar = "🧑‍💻" if pesan["role"] == "user" else "🤖"
    with st.chat_message(pesan["role"], avatar=avatar):
        st.markdown(pesan["teks"])

# ==========================================
# 5. INPUT CHAT (EFEK STREAMING MENGETIK)
# ==========================================
pertanyaan = st.chat_input("Tanya Jarvis di sini bro...")

if pertanyaan:
    # Tampilkan chat user
    st.session_state.histori_layar.append({"role": "user", "teks": pertanyaan})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(pertanyaan)
    
    # Tampilkan chat AI dengan efek mengetik asli (Streaming)
    with st.chat_message("assistant", avatar="🤖"):
        try:
            # Fungsi khusus dari Streamlit untuk animasi mengetik real-time
            def generate_typing_effect():
                # Kirim pesan versi STREAM ke Gemini
                response_stream = st.session_state.chat_session.send_message_stream(pertanyaan)
                for chunk in response_stream:
                    yield chunk.text
            
            # Jalankan efek mengetik di layar
            respons_teks = st.write_stream(generate_typing_effect())
            
            # Simpan jawaban akhir ke histori
            st.session_state.histori_layar.append({"role": "assistant", "teks": respons_teks})
            
        except Exception as e:
            st.error(f"Waduh bro, Jarvis lagi pusing: {e}")
