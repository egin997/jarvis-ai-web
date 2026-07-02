import streamlit as st
from google import genai
from google.genai import types
import datetime
from PIL import Image
import uuid
import PyPDF2 # BARU: Library buat bongkar PDF

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
    input_pin = st.text_input("Masukkan PIN Rahasia Lo:", type="password")
    if st.button("Unlock Jarvis 🔑", use_container_width=True):
        if input_pin == PIN_RAHASIA:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("PIN Salah bro! Jangan macem-macem ya.")
    st.stop()


# ==========================================
# 2. SISTEM LEMARI CHAT (MULTI-SESSION)
# ==========================================
if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=API_KEY)

if "kumpulan_chat" not in st.session_state:
    st.session_state.kumpulan_chat = {} 

if "chat_aktif_id" not in st.session_state:
    st.session_state.chat_aktif_id = None

def bikin_chat_baru():
    id_baru = str(uuid.uuid4())
    tanggal_asli = datetime.datetime.now().strftime("%A, %d %B %Y")
    
    st.session_state.kumpulan_chat[id_baru] = {
        "judul": "💬 Obrolan Baru", 
        "histori_layar": [],
        "chat_session": st.session_state.client.chats.create(
            model="gemini-2.5-flash", 
            config=types.GenerateContentConfig(
                system_instruction=f"Hari ini {tanggal_asli}. Lo Jarvis. Lo pinter baca dokumen dan gambar. Jawab sesuai konteks yang dikasih dengan bahasa santai.",
                tools=[{"google_search": {}}] 
            )
        )
    }
    st.session_state.chat_aktif_id = id_baru

if st.session_state.chat_aktif_id is None:
    bikin_chat_baru()

laci_sekarang = st.session_state.kumpulan_chat[st.session_state.chat_aktif_id]


# ==========================================
# 3. SIDEBAR (MENU RIWAYAT CHAT)
# ==========================================
with st.sidebar:
    st.title("🤖 Jarvis Menu")
    
    if st.button("➕ Obrolan Baru", use_container_width=True):
        bikin_chat_baru()
        st.rerun()
        
    st.divider()
    st.write("📚 **Riwayat Obrolan**")
    
    for chat_id, data_chat in st.session_state.kumpulan_chat.items():
        label_tombol = f"**{data_chat['judul']}**" if chat_id == st.session_state.chat_aktif_id else data_chat['judul']
        if st.button(label_tombol, key=chat_id, use_container_width=True):
            st.session_state.chat_aktif_id = chat_id
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

if not laci_sekarang["histori_layar"]:
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

# Render histori chat dari LACI YANG LAGI AKTIF
for pesan in laci_sekarang["histori_layar"]:
    avatar = "🧑‍💻" if pesan["role"] == "user" else "🤖"
    with st.chat_message(pesan["role"], avatar=avatar):
        st.markdown(pesan["teks"])
        if pesan.get("gambar"):
            st.image(pesan["gambar"], width=250)
        if pesan.get("suara"):
            st.audio(pesan["suara"], format="audio/wav")
        # BARU: Tampilin info kalo pernah ngirim PDF
        if pesan.get("pdf_name"):
            st.info(f"📄 Membaca dokumen: **{pesan['pdf_name']}**")


# ==========================================
# 5. FITUR LAMPIRAN (GAMBAR & PDF) & SUARA
# ==========================================
st.write("")
with st.expander("📎 Lampirkan File / 🎙️ Rekam Suara", expanded=False):
    col_img, col_mic = st.columns(2)
    with col_img:
        # BARU: Tambah ekstensi 'pdf' di kotak uploader
        file_upload = st.file_uploader("Upload Gambar/PDF", type=['png', 'jpg', 'jpeg', 'pdf'], label_visibility="collapsed")
    with col_mic:
        suara_upload = st.audio_input("Ngobrol pake suara")
        
    if file_upload or suara_upload:
        if st.button("🚀 Kirim Lampiran/Suara", use_container_width=True):
            teks_dari_tombol = "Tolong analisis file/suara yang gue kirim ini bro."


# ==========================================
# 6. LOGIK PENGIRIMAN PESAN
# ==========================================
teks_dari_input = st.chat_input("Ketik di sini, atau upload file di atas bro...")
pertanyaan = teks_dari_input or teks_dari_tombol

if pertanyaan:
    img_pil = None
    teks_pdf = ""
    nama_pdf = None
    
    # Cek jenis file yang diupload (Gambar atau PDF)
    if file_upload:
        if file_upload.name.endswith('.pdf'):
            # EKSTRAKSI TEKS DARI PDF
            nama_pdf = file_upload.name
            pdf_reader = PyPDF2.PdfReader(file_upload)
            for page in pdf_reader.pages:
                teks_pdf += page.extract_text() + "\n"
        else:
            img_pil = Image.open(file_upload)

    if len(laci_sekarang["histori_layar"]) == 0:
        judul_pendek = pertanyaan[:20] + "..." if len(pertanyaan) > 20 else pertanyaan
        laci_sekarang["judul"] = f"💬 {judul_pendek}"

    # Simpan jejak pesan user ke memori layar
    laci_sekarang["histori_layar"].append({
        "role": "user", 
        "teks": pertanyaan if not (file_upload or suara_upload) else "*(Mengirim Lampiran)*\n\n" + pertanyaan, 
        "gambar": img_pil,
        "suara": suara_upload.getvalue() if suara_upload else None,
        "pdf_name": nama_pdf # Simpan nama PDF biar muncul di riwayat
    })
    
    # Nampilin efek di layar user
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(pertanyaan)
        if img_pil:
            st.image(img_pil, width=250)
        if suara_upload:
            st.audio(suara_upload.getvalue(), format="audio/wav")
        if nama_pdf:
            st.info(f"📄 Mengirim dokumen: **{nama_pdf}**")
    
    # Proses mikir AI
    with st.chat_message("assistant", avatar="🤖"):
        try:
            isi_pesan = []
            
            # Kalau ada PDF, kita jejalin isi teks PDF-nya barengan sama pertanyaan lu (Context Stuffing)
            if teks_pdf:
                prompt_pdf = f"Berikut adalah isi dokumen yang gue lampirkan:\n\n{teks_pdf[:50000]}\n\n---\nBerdasarkan dokumen di atas, tolong jawab: {pertanyaan}"
                isi_pesan.append(prompt_pdf)
            else:
                isi_pesan.append(pertanyaan)
                
            if img_pil:
                isi_pesan.append(img_pil)
            if suara_upload:
                audio_part = types.Part.from_bytes(data=suara_upload.getvalue(), mime_type="audio/wav")
                isi_pesan.append(audio_part)

            def generate_typing_effect():
                response_stream = laci_sekarang["chat_session"].send_message_stream(isi_pesan)
                for chunk in response_stream:
                    yield chunk.text
            
            respons_teks = st.write_stream(generate_typing_effect())
            
            laci_sekarang["histori_layar"].append({
                "role": "assistant", 
                "teks": respons_teks, 
                "gambar": None,
                "suara": None,
                "pdf_name": None
            })
            
            st.rerun() 
            
        except Exception as e:
            st.error(f"Waduh bro, Jarvis gagal baca: {e}")
