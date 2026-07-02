import streamlit as st
from google import genai
from google.genai import types
import datetime

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Jarvis AI", page_icon="🤖", layout="centered")

# Ambil API Key dan PIN Rahasia dari Secret Cloud lo
API_KEY = st.secrets["Your_API_Key"]
PIN_RAHASIA = st.secrets["App_PIN"] # Kunci PIN baru lo nanti di Cloud

# ==========================================
# 2. GERBANG LOGIN PIN RAHASIA
# ==========================================
# Cek apakah user udah sukses login sebelumnya
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Kalau BELUM login, tampilkan halaman gembok
if not st.session_state.logged_in:
    st.title("🔒 Jarvis Security Gate")
    st.write("Aplikasi ini diproteksi. Masukin PIN buat bangunin Jarvis.")
    
    # Input PIN (pake type="password" biar angkanya berubah jadi titik-titik)
    input_pin = st.text_input("Masukkan PIN Rahasia Lo:", type="password")
    tombol_masuk = st.button("Unlock Jarvis 🔑", use_container_width=True)
    
    if tombol_masuk:
        if input_pin == PIN_RAHASIA:
            st.session_state.logged_in = True
            st.success("PIN Bener! Membuka Jarvis...")
            st.rerun() # Refresh halaman buat masuk ke Jarvis
        else:
            st.error("PIN Salah bro! Jangan macem-macem ya.")
            
    # Stop program di sini kalau belum login, jadi kode Jarvis di bawah gak bakal kebaca
    st.stop()


# ==========================================
# 3. KODE UTAMA JARVIS (HANYA JALAN KALO UDAH LOGIN)
# ==========================================

# Inisialisasi Client & Chat Session
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

# SIDEBAR
with st.sidebar:
    st.title("⚙️ Jarvis Control")
    st.write("Platform AI Engineer Pribadi Egin.")
    st.divider()
    
    # Tombol Logout
    if st.button("🔒 Logout / Kunci Aplikasi", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
        
    # Tombol Reset Chat
    if st.button("🗑️ Hapus Obrolan (Reset)", use_container_width=True):
        st.session_state.histori_layar = []
        st.session_state.chat_session = st.session_state.client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction="Lo adalah Jarvis, asisten gue yang asik dan santai.",
                tools=[{"google_search": {}}] 
            )
        )
        st.rerun()

# AREA CHAT UTAMA
st.title("🤖 Jarvis Assistant")

if not st.session_state.histori_layar:
    st.write("Halo bro! Gue Jarvis. Ada yang bisa gue bantu hari ini?")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("💡 **Eksplor Ide**\n\nKasih gue ide bisnis modal kecil dong.")
    with col2:
        st.info("✈️ **Rencana Jalan**\n\nBikin itinerary liburan ke Bali 3 hari.")
    with col3:
        st.info("⚽ **Update Berita**\n\nSiapa yang menang pertandingan bola semalem?")

for pesan in st.session_state.histori_layar:
    avatar = "🧑‍💻" if pesan["role"] == "user" else "🤖"
    with st.chat_message(pesan["role"], avatar=avatar):
        st.markdown(pesan["teks"])

# INPUT CHAT
pertanyaan = st.chat_input("Tanya Jarvis di sini bro...")

if pertanyaan:
    st.session_state.histori_layar.append({"role": "user", "teks": pertanyaan})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(pertanyaan)
    
    with st.chat_message("assistant", avatar="🤖"):
        try:
            def generate_typing_effect():
                response_stream = st.session_state.chat_session.send_message_stream(pertanyaan)
                for chunk in response_stream:
                    yield chunk.text
            
            respons_teks = st.write_stream(generate_typing_effect())
            st.session_state.histori_layar.append({"role": "assistant", "teks": respons_teks})
            
        except Exception as e:
            st.error(f"Waduh bro, Jarvis lagi pusing: {e}")
