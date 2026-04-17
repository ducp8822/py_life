import streamlit as st
import pandas as pd
from ui.helpers import init_session_state, is_valid_email
from ui.export_utils import generate_pdf_report, generate_fasta_string
from db.ncbi_fetch import NCBIFetcher
from algo.sequence_analysis import get_basic_stats, find_orfs, translate_sequence, validate_sequence
from algo.alignment import Alignment
from viz.visualization import (
    plot_length_distribution, 
    plot_organism_pie, 
    plot_submission_timeline,
    plot_nucleotide_composition,
    plot_gc_heatmap
)

# Cấu hình giao diện Streamlit
st.set_page_config(
    page_title="AgriGene Explorer", 
    page_icon="🧬", 
    layout="wide",
    initial_sidebar_state="expanded"
)

init_session_state()

# CSS tuỳ chỉnh (Theme xanh lá)
st.markdown("""
    <style>
    .stApp {
        --primary-color: #2E8B57;
    }
    .main-header {
        color: #2E8B57;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #2E8B57;'>🧬 AgriGene Explorer</h2>", unsafe_allow_html=True)
    st.caption("Công cụ tra cứu & phân tích trình tự gen nông nghiệp từ NCBI.")
    st.divider()
    page = st.radio(
        "Nội dung",
        ["🔍 Tìm kiếm Gen", "🧬 Phân tích Trình tự", "🔬 Căn chỉnh (Alignment)", "📊 Thống kê & Visualize", "⚙️ Cài đặt"]
    )
    st.divider()
    st.markdown("**Demo Data (Đạo ôn lúa):**\n- `JN005831` (Pi54 gene)")

# ----------------- TRANG 1: TÌM KIẾM -----------------
if page == "🔍 Tìm kiếm Gen":
    st.markdown("<h1 class='main-header'>🔍 Tìm kiếm Gen Nông Nghiệp</h1>", unsafe_allow_html=True)
    
    if not st.session_state['ncbi_email']:
        st.warning("⚠️ Vui lòng cấu hình Email NCBI tại trang **Cài đặt** trước khi bắt đầu!")
    else:
        col1, col2 = st.columns(2)
        with col1:
            query = st.text_input("Từ khóa gen (VD: Pi54, rbcL):")
        with col2:
            top_agri_organisms = [
                "", "Oryza sativa", "Zea mays", "Glycine max", 
                "Solanum lycopersicum", "Triticum aestivum", 
                "Magnaporthe oryzae"
            ]
            organism = st.selectbox("Tên loài (Gợi ý):", top_agri_organisms)
            
        with st.expander("Bộ lọc nâng cao"):
            gene_type = st.selectbox("Loại gen:", ["All", "CDS", "mRNA", "rRNA", "genomic"])
            
        if st.button("🔎 Tìm kiếm", type="primary"):
            if not query and not organism:
                st.error("Vui lòng nhập ít nhất Từ khóa hoặc Tên loài!")
            else:
                with st.spinner("Đang truy vấn NCBI Entrez..."):
                    id_list = NCBIFetcher.search_sequences(
                        query, organism, gene_type, st.session_state['max_results']
                    )
                    
                    if not id_list:
                        st.info("Không tìm thấy kết quả nào phù hợp.")
                    else:
                        st.success(f"Tìm thấy {len(id_list)} sequences. Đang tải metadata...")
                        
                        progress_bar = st.progress(0)
                        df_records = NCBIFetcher.fetch_records(id_list)
                        progress_bar.progress(100)
                        
                        if not df_records.empty:
                            st.session_state['search_results'] = df_records
                            st.dataframe(df_records, use_container_width=True)
                            
                            csv = df_records.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Tải Metadata (CSV)",
                                data=csv,
                                file_name='agrigene_results.csv',
                                mime='text/csv',
                            )
                        else:
                            st.error("Không thể tải metadata cho các ID này.")

# ----------------- TRANG 2: PHÂN TÍCH -----------------
elif page == "🧬 Phân tích Trình tự":
    st.markdown("<h1 class='main-header'>🧬 Phân tích Trình tự FASTA</h1>", unsafe_allow_html=True)
    
    input_method = st.radio("Phương thức nhập:", ["Dán FASTA", "Nhập Accession ID"])
    seq_data = ""
    header = ""
    
    if input_method == "Dán FASTA":
        raw_fasta = st.text_area("Dán trình tự FASTA vào đây:", height=200)
        if raw_fasta:
            lines = raw_fasta.split('\n')
            if lines[0].startswith('>'):
                header = lines[0][1:].strip()
                seq_data = "".join(lines[1:]).replace(" ", "").replace("\n", "").replace("\r", "")
            else:
                seq_data = raw_fasta.replace(" ", "").replace("\n", "").replace("\r", "")
                header = "Custom_Sequence"
                
    else:
        acc_id = st.text_input("Nhập Accession ID (VD: JN005831):")
        if st.button("Tải FASTA"):
            if not st.session_state['ncbi_email']:
                st.error("Chưa cấu hình Email trong Cài đặt!")
            elif acc_id:
                st.session_state['loaded_acc_id'] = acc_id
                
        # Handle persistent fetch state across reruns if input didn't change
        load_target = st.session_state.get('loaded_acc_id', '')
        if load_target and input_method == "Nhập Accession ID":
            with st.spinner(f"Đang tải {load_target}..."):
                fetch_head, fetch_seq = NCBIFetcher.fetch_fasta(load_target)
                if fetch_seq:
                    header = fetch_head.strip()
                    seq_data = fetch_seq.replace(" ", "").replace("\n", "").replace("\r", "")
                    st.success("Tải thành công!")

    if seq_data:
        if not validate_sequence(seq_data):
            st.error("Trình tự không hợp lệ! Vui lòng chỉ nhập các Nucleotide cơ bản (A,T,G,C,N,U).")
        else:
            st.subheader("1. Thống kê cơ bản")
            stats = get_basic_stats(seq_data)
            orfs = find_orfs(seq_data)
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Độ dài", f"{stats['Độ dài (bp)']} bp")
            c2.metric("GC Content", f"{stats['GC Content (%)']:.2f}%")
            if stats['AT/GC Ratio'] != float('inf'):
                c3.metric("AT/GC Ratio", f"{stats['AT/GC Ratio']:.2f}")
            else:
                c3.metric("AT/GC Ratio", "INF")
            c4.metric("Số lượng ORF (>= 100nt)", len(orfs))
            
            col_plot, col_orf = st.columns([1, 1])
            with col_plot:
                fig_nuc = plot_nucleotide_composition(stats)
                st.plotly_chart(fig_nuc, use_container_width=True)
                
            with col_orf:
                st.markdown("**Danh sách ORFs tìm thấy:**")
                if orfs:
                    df_orfs = pd.DataFrame(orfs, columns=["Start (nt)", "End (nt)", "Frame"])
                    st.dataframe(df_orfs, height=300)
                else:
                    st.info("Không tìm thấy ORF nào phù hợp.")
                    
            st.subheader("2. Dịch Protein")
            if st.button("Dịch DNA sang Protein"):
                protein_seq = translate_sequence(seq_data)
                st.text_area("Chuỗi Axit Amin:", value=protein_seq, height=150)
                
            st.divider()
            st.markdown("### 📥 Tải Báo Cáo")
            pdf_bytes = generate_pdf_report(header, stats['Độ dài (bp)'], stats['GC Content (%)'], stats['AT/GC Ratio'])
            fasta_str = generate_fasta_string(header, seq_data)
            
            ex_col1, ex_col2 = st.columns(2)
            with ex_col1:
                st.download_button(
                    label="📄 Tải Report (PDF)",
                    data=pdf_bytes,
                    file_name="Sequence_Report.pdf",
                    mime="application/pdf"
                )
            with ex_col2:
                st.download_button(
                    label="🧬 Tải Trình tự (FASTA)",
                    data=fasta_str.encode('utf-8'),
                    file_name="sequence.fasta",
                    mime="text/plain"
                )

# ----------------- TRANG 2.5: ALIGNMENT -----------------
elif page == "🔬 Căn chỉnh (Alignment)":
    st.markdown("<h1 class='main-header'>🔬 Căn chỉnh Trình tự (Pairwise Alignment)</h1>", unsafe_allow_html=True)
    st.caption("Sử dụng Quy hoạch động (Dynamic Programming) để tìm kiếm độ tương đồng giữa 2 chuỗi.")
    
    col_seq1, col_seq2 = st.columns(2)
    with col_seq1:
        seq1 = st.text_area("Trình tự 1 (DNA/RNA):", placeholder="VD: GATTCGA")
    with col_seq2:
        seq2 = st.text_area("Trình tự 2 (DNA/RNA):", placeholder="VD: GACTCGA")
        
    st.markdown("### Thông số Thuật toán")
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        match_score = st.number_input("Match Score", value=1)
    with col_s2:
        mismatch_score = st.number_input("Mismatch Penalty", value=-1)
    with col_s3:
        gap_penalty = st.number_input("Gap Penalty", value=-2)
    with col_s4:
        method = st.selectbox("Phương pháp", ["Global (Needleman-Wunsch)", "Local (Smith-Waterman)"])
        
    if st.button("Bắt đầu Căn chỉnh", type="primary"):
        seq1 = seq1.replace(" ", "").replace("\n", "").replace("\r", "").upper()
        seq2 = seq2.replace(" ", "").replace("\n", "").replace("\r", "").upper()
        
        if not seq1 or not seq2:
            st.error("Vui lòng nhập đầy đủ cả hai trình tự.")
        elif len(seq1) > 1000 or len(seq2) > 1000:
            st.warning("Chiều dài tối đa hỗ trợ trên Demo Web là 1000bp để tránh Timeout.")
        elif not validate_sequence(seq1) or not validate_sequence(seq2):
            st.error("Trình tự không hợp lệ.")
        else:
            with st.spinner("Đang tính toán ma trận DP..."):
                aligner = Alignment(match_score, mismatch_score, gap_penalty)
                if method == "Global (Needleman-Wunsch)":
                    score, al1, match_line, al2 = aligner.needleman_wunsch(seq1, seq2)
                else:
                    score, al1, match_line, al2 = aligner.smith_waterman(seq1, seq2)
                    
                st.success(f"Alignment Score: **{score}**")
                
                # Format fixed width for alignment visualization
                st.markdown("### Kết quả")
                formatted_html = f"<pre style='background-color:#f0f2f6; padding: 10px; border-radius: 5px; font-family: monospace;'>Seq1: {al1}<br>      {match_line}<br>Seq2: {al2}</pre>"
                st.markdown(formatted_html, unsafe_allow_html=True)

# ----------------- TRANG 3: THỐNG KÊ -----------------
elif page == "📊 Thống kê & Visualize":
    st.markdown("<h1 class='main-header'>📊 Thống kê Hệ Dữ Liệu</h1>", unsafe_allow_html=True)
    
    df = st.session_state.get('search_results')
    
    uploaded_file = st.file_uploader("Hoặc tải lên file CSV metadata:", type=['csv'])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        
    if df is not None and not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng số Records", len(df))
        c2.metric("Số loài sinh học", df['Organism'].nunique())
        top_gene = df['Gene Type'].mode()[0] if not df['Gene Type'].empty else "N/A"
        c3.metric("Gene Type phổ biến", top_gene)
        
        st.divider()
        
        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            st.plotly_chart(plot_length_distribution(df), use_container_width=True)
        with row1_col2:
            st.plotly_chart(plot_organism_pie(df), use_container_width=True)
            
        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            st.plotly_chart(plot_submission_timeline(df), use_container_width=True)
        with row2_col2:
            st.plotly_chart(plot_gc_heatmap(df), use_container_width=True)
    else:
        st.info("Chưa có dữ liệu. Vui lòng thực hiện Tìm kiếm hoặc upload file CSV.")

# ----------------- TRANG 4: CÀI ĐẶT -----------------
elif page == "⚙️ Cài đặt":
    st.markdown("<h1 class='main-header'>⚙️ Cài đặt Hệ thống</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    **Quy định của NCBI:**
    Để sử dụng E-utilities API, bạn bắt buộc phải cung cấp địa chỉ Email. 
    API Key là tùy chọn nhưng sẽ giúp tăng giới hạn request từ 3 lên 10 requests/giây.
    """)
    
    with st.form("settings_form"):
        email_input = st.text_input("NCBI Email (Bắt buộc):", value=st.session_state['ncbi_email'])
        api_key_input = st.text_input("NCBI API Key (Tuỳ chọn):", value=st.session_state['ncbi_api_key'], type="password")
        max_res = st.slider("Max Results Limit:", min_value=10, max_value=200, value=st.session_state['max_results'], step=10)
        
        submitted = st.form_submit_button("Lưu cấu hình")
        if submitted:
            if not is_valid_email(email_input):
                st.error("Định dạng email không hợp lệ!")
            else:
                st.session_state['ncbi_email'] = email_input
                st.session_state['ncbi_api_key'] = api_key_input
                st.session_state['max_results'] = max_res
                st.success("Đã lưu cấu hình thành công!")