from fpdf import FPDF
import io

def generate_fasta_string(header: str, sequence: str) -> str:
    """Tạo chuỗi FASTA format chuẩn với độ dài 80 ký tự/dòng."""
    fasta = f">{header}\n"
    # Chia nhỏ dòng 80 kí tự
    for i in range(0, len(sequence), 80):
        fasta += sequence[i:i+80] + "\n"
    return fasta

class PDFReport(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 15)
        self.cell(0, 10, 'AgriGene Explorer - Sequence Analysis Report', border=False, ln=1, align='C')
        self.ln(10)

    def chapter_title(self, title):
        self.set_font('Helvetica', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 8, title, 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Helvetica', '', 12)
        self.multi_cell(0, 6, body)
        self.ln()

def generate_pdf_report(seq_header: str, seq_len: int, gc_content: float, at_gc_ratio: float, alignment_res=None) -> bytes:
    """Tạo báo cáo PDF cơ bản."""
    pdf = PDFReport()
    pdf.add_page()
    
    # Overview
    pdf.chapter_title('1. Basic Statistics')
    body = f"Sequence Name/Header: {seq_header[:100]}...\n"
    body += f"Length (bp): {seq_len}\n"
    body += f"GC Content: {gc_content:.2f}%\n"
    body += f"AT/GC Ratio: {at_gc_ratio:.2f}\n"
    pdf.chapter_body(body)
    
    # Alignment (If any)
    if alignment_res:
        pdf.chapter_title('2. Alignment Score Preview')
        body_align = f"Score: {alignment_res['score']}\n"
        pdf.chapter_body(body_align)

    output = io.BytesIO()
    # Output to BytesIO -> getvalue
    out_val = pdf.output(dest='S')
    if isinstance(out_val, str):
        return out_val.encode('latin1')
    return bytes(out_val)
