import streamlit as st
from google import genai
from google.genai import types
import datetime
from PIL import Image
import uuid
import PyPDF2
from supabase import create_client, Client

st.set_page_config(page_title="Jarvis AI", page_icon="🤖", layout="centered")

API_KEY = st.secrets["Your_API_Key"]
PIN_RAHASIA = st.secrets["App_PIN"]
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# ==========================================
# 0. KONEKSI KE DATABASE SUPABASE
# ==========================================
@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# ==========================================
# 🛠️ AMUNISI AGENT: CUSTOM PYTHON FUNCTIONS
# ==========================================
# BARU: Kita bikin fungsi matematika murni. Teks penjelasan (docstring) di bawah nama fungsi 
# WAJIB ADA karena bakal dibaca oleh Gemini buat tau kapan fungsi ini harus dipake!
def hitung_simulasi_investasi(modal_awal: float, keuntungan_bulanan: float, durasi_bulan: int) -> str:
    """
    Menghitung simulasi pertumbuhan investasi dan ROI (Return on Investment) bisnis secara akurat dan pasti.
    Gunakan fungsi ini hanya jika user meminta perhitungan investasi, ROI, atau simulasi modal/keuntungan bisnis.
    """
    total_keuntungan = keuntungan_bulanan * durasi_bulan
    total_aset = modal_awal + total_keuntungan
    roi = (total_keuntungan / modal_awal) * 100 if modal_awal > 0 else 0
    
    return f"Hasil Analisis Agent: Total aset setelah {durasi_bulan} bulan menjadi Rp{total_aset:,.0f}. Total keuntungan bersih Rp{total_keuntungan:,.0f} dengan ROI sebesar {roi:.2f}%."


# ==========================================
# 1. GERBANG LOGIN PIN RAHASIA (URL PARAMS)
# ==========================================
if st.query_params.get("kunci") == "terbuka":
    st.session_state.logged_in = True
else:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 Jarvis Security Gate")
    input_pin = st.text_input("Masukkan PIN Rahasia Lo:", type="password")
    if st.button("Unlock Jarvis 🔑", use_container_width=True):
        if input_pin == PIN_RAHASIA:
            st.query_params["kunci"] = "terbuka"
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("PIN Salah bro! Jangan macem-macem ya.")
    st.stop()

# ==========================================
# 2. INISIALISASI AI CLIENT
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
                system_instruction=f"Hari ini {tanggal_asli}. Lo Jarvis, Agent AI gaul dan cerdas. Lu bisa ngejalanin fungsi Python yang gua daftarin di tools buat ngitung investasi.",
                # BARU: Daftarin fungsi Python lo ke dalam list tools AI!
                tools=[hitung_simulasi_investasi, {"google_search": {}}] 
            )
        )
    }
    st.session_state.chat_aktif_id = id_baru

def load_chat_dari_db(session_id):
    if session_id not in st.session_state.kumpulan_chat:
        respons_db = supabase.table("obrolan_jarvis").select("*").eq("session_id", session_id).order("waktu").execute()
        data_db = respons_db.data
        
        histori_db = []
        for baris in data_db:
            histori_db.append({
                "role": baris["role"], "teks": baris["pesan"], "gambar": None, "suara": None, "pdf_name": None
            })
            
        judul_chat = "💬 Obrolan Lama"
        if data_db:
            judul_chat = f"💬 {data_db[0]['pesan'][:20]}..."

        tanggal_asli = datetime.datetime.now().strftime("%A, %d %B %Y")
        sesi_baru = st.session_state.client.chats.create(
            model="gemini-2.5-flash", 
            config=types.GenerateContentConfig(
                system_instruction=f"Hari ini {tanggal_asli}. Lo Jarvis.",
                # BARU: Pasang juga tools-nya di sesi load database
                tools=[hitung_simulasi_investasi, {"google_search": {}}] 
            )
        )
        
        st.session_state.kumpulan_chat[session_id] = {
            "judul": text_db if 'text_db' in locals() else judul_chat, 
            "histori_layar": histori_db, "chat_session": sesi_baru
        }
    st.session_state.chat_aktif_id = session_id

if st.session_state.chat_aktif_id is None:
    bikin_chat_baru()

laci_sekarang = st.session_state.kumpulan_chat[st.session_state.chat_aktif_id]

# ==========================================
# 3. SIDEBAR (RIWAYAT DATABASE)
# ==========================================
with st.sidebar:
    st.title("🤖 Jarvis Menu")
    if st.button("➕ Obrolan Baru", use_container_width=True):
        bikin_chat_baru()
        st.rerun()
    st.divider()
    st.write("📚 **Riwayat Abadi (Database)**")
    try:
        sesi_db_respons = supabase.table("obrolan_jarvis").select("session_id").execute()
        sesi_unik = list(set([baris['session_id'] for baris in sesi_db_respons.data]))
        for s_id in sesi_unik:
            label_tombol = f"Sesi: {s_id[:8]}..."
            if s_id in st.session_state.kumpulan_chat:
                label_tombol = st.session_state.kumpulan_chat[s_id]['judul']
            if st.button(label_tombol, key=f"btn_{s_id}", use_container_width=True):
                load_chat_dari_db(s_id)
                st.rerun()
    except Exception as e:
        st.warning(f"Gagal konek DB: {e}")
    st.divider()
    if st.button("🚪 Keluar / Logout", use_container_width=True):
        st.query_params.clear()
        st.session_state.logged_in = False
        st.rerun()

# ==========================================
# 4. AREA CHAT UTAMA
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
        # BARU: Ubah tombol ketiga jadi simulasi investasi biar langsung nyobain Agent-nya!
        if st.button("📈 Cek Investasi\n\nSimulasi ROI", use_container_width=True):
            teks_dari_tombol = "Coba hitung simulasi investasi kalau modal awal gua 10 juta, profit bersih 1.5 juta per bulan, selama 12 bulan. Berapa ROI gua?"

for pesan in laci_sekarang["histori_layar"]:
    avatar = "🧑‍💻" if pesan["role"] == "user" else "🤖"
    with st.chat_message(pesan["role"], avatar=avatar):
        st.markdown(pesan["teks"])
        if pesan.get("gambar"): st.image(pesan["gambar"], width=250)
        if pesan.get("suara"): st.audio(pesan["suara"], format="audio/wav")
        if pesan.get("pdf_name"): st.info(f"📄 Membaca dokumen: **{pesan['pdf_name']}**")

st.write("")
with st.expander("📎 Lampirkan File / 🎙️ Rekam Suara", expanded=False):
    col_img, col_mic = st.columns(2)
    with col_img:
        file_upload = st.file_uploader("Upload Gambar/PDF", type=['png', 'jpg', 'jpeg', 'pdf'], label_visibility="collapsed")
    with col_mic:
        suara_upload = st.audio_input("Ngobrol pake suara")
    if file_upload or suara_upload:
        if st.button("🚀 Kirim Lampiran/Suara", use_container_width=True):
            teks_dari_tombol = "Tolong analisis file/suara yang gue kirim ini bro."

# ==========================================
# 5. LOGIK PENGIRIMAN PESAN
# ==========================================
teks_dari_input = st.chat_input("Ketik di sini...")
pertanyaan = teks_dari_input or teks_dari_tombol

if pertanyaan:
    img_pil = None
    teks_pdf = ""
    nama_pdf = None
    if file_upload:
        if file_upload.name.endswith('.pdf'):
            nama_pdf = file_upload.name
            pdf_reader = PyPDF2.PdfReader(file_upload)
            for page in pdf_reader.pages: teks_pdf += page.extract_text() + "\n"
        else: img_pil = Image.open(file_upload)

    teks_tampil_user = pertanyaan if not (file_upload or suara_upload) else "*(Mengirim Lampiran)*\n\n" + pertanyaan
    if len(laci_sekarang["histori_layar"]) == 0:
        laci_sekarang["judul"] = f"💬 {teks_tampil_user[:20]}..."

    laci_sekarang["histori_layar"].append({
        "role": "user", "teks": teks_tampil_user, "gambar": img_pil, "suara": suara_upload.getvalue() if suara_upload else None, "pdf_name": nama_pdf 
    })
    
    try:
        supabase.table("obrolan_jarvis").insert({"session_id": st.session_state.chat_aktif_id, "role": "user", "pesan": teks_tampil_user}).execute()
    except Exception as e: st.toast(f"Gagal simpan ke DB: {e}")

    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(teks_tampil_user)
        if img_pil: st.image(img_pil, width=250)
        if suara_upload: st.audio(suara_upload.getvalue(), format="audio/wav")
        if nama_pdf: st.info(f"📄 Mengirim dokumen: **{nama_pdf}**")
    
    with st.chat_message("assistant", avatar="🤖"):
        try:
            isi_pesan = []
            if teks_pdf: isi_pesan.append(f"Isi dokumen:\n\n{teks_pdf[:50000]}\n\n---\nPertanyaan: {pertanyaan}")
            else: isi_pesan.append(pertanyaan)
            if img_pil: isi_pesan.append(img_pil)
            if suara_upload:
                audio_part = types.Part.from_bytes(data=suara_upload.getvalue(), mime_type="audio/wav")
                isi_pesan.append(audio_part)

            def generate_typing_effect():
                response_stream = laci_sekarang["chat_session"].send_message_stream(isi_pesan)
                for chunk in response_stream:
                    yield chunk.text
            
            respons_teks = st.write_stream(generate_typing_effect())
            
            laci_sekarang["histori_layar"].append({
                "role": "assistant", "teks": respons_teks, "gambar": None, "suara": None, "pdf_name": None
            })
            
            supabase.table("obrolan_jarvis").insert({"session_id": st.session_state.chat_aktif_id, "role": "assistant", "pesan": respons_teks}).execute()
            st.rerun() 
            
        except Exception as e: st.error(f"Waduh bro, Jarvis gagal baca: {e}")
