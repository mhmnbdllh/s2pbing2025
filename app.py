import streamlit as st
import google.generativeai as genai
import time

# --- Konfigurasi Halaman ---
st.set_page_config(
    page_title="AI Lesson Plan Generator",
    page_icon="📚",
    layout="wide"
)

# --- Ambil API Key dari Streamlit Secrets ---
try:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("❌ API Key tidak ditemukan. Setup Secrets terlebih dahulu!")
    st.stop()

# --- Konfigurasi Gemini ---
MODEL_NAME = "gemini-2.5-flash"
genai.configure(api_key=gemini_api_key)

# --- Title ---
st.title("📚 AI Lesson Plan Generator")
st.markdown("*Buat Rencana Pembelajaran (RPP) berbasis AI dengan muatan kearifan lokal Jawa Timur*")

# --- Form Input ---
with st.form("lesson_plan_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        topic = st.text_area(
            "📖 **Topik Pembelajaran**", 
            height=100,
            placeholder="Contoh: Memperkenalkan Tari Remo melalui Media Interaktif...",
            help="Maksimal 100 kata"
        )
        language = st.selectbox("🌐 **Bahasa Output**", ["Indonesian", "English"], index=0)
        grade = st.text_input("🎓 **Jenjang / Kelas**", placeholder="Contoh: Kelas 5 SD / Umum")
        
    with col2:
        std1 = st.text_area(
            "🎯 **Standar 1 (Capaian Pembelajaran)**", 
            height=80,
            placeholder="Contoh: Memahami prosedur gerak tari tradisional..."
        )
        std2 = st.text_area(
            "📝 **Standar 2 (Tujuan Pembelajaran)**", 
            height=80,
            placeholder="Contoh: Mempraktikkan gerak dasar Tari Remo..."
        )
        time_allotment = st.text_input("⏰ **Alokasi Waktu**", placeholder="Contoh: 2 x 35 Menit")
    
    submitted = st.form_submit_button("🚀 **Generate Lesson Plan**", use_container_width=True)

# --- Fungsi Panggil Gemini dengan Retry ---
def call_gemini(prompt_text):
    model = genai.GenerativeModel(MODEL_NAME)
    
    generation_config = {
        "temperature": 0.7,
        "max_output_tokens": 6000,
    }
    
    max_retries = 5
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt_text,
                generation_config=generation_config
            )
            
            content = response.text
            
            # Bersihkan markdown wrapper
            content = content.replace("```markdown", "").replace("```", "").strip()
            
            return content
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if "503" in error_msg or "high demand" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 1
                    st.warning(f"⚠️ Server sibuk. Mencoba ulang dalam {wait_time} detik... (Percobaan {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    st.error("❌ Server AI sedang sangat sibuk. Silakan coba lagi nanti.")
                    return None
            else:
                st.error(f"❌ Error: {str(e)}")
                return None

# --- Proses Generate ---
if submitted:
    # Validasi word count
    word_count = len(topic.split())
    
    if word_count > 100:
        st.error(f"❌ Topik melebihi 100 kata! Saat ini: {word_count} kata.")
        st.stop()
    
    if not topic.strip():
        st.error("❌ Topik tidak boleh kosong!")
        st.stop()
    
    # Progress indicator
    with st.spinner("🔄 Sedang menyusun Rencana Pembelajaran... (mohon tunggu hingga 30 detik)"):
        
        # Prompt (sama persis dengan versi Google Apps Script)
        prompt = f"""
        Act as an expert Lesson Planner. Generate a comprehensive Lesson Plan based on:
        - Topic: {topic}
        - Language: {language}
        - Standard 1: {std1}
        - Standard 2: {std2}
        - Grade Level: {grade}
        - Time Allotment: {time_allotment}

        Cultural & Religious Integration:
        - Align content with the Local Wisdom of Jawa Timur (East Java).

        Structure Requirements:
        1. Response Language: {language.upper()}.
        2. Format: Clean Markdown (No backticks at the start/end).
        3. Sections: Initial Competencies, Pancasila Student Profile, Activities (Opening, Core, Closing), and Assessment.
        
        Constraint: No introductory or meta-talk. Just the plan.
        """
        
        result = call_gemini(prompt)
        
        if result:
            st.success("✅ Lesson Plan berhasil dibuat!")
            st.markdown(result)
            
            # Tombol download
            st.download_button(
                label="📥 Download Lesson Plan (Markdown)",
                data=result,
                file_name=f"lesson_plan_{topic[:30].replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True
            )
        else:
            st.error("❌ Gagal menghasilkan Lesson Plan. Silakan coba lagi.")
