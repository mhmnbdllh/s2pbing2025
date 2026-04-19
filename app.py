import streamlit as st
import google.generativeai as genai
import time
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from io import BytesIO
import re

# --- Konfigurasi Halaman ---
st.set_page_config(
    page_title="AI Lesson Plan Generator",
    page_icon="📚",
    layout="centered"
)

# --- Header ---
st.title("📚 AI Lesson Plan Generator")
st.caption("Powered by Google Gemini AI | Generate RPP berkualitas dengan muatan kearifan lokal Jawa Timur")

# --- Ambil API Key dari Streamlit Secrets ---
try:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("❌ API Key tidak ditemukan. Setup Secrets terlebih dahulu!")
    st.stop()

# --- Konfigurasi Gemini ---
MODEL_NAME = "gemini-2.5-flash"
genai.configure(api_key=gemini_api_key)

# --- Session State untuk menyimpan hasil ---
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = None
if 'is_generated' not in st.session_state:
    st.session_state.is_generated = False
if 'current_topic' not in st.session_state:
    st.session_state.current_topic = ""

# --- Dropdown Kelas ---
kelas_options = [
    "Kelas 1 SD", "Kelas 2 SD", "Kelas 3 SD", "Kelas 4 SD", "Kelas 5 SD", "Kelas 6 SD",
    "Kelas VII SMP", "Kelas VIII SMP", "Kelas IX SMP",
    "Kelas X SMA", "Kelas XI SMA", "Kelas XII SMA"
]

# ─────────────────────────────────────────────
# HELPER: add formatted runs (bold / italic) to a paragraph
# ─────────────────────────────────────────────
def _add_inline_runs(paragraph, text):
    """
    Parse inline markdown (** bold **, * italic *, *** bold-italic ***)
    and add properly formatted runs to `paragraph`.
    """
    # Pattern captures: ***text***, **text**, *text*, plain text
    pattern = r'(\*\*\*.*?\*\*\*|\*\*.*?\*\*|\*.*?\*)'
    parts = re.split(pattern, text)
    for part in parts:
        if not part:
            continue
        if part.startswith('***') and part.endswith('***'):
            run = paragraph.add_run(part[3:-3])
            run.bold = True
            run.italic = True
        elif part.startswith('**') and part.endswith('**'):
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        elif part.startswith('*') and part.endswith('*') and len(part) > 2:
            run = paragraph.add_run(part[1:-1])
            run.italic = True
        else:
            paragraph.add_run(part)


# ─────────────────────────────────────────────
# HELPER: strip ALL markdown from a heading line before using it
# ─────────────────────────────────────────────
def _strip_markdown(text):
    """Remove bold/italic markers and leading list chars from text."""
    text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}(.*?)_{1,3}', r'\1', text)
    return text.strip()


# ─────────────────────────────────────────────
# MAIN: create_word_document  (fully rewritten)
# ─────────────────────────────────────────────
def create_word_document(content, topic_name):
    doc = Document()

    # Page margins
    for section in doc.sections:
        section.top_margin    = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin   = Inches(1)
        section.right_margin  = Inches(1)

    # ── Document title ──────────────────────────────────────────────
    title_para = doc.add_heading('RENCANA PELAKSANAAN PEMBELAJARAN (RPP)', level=1)
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = sub.add_run(f"Topik: {topic_name}")
    run.bold = True

    doc.add_paragraph('─' * 60)

    # ── Line-by-line markdown parser ────────────────────────────────
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        i += 1

        # Skip empty lines → blank paragraph for spacing
        if not stripped:
            doc.add_paragraph()
            continue

        # ── Headings: #, ##, ###, #### ──────────────────────────────
        heading_match = re.match(r'^(#{1,4})\s+(.*)', stripped)
        if heading_match:
            hashes  = heading_match.group(1)
            h_text  = _strip_markdown(heading_match.group(2))
            h_level = min(len(hashes), 4)          # cap at level 4
            doc.add_heading(h_text, level=h_level)
            continue

        # ── Numbered list: 1. item, 2. item … ───────────────────────
        num_match = re.match(r'^(\d+)[.)]\s+(.*)', stripped)
        if num_match:
            item_text = num_match.group(2)
            para = doc.add_paragraph(style='List Number')
            _add_inline_runs(para, item_text)
            continue

        # ── Bullet list: -, *, + ─────────────────────────────────────
        bullet_match = re.match(r'^[-*+]\s+(.*)', stripped)
        if bullet_match:
            item_text = bullet_match.group(1)

            # Check if it looks like a sub-bullet (indented in original)
            indent_len = len(raw) - len(raw.lstrip())
            style = 'List Bullet 2' if indent_len >= 4 else 'List Bullet'

            para = doc.add_paragraph(style=style)
            _add_inline_runs(para, item_text)
            continue

        # ── Indented bullet (spaces before - or *) ───────────────────
        indented_match = re.match(r'^(\s{2,})[-*+]\s+(.*)', raw)
        if indented_match:
            item_text = indented_match.group(2)
            para = doc.add_paragraph(style='List Bullet 2')
            _add_inline_runs(para, item_text)
            continue

        # ── Horizontal rule: ---, ***, ___ ──────────────────────────
        if re.match(r'^[-*_]{3,}$', stripped):
            doc.add_paragraph('─' * 60)
            continue

        # ── Bold-only line (acts like a sub-heading) ─────────────────
        if re.match(r'^\*\*.*\*\*$', stripped) and stripped.count('**') == 2:
            clean = stripped[2:-2]
            para  = doc.add_paragraph()
            run   = para.add_run(clean)
            run.bold = True
            run.font.size = Pt(12)
            continue

        # ── Plain paragraph (may contain inline markdown) ────────────
        para = doc.add_paragraph()
        _add_inline_runs(para, stripped)

    # ── Footer ──────────────────────────────────────────────────────
    from datetime import datetime
    footer      = doc.sections[0].footer
    footer_para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    footer_para.clear()
    footer_para.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_para.add_run(
        f"Generated by AI Lesson Plan Generator | {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )

    doc_bytes = BytesIO()
    doc.save(doc_bytes)
    doc_bytes.seek(0)
    return doc_bytes


# --- Fungsi panggil Gemini ---
def call_gemini(prompt_text):
    model = genai.GenerativeModel(MODEL_NAME)

    for attempt in range(3):
        try:
            response = model.generate_content(
                prompt_text,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 6000,
                }
            )
            content = response.text
            content = re.sub(r'^```\w*\n?', '', content)
            content = re.sub(r'\n?```$', '', content)
            return content.strip()
        except Exception as e:
            if attempt < 2 and ("503" in str(e) or "high demand" in str(e).lower()):
                time.sleep(2)
                continue
            st.error(f"Error: {str(e)}")
            return None


# --- Form Input ---
with st.form("lesson_form"):
    topic = st.text_area(
        "📖 **Topik Pembelajaran**",
        height=80,
        placeholder="Contoh: Memperkenalkan Tari Remo kepada siswa",
        help="Minimal 3 kata, maksimal 100 kata (MAX 500 KARAKTER)",
        max_chars=500
    )

    col1, col2 = st.columns(2)
    with col1:
        language = st.selectbox("🌐 Bahasa", ["Indonesian", "English"], index=0)
        grade    = st.selectbox("🎓 Kelas", kelas_options, index=4)
    with col2:
        std1 = st.text_area(
            "🎯 Standar 1 (Capaian Pembelajaran)",
            height=60,
            help="Minimal 2 kata, maksimal 25 kata (MAX 125 KARAKTER)",
            max_chars=125
        )
        std2 = st.text_area(
            "📝 Standar 2 (Tujuan Pembelajaran)",
            height=60,
            help="Minimal 2 kata, maksimal 25 kata (MAX 125 KARAKTER)",
            max_chars=125
        )

    time_minutes = st.text_input(
        "⏰ Alokasi Waktu (Menit)",
        placeholder="Contoh: 70",
        help="Hanya angka, maksimal 3 digit (contoh: 70, 90, 120)",
        max_chars=3
    )

    submitted = st.form_submit_button("🚀 Generate Lesson Plan", use_container_width=True)


# --- Validasi dan Proses Generate ---
if submitted:
    valid = True

    if not topic.strip():
        st.error("❌ Topik tidak boleh kosong!")
        valid = False
    else:
        wc = len(topic.strip().split())
        if wc < 3:
            st.error(f"❌ Topik minimal 3 kata! Saat ini: {wc} kata")
            valid = False
        elif wc > 100:
            st.error(f"❌ Topik maksimal 100 kata! Saat ini: {wc} kata")
            valid = False

    if not std1.strip():
        st.error("❌ Standar 1 tidak boleh kosong!")
        valid = False
    else:
        wc = len(std1.strip().split())
        if wc < 2:
            st.error(f"❌ Standar 1 minimal 2 kata! Saat ini: {wc} kata")
            valid = False
        elif wc > 25:
            st.error(f"❌ Standar 1 maksimal 25 kata! Saat ini: {wc} kata")
            valid = False

    if not std2.strip():
        st.error("❌ Standar 2 tidak boleh kosong!")
        valid = False
    else:
        wc = len(std2.strip().split())
        if wc < 2:
            st.error(f"❌ Standar 2 minimal 2 kata! Saat ini: {wc} kata")
            valid = False
        elif wc > 25:
            st.error(f"❌ Standar 2 maksimal 25 kata! Saat ini: {wc} kata")
            valid = False

    if not time_minutes.strip():
        st.error("❌ Alokasi waktu tidak boleh kosong!")
        valid = False
    else:
        if not time_minutes.isdigit():
            st.error("❌ Alokasi waktu harus berupa ANGKA saja (contoh: 70)")
            valid = False
        elif len(time_minutes) > 3:
            st.error("❌ Alokasi waktu maksimal 3 digit!")
            valid = False
        elif int(time_minutes) < 10:
            st.error("❌ Alokasi waktu minimal 10 menit!")
            valid = False

    if valid:
        st.session_state.current_topic = topic

        with st.spinner("AI sedang menyusun Rencana Pembelajaran..."):
            prompt = f"""
            Buat Rencana Pelaksanaan Pembelajaran (RPP) dengan detail berikut:

            Topik: {topic}
            Bahasa: {language}
            Kelas: {grade}
            Standar 1: {std1}
            Standar 2: {std2}
            Alokasi Waktu: {time_minutes} Menit

            Integrasikan kearifan lokal Jawa Timur.

            Struktur:
            1. KOMPETENSI AWAL
            2. PROFIL PELAJAR PANCASILA
            3. KEGIATAN PEMBELAJARAN (Pendahuluan, Inti, Penutup)
            4. PENILAIAN

            Gunakan format:
            ## untuk judul utama
            ### untuk sub judul
            - untuk list
            **teks** untuk penekanan

            Langsung ke konten, tanpa kata pengantar.
            """

            result = call_gemini(prompt)

            if result:
                st.session_state.generated_content = result
                st.session_state.is_generated      = True
                st.success("✅ Lesson Plan berhasil dibuat!")
            else:
                st.error("Gagal menghasilkan. Silakan coba lagi.")


# --- Tampilkan hasil jika ada ---
if st.session_state.is_generated and st.session_state.generated_content:
    st.divider()

    doc_file = create_word_document(
        st.session_state.generated_content,
        st.session_state.current_topic[:50]
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.download_button(
            label="📥 Download Lesson Plan (Word)",
            data=doc_file,
            file_name=f"Lesson_Plan_{int(time.time())}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

    st.divider()

    st.subheader("📄 Preview")
    st.markdown(st.session_state.generated_content, unsafe_allow_html=True)

    st.caption("💡 Download file Word untuk hasil cetak yang rapi.")
