import streamlit as st
from google import genai
from google.genai import types
import datetime
from PIL import Image

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
        model="gemini-2.5-flash", 
        config=types.GenerateContentConfig(
            system_instruction=f"Hari ini tanggal {tanggal_asli}. Lo adalah Jarvis, asisten AI gue. Jawablah langsung dari suara atau gambar yang gue kasih dengan santai.",
            tools=[{"google_search": {}}] 
        )
    )

if "histori_layar" not in st.session_state:
    st.session_state.histori_layar = []


# ==========================================
# 3. SIDEBAR (DIBERSIHIN BIAR RAPI)
# ==========================================
with st.sidebar:
    st.title("🤖 Jarvis Menu")
    
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
    
    if st.button("🚪 Keluar / Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()


# ==========================================
# 4. AREA CHAT UTAMA & KARTU REKOMENDASI
# ==========================================
st.title("🤖 Jarvis Assistant")

teks_dari_tombol = None

if not st.session_state.histori_layar:
    st.write("Halo bro! Gue Jarvis. Ada yang bisa gue bantu hari ini?")
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

# Render histori chat di layar
for pesan in st.session_state.histori_layar:
    avatar = "🧑‍💻" if pesan["role"] == "user" else "🤖"
    with st.chat_message(pesan["role"], avatar=avatar):
        st.markdown(pesan["teks"])
        # Tampilin gambar kalau ada di memori
        if pesan.get("gambar"):
            st.image(pesan["gambar"], width=250)
        # Tampilin play suara kalau ada di memori
        if pesan.get("suara"):
            st.audio(pesan["suara"], format="audio/wav")


# ==========================================
# 5. FITUR LAMPIRAN & REKAM SUARA
# ==========================================
st.write("") # Spasi dikit
with st.expander("📎 Lampirkan Gambar / 🎙️ Rekam Suara", expanded=False):
    col_img, col_mic = st.columns(2)
    with col_img:
        gambar_upload = st.file_uploader("Upload Gambar", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
    with col_mic:
        # Fitur baru Streamlit buat rekam suara!
        suara_upload = st.audio_input("Ngobrol pake suara")
        
    # Tombol rahasia biar user tetep bisa ngirim kalau males ngetik
    if gambar_upload or suara_upload:
        if st.button("🚀 Kirim Lampiran/Suara", use_container_width=True):
            teks_dari_tombol = "Tolong perhatikan dan respon lampiran ini."


# ==========================================
# 6. LOGIK PENGIRIMAN PESAN KE AI
# ==========================================
teks_dari_input = st.chat_input("Ketik di sini atau pake mic di atas bro...")
pertanyaan = teks_dari_input or teks_dari_tombol

if pertanyaan:
    img_pil = None
    if gambar_upload:
        img_pil = Image.open(gambar_upload)

    # Simpan chat ke histori layar (Termasuk byte suaranya)
    st.session_state.histori_layar.append({
        "role": "user", 
        "teks": pertanyaan if not (gambar_upload or suara_upload) else "*(Mengirim Lampiran/Suara)* " + pertanyaan, 
        "gambar": img_pil,
        "suara": suara_upload.getvalue() if suara_upload else None
    })
    
    # Nampilin efek yang dikirim user ke layar saat itu juga
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(pertanyaan)
        if img_pil:
            st.image(img_pil, width=250)
        if suara_upload:
            st.audio(suara_upload.getvalue(), format="audio/wav")
    
    # Proses mikir si AI
    with st.chat_message("assistant", avatar="🤖"):
        try:
            # Merakit paket isi pesan (Teks + Gambar + Suara)
            isi_pesan = [pertanyaan]
            if img_pil:
                isi_pesan.append(img_pil)
            if suara_upload:
                # Mengubah format suara Streamlit biar dipahami otak Gemini
                audio_part = types.Part.from_bytes(data=suara_upload.getvalue(), mime_type="audio/wav")
                isi_pesan.append(audio_part)

            def generate_typing_effect():
                response_stream = st.session_state.chat_session.send_message_stream(isi_pesan)
                for chunk in response_stream:
                    yield chunk.text
            
            respons_teks = st.write_stream(generate_typing_effect())
            
            st.session_state.histori_layar.append({
                "role": "assistant", 
                "teks": respons_teks, 
                "gambar": None,
                "suara": None
            })
            
        except Exception as e:
            st.error(f"Waduh bro, Jarvis lagi pusing: {e}")
