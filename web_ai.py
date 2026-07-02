import streamlit as st
from google import genai
from google.genai import types
import datetime
from PIL import Image # BARU: Library buat ngebaca gambar

st.set_page_config(page_title="Jarvis AI", page_icon="🤖", layout="centered")

API_KEY = st.secrets["Your_API_Key"]
PIN_RAHASIA = st.secrets["App_PIN"]

# ==========================================
# 1. GERBANG LOGIN PIN RAHASIA
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 Jarvis Security Gate")
    st.write("Aplikasi ini diproteksi. Masukin PIN buat bangunin Jarvis.")
    
    input_pin = st.text_input("Masukkan PIN Rahasia Lo:", type="password")
    if st.button("Unlock Jarvis 🔑", use_container_width=True):
        if input_pin == PIN_RAHASIA:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("PIN Salah bro! Jangan macem-macem ya.")
    st.stop()


# ==========================================
# 2. INISIALISASI MESIN & MEMORI
# ==========================================
if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=API_KEY)

if "chat_session" not in st.session_state:
    tanggal_asli = datetime.datetime.now().strftime("%A, %d %B %Y")
    st.session_state.chat_session = st.session_state.client.chats.create(
        model="gemini-2.5-flash", # Model ini otomatis pinter baca gambar & teks
        config=types.GenerateContentConfig(
            system_instruction=f"Hari ini tanggal {tanggal_asli}. Lo adalah Jarvis, asisten AI pribadi gue yang asik, gaul, cerdas, dan santai.",
            tools=[{"google_search": {}}] 
        )
    )

if "histori_layar" not in st.session_state:
    st.session_state.histori_layar = []


# ==========================================
# 3. SIDEBAR ALA CHATGPT
# ==========================================
with st.sidebar:
    st.title("🤖 Jarvis Menu")
    
    # Tombol Obrolan Baru
    if st.button("📝 Obrolan Baru", use_container_width=True):
        st.session_state.histori_layar = []
        st.session_state.chat_session = st.session_state.client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction="Lo adalah Jarvis, asisten gue yang asik dan santai.",
                tools=[{"google_search": {}}] 
            )
        )
        st.rerun()
        
    st.divider()
    
    # Fitur Upload Gambar di Sidebar
    st.write("📎 **Mata Jarvis**")
    gambar_upload = st.file_uploader("Upload gambar ke Jarvis", type=['png', 'jpg', 'jpeg'])
    if gambar_upload:
        st.success("Gambar nempel! Tinggal ketik perintah lo di bawah.")

    st.divider()
    
    # Tombol Logout
    if st.button("🚪 Keluar / Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()


# ==========================================
# 4. AREA CHAT UTAMA & KARTU REKOMENDASI
# ==========================================
st.title("🤖 Jarvis Assistant")

# Variabel penyimpan teks dari tombol saran
teks_dari_tombol = None

if not st.session_state.histori_layar:
    st.write("Halo bro! Gue Jarvis. Ada yang bisa gue bantu hari ini?")
    
    # Kartu sekarang pake tombol asli, kalau diklik bakal ngisi teks_dari_tombol
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💡 Eksplor Ide\n\nBikin ide bisnis", use_container_width=True):
            teks_dari_tombol = "Kasih gue ide bisnis modal kecil dong."
    with col2:
        if st.button("✈️ Rencana Jalan\n\nLiburan Bali", use_container_width=True):
            teks_dari_tombol = "Bikin itinerary liburan ke Bali 3 hari."
    with col3:
        if st.button("⚽ Update Berita\n\nBola Semalem", use_container_width=True):
            teks_dari_tombol = "Siapa yang menang pertandingan bola semalem?"

# Render histori chat (termasuk nampilin gambar yang pernah di-upload)
for pesan in st.session_state.histori_layar:
    avatar = "🧑‍💻" if pesan["role"] == "user" else "🤖"
    with st.chat_message(pesan["role"], avatar=avatar):
        st.markdown(pesan["teks"])
        # Kalau pesannya nyimpen gambar, tampilin juga
        if pesan.get("gambar"):
            st.image(pesan["gambar"], width=250)


# ==========================================
# 5. LOGIK PENGIRIMAN PESAN
# ==========================================
# Cek apakah user ngetik di kotak ATAU ngeklik tombol rekomendasi
teks_dari_input = st.chat_input("Tanya atau suruh Jarvis deskripsiin gambar...")
pertanyaan = teks_dari_input or teks_dari_tombol

if pertanyaan:
    # Siapin file gambar buat diproses (jika ada)
    img_pil = None
    if gambar_upload:
        img_pil = Image.open(gambar_upload)

    # 1. Tampilkan chat user di layar
    st.session_state.histori_layar.append({
        "role": "user", 
        "teks": pertanyaan, 
        "gambar": img_pil # Simpan gambarnya ke histori layar
    })
    
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(pertanyaan)
        if img_pil:
            st.image(img_pil, width=250)
    
    # 2. Proses ke AI Gemini
    with st.chat_message("assistant", avatar="🤖"):
        try:
            def generate_typing_effect():
                # Gabungkan teks dan gambar (kalau ada) buat dikirim barengan
                isi_pesan = [pertanyaan]
                if img_pil:
                    isi_pesan.append(img_pil)
                    
                response_stream = st.session_state.chat_session.send_message_stream(isi_pesan)
                for chunk in response_stream:
                    yield chunk.text
            
            respons_teks = st.write_stream(generate_typing_effect())
            
            # Simpan balasan AI ke memori layar
            st.session_state.histori_layar.append({
                "role": "assistant", 
                "teks": respons_teks, 
                "gambar": None
            })
            
        except Exception as e:
            st.error(f"Waduh bro, Jarvis pusing: {e}")
