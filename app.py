import streamlit as st
import google.generativeai as genai
import time
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import re

# --- Konfigurasi Halaman ---
st.set_page_config(
    page_title="AI Lesson Plan Generator | Professional Edition",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS untuk tampilan lebih profesional ---
st.markdown("""
<style>
    /* Gradien background */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Card styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .result-container {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        margin-top: 2rem;
        animation: fadeIn 0.5s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Form styling */
    .stForm {
        background: rgba(255,255,255,0.95);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        font-weight: bold;
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    /* Success message styling */
    .stSuccess {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 10px;
    }
    
    /* Info box styling */
    .info-box {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="main-header">
    <h1>📚 AI Lesson Plan Generator</h1>
    <p style="font-size: 1.2rem;">Professional Edition | Powered by Google Gemini AI</p>
    <p style="font-size: 1rem; opacity: 0.9;">✨ Generate RPP berkualitas dengan muatan kearifan lokal Jawa Timur ✨</p>
</div>
""", unsafe_allow_html=True)

# --- Ambil API Key dari Streamlit Secrets ---
try:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("❌ API Key tidak ditemukan. Setup Secrets terlebih dahulu!")
    st.stop()

# --- Konfigurasi Gemini ---
MODEL_NAME = "gemini-2.5-flash"
genai.configure(api_key=gemini_api_key)

# --- Session State untuk menyimpan hasil generate ---
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = None
if 'is_generated' not in st.session_state:
    st.session_state.is_generated = False

# --- Fungsi konversi markdown ke format Word yang rapi ---
def markdown_to_word_formatting(text):
    """Mengkonversi markdown sederhana ke formatting Word"""
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        # Heading Level 1 (### atau ##)
        if line.startswith('### '):
            formatted_lines.append(('h3', line[4:].strip()))
        elif line.startswith('## '):
            formatted_lines.append(('h2', line[3:].strip()))
        elif line.startswith('# '):
            formatted_lines.append(('h1', line[2:].strip()))
        # Bold text
        elif '**' in line:
            line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
            formatted_lines.append(('bold', line))
        # List item
        elif line.strip().startswith('- '):
            formatted_lines.append(('list', line.strip()[2:]))
        elif line.strip().startswith('* '):
            formatted_lines.append(('list', line.strip()[2:]))
        # Normal paragraph
        elif line.strip():
            formatted_lines.append(('normal', line.strip()))
        else:
            formatted_lines.append(('empty', ''))
    
    return formatted_lines

def create_word_document(content):
    """Membuat file Word dengan formatting yang rapi"""
    doc = Document()
    
    # Set margin
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1.2)
        section.right_margin = Inches(1.2)
    
    # Judul utama
    title = doc.add_heading('Rencana Pelaksanaan Pembelajaran (RPP)', level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Garis pemisah
    doc.add_paragraph('_' * 60)
    
    # Proses konten
    formatted_content = markdown_to_word_formatting(content)
    
    for element_type, element_text in formatted_content:
        if element_type == 'h1':
            doc.add_heading(element_text, level=1)
        elif element_type == 'h2':
            doc.add_heading(element_text, level=2)
        elif element_type == 'h3':
            doc.add_heading(element_text, level=3)
        elif element_type == 'bold':
            p = doc.add_paragraph()
            run = p.add_run(element_text)
            run.bold = True
        elif element_type == 'list':
            p = doc.add_paragraph(element_text, style='List Bullet')
        elif element_type == 'normal':
            p = doc.add_paragraph(element_text)
            p.paragraph_format.space_after = Pt(6)
        elif element_type == 'empty':
            doc.add_paragraph()
    
    # Footer dengan timestamp
    from datetime import datetime
    footer = doc.sections[0].footer
    footer_para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    footer_para.text = f"Dokumen generated oleh AI Lesson Plan Generator | {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    footer_para.style = doc.styles['Normal']
    footer_para.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Save to bytes
    doc_bytes = BytesIO()
    doc.save(doc_bytes)
    doc_bytes.seek(0)
    
    return doc_bytes

# --- Fungsi panggil Gemini ---
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
            content = re.sub(r'^```(?:markdown)?\n?', '', content)
            content = re.sub(r'\n?```$', '', content)
            content = content.strip()
            
            return content
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if "503" in error_msg or "high demand" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 1
                    progress_bar = st.progress(0)
                    for i in range(wait_time):
                        progress_bar.progress((i + 1) / wait_time)
                        time.sleep(1)
                    progress_bar.empty()
                    st.warning(f"⚠️ Server sibuk. Mencoba ulang... (Percobaan {attempt + 1}/{max_retries})")
                else:
                    st.error("❌ Server AI sedang sangat sibuk. Silakan coba lagi nanti.")
                    return None
            else:
                st.error(f"❌ Error: {str(e)}")
                return None

# --- Form Input ---
with st.form("lesson_plan_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        topic = st.text_area(
            "📖 **Topik Pembelajaran**", 
            height=100,
            placeholder="Contoh: Memperkenalkan Tari Remo melalui Media Interaktif...",
            help="Maksimal 100 kata | Semakin spesifik, semakin baik hasilnya"
        )
        language = st.selectbox("🌐 **Bahasa Output**", ["Indonesian", "English"], index=0)
        grade = st.text_input("🎓 **Jenjang / Kelas**", placeholder="Contoh: Kelas 5 SD / Kelas X SMA")
        
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
        time_allotment = st.text_input("⏰ **Alokasi Waktu**", placeholder="Contoh: 2 x 35 Menit / 90 Menit")
    
    submitted = st.form_submit_button("🚀 **Generate Lesson Plan**", use_container_width=True)

# --- Proses Generate (hanya jika tombol ditekan) ---
if submitted:
    # Validasi input
    if not topic.strip():
        st.error("❌ Topik tidak boleh kosong!")
        st.stop()
    
    word_count = len(topic.split())
    if word_count > 100:
        st.error(f"❌ Topik melebihi 100 kata! Saat ini: {word_count} kata.")
        st.stop()
    
    # Reset session state untuk generate baru
    st.session_state.is_generated = False
    st.session_state.generated_content = None
    
    # Progress indicator
    with st.spinner("🔄 AI sedang menyusun Rencana Pembelajaran yang berkualitas... (mohon tunggu 15-30 detik)"):
        
        # Prompt (dioptimasi untuk output tanpa markdown)
        prompt = f"""
        Act as an expert Lesson Planner with 20+ years of experience. Generate a comprehensive, professional Lesson Plan based on:
        
        DETAILS:
        - Topic: {topic}
        - Language: {language}
        - Standard 1 (Core Competency): {std1}
        - Standard 2 (Learning Objectives): {std2}
        - Grade Level: {grade}
        - Time Allotment: {time_allotment}

        CULTURAL INTEGRATION:
        - Align content with the Local Wisdom of Jawa Timur (East Java)
        - Include examples from Javanese culture, traditions, and values

        STRUCTURE (Must follow EXACTLY):
        1. INITIAL COMPETENCIES (Kompetensi Awal)
        2. PANCASILA STUDENT PROFILE (Profil Pelajar Pancasila)
        3. LEARNING ACTIVITIES (Kegiatan Pembelajaran):
           - Opening Activities (Kegiatan Pendahuluan) - 15% of time
           - Core Activities (Kegiatan Inti) - 70% of time  
           - Closing Activities (Kegiatan Penutup) - 15% of time
        4. ASSESSMENT (Penilaian):
           - Attitude Assessment (Sikap)
           - Knowledge Assessment (Pengetahuan)
           - Skills Assessment (Keterampilan)

        FORMATTING RULES:
        - Response Language: {language.upper()}
        - Use simple formatting: Use **bold** for sub-headers only
        - NO markdown code blocks, NO backticks
        - NO introductory text, NO meta commentary
        - Start directly with "## INITIAL COMPETENCIES" or "## KOMPETENSI AWAL"
        - Use line breaks to separate sections
        """
        
        result = call_gemini(prompt)
        
        if result:
            st.session_state.generated_content = result
            st.session_state.is_generated = True
            st.success("✅ Lesson Plan berhasil dibuat! Scroll ke bawah untuk melihat hasil dan download.")
        else:
            st.error("❌ Gagal menghasilkan Lesson Plan. Silakan coba lagi.")

# --- Tampilkan hasil jika sudah ada di session state ---
if st.session_state.is_generated and st.session_state.generated_content:
    st.markdown('<div class="result-container">', unsafe_allow_html=True)
    
    col_download, col_info = st.columns([1, 3])
    
    with col_download:
        # Tombol download Word
        doc_file = create_word_document(st.session_state.generated_content)
        st.download_button(
            label="📥 **Download Lesson Plan (Word Document)**",
            data=doc_file,
            file_name=f"Lesson_Plan_{topic[:30].replace(' ', '_')}_{int(time.time())}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    
    with col_info:
        st.markdown("""
        <div class="info-box">
            ✅ <strong>Tips:</strong> File akan terdownload dalam format <strong>Microsoft Word (.docx)</strong><br>
            📄 Format sudah profesional dengan margin, heading, dan struktur yang rapi
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Tampilkan preview dengan styling yang lebih baik
    st.markdown("### 📄 Preview Lesson Plan")
    
    # Render konten dengan sedikit styling
    content = st.session_state.generated_content
    
    # Konversi markdown sederhana ke HTML untuk preview yang lebih baik
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'^## (.*?)$', r'<h2 style="color: #667eea; margin-top: 20px;">\1</h2>', content, flags=re.MULTILINE)
    content = re.sub(r'^### (.*?)$', r'<h3 style="color: #764ba2; margin-top: 15px;">\1</h3>', content, flags=re.MULTILINE)
    
    st.markdown(content, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.info("💡 **Catatan:** Preview ini hanya untuk dilihat. Download file Word untuk format yang lebih profesional dan siap cetak.")
