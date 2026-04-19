import streamlit as st
import google.generativeai as genai
import time
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
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

# --- Fungsi membuat file Word ---
def create_word_document(content, topic_name):
    doc = Document()
    
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
    
    title = doc.add_heading('RENCANA PELAKSANAAN PEMBELAJARAN (RPP)', level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph(f"Topik: {topic_name}")
    doc.add_paragraph('_' * 50)
    
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            doc.add_paragraph()

        # Heading level 1 (#)
        elif line.startswith('#'):
            para = doc.add_heading(level=1)
            parts = re.split(r'(\*\*.*?\*\*|\*.*?\*)', line[1:].strip())
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    run = para.add_run(part[2:-2]); run.bold = True
                elif part.startswith('*') and part.endswith('*'):
                    run = para.add_run(part[1:-1]); run.italic = True
                else:
                    para.add_run(part)

        # Heading level 2 (##)
        elif line.startswith('##'):
            doc.add_heading(line.replace('##', '').strip(), level=2)

        # Heading level 3 (###)
        elif line.startswith('###'):
            doc.add_heading(line.replace('###', '').strip(), level=3)

        # Bullet list
        elif line.startswith('-') or line.startswith('*'):
            para = doc.add_paragraph(style='List Bullet')
            parts = re.split(r'(\*\*.*?\*\*|\*.*?\*)', line[1:].strip())
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    run = para.add_run(part[2:-2]); run.bold = True
                elif part.startswith('*') and part.endswith('*'):
                    run = para.add_run(part[1:-1]); run.italic = True
                else:
                    para.add_run(part)

        # Tabel Markdown
        elif '|' in line:
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if not hasattr(doc, 'current_table'):
                doc.current_table = doc.add_table(rows=1, cols=len(cells))
                hdr_cells = doc.current_table.rows[0].cells
                for i, cell in enumerate(cells):
                    para = hdr_cells[i].paragraphs[0]
                    parts = re.split(r'(\*\*.*?\*\*|\*.*?\*)', cell)
                    for part in parts:
                        if part.startswith('**') and part.endswith('**'):
                            run = para.add_run(part[2:-2]); run.bold = True
                        elif part.startswith('*') and part.endswith('*'):
                            run = para.add_run(part[1:-1]); run.italic = True
                        else:
                            para.add_run(part)
            else:
                row_cells = doc.current_table.add_row().cells
                for i, cell in enumerate(cells):
                    para = row_cells[i].paragraphs[0]
                    parts = re.split(r'(\*\*.*?\*\*|\*.*?\*)', cell)
                    for part in parts:
                        if part.startswith('**') and part.endswith('**'):
                            run = para.add_run(part[2:-2]); run.bold = True
                        elif part.startswith('*') and part.endswith('*'):
                            run = para.add_run(part[1:-1]); run.italic = True
                        else:
                            para.add_run(part)

        # Paragraf biasa
        else:
            para = doc.add_paragraph()
            parts = re.split(r'(\*\*.*?\*\*|\*.*?\*)', line)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    run = para.add_run(part[2:-2]); run.bold = True
                elif part.startswith('*') and part.endswith('*'):
                    run = para.add_run(part[1:-1]); run.italic = True
                else:
                    para.add_run(part)
    
    from datetime import datetime
    footer = doc.sections[0].footer
    footer_para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    footer_para.text = f"Generated by AI Lesson Plan Generator | {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    footer_para.style = doc.styles['Normal']
    footer_para.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc_bytes = BytesIO()
    doc.save(doc_bytes)
    doc_bytes.seek(0)
    return doc_bytes
