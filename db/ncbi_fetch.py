import time
import urllib.error
import pandas as pd
import streamlit as st
from Bio import Entrez, SeqIO
from typing import List, Tuple, Optional, Any

class NCBIFetcher:
    """Class hỗ trợ tương tác với NCBI Entrez API."""

    @staticmethod
    def _apply_rate_limit() -> None:
        """
        Xử lý rate limit của NCBI. 
        Tối đa 3 requests/giây (nếu không có API key) hoặc 10 requests/giây (có API key).
        """
        delay = 0.11 if st.session_state.get('ncbi_api_key') else 0.34
        time.sleep(delay)

    @staticmethod
    def _setup_entrez() -> None:
        """Thiết lập thông tin xác thực cho Entrez."""
        email = st.session_state.get('ncbi_email')
        if not email:
            raise ValueError("Vui lòng thiết lập Email trong trang 'Cài đặt' trước khi tìm kiếm.")
        Entrez.email = email
        api_key = st.session_state.get('ncbi_api_key')
        if api_key:
            Entrez.api_key = api_key

    @staticmethod

    def search_sequences(query: str, organism: str, gene_type: str, max_results: int = 50) -> List[str]:
        """
        Tìm kiếm trình tự trên Nucleotide database.
        
        Args:
            query (str): Từ khóa tìm kiếm (ví dụ tên gen).
            organism (str): Tên loài (ví dụ: 'Oryza sativa').
            gene_type (str): Loại gen (CDS, mRNA, rRNA, etc.).
            max_results (int): Số lượng kết quả tối đa.
            
        Returns:
            List[str]: Danh sách các Accession IDs.
        """
        NCBIFetcher._setup_entrez()
        
        search_term = f"({query}[Gene])" if query else ""
        if organism:
            search_term += f" AND ({organism}[Organism])" if search_term else f"({organism}[Organism])"
        if gene_type and gene_type != "All":
            search_term += f" AND ({gene_type}[Feature key])" if search_term else f"({gene_type}[Feature key])"

        try:
            NCBIFetcher._apply_rate_limit()
            handle = Entrez.esearch(db="nucleotide", term=search_term, retmax=max_results, retmode="xml")
            record = Entrez.read(handle)
            handle.close()
            return record.get("IdList", [])
        except urllib.error.URLError as e:
            st.error(f"Lỗi kết nối mạng: {e.reason}")
            return []
        except urllib.error.HTTPError as e:
            st.error(f"Lỗi HTTP từ NCBI: {e.code}")
            return []
        except Exception as e:
            err_msg = str(e)
            if "mismatched tag" in err_msg or "XML" in err_msg:
                st.error("Lỗi Parsing từ NCBI: Máy chủ NCBI hiện đang quá tải hoặc tạm thời chặn yêu cầu do tần suất cao (trả về HTML lỗi thay vì XML). Vui lòng chờ 1-2 phút rồi ấn Tìm kiếm lại, hoặc cấu hình thêm API Key ở mục Cài đặt để đường truyền ổn định hơn.")
            else:
                st.error(f"Lỗi không xác định khi tìm kiếm: {err_msg}")
            return []

    @staticmethod
    def fetch_records(id_list: List[str], rettype: str = 'gb') -> pd.DataFrame:
        """
        Lấy GenBank records từ danh sách ID và parse metadata thành DataFrame.
        """
        if not id_list:
            return pd.DataFrame()

        NCBIFetcher._setup_entrez()
        data = []
        
        try:
            NCBIFetcher._apply_rate_limit()
            handle = Entrez.efetch(db="nucleotide", id=id_list, rettype=rettype, retmode="text")
            raw_data = handle.read()
            if isinstance(raw_data, bytes):
                raw_data = raw_data.decode('utf-8')
                
            if "<html" in raw_data[:500].lower() or "ErrorBlockedDiagnostic" in raw_data:
                st.error("Lỗi từ NCBI: Địa chỉ IP của bạn đã bị chặn tạm thời do giới hạn truy cập. Vui lòng điền API Key hoặc đợi 15 phút.")
                return pd.DataFrame()
                
            from io import StringIO
            records = SeqIO.parse(StringIO(raw_data), rettype)
            
            for rec in records:
                organism = rec.annotations.get("organism", "Unknown")
                date = rec.annotations.get("date", "Unknown")
                
                g_type = "Genomic"
                for feature in rec.features:
                    if feature.type in ["CDS", "mRNA", "rRNA", "tRNA"]:
                        g_type = feature.type
                        break

                data.append({
                    "Accession": rec.id,
                    "Organism": organism,
                    "Description": rec.description[:100] + "..." if len(rec.description) > 100 else rec.description,
                    "Length": len(rec.seq),
                    "Gene Type": g_type,
                    "Submission Date": date
                })
            handle.close()
            return pd.DataFrame(data)
        except urllib.error.URLError as e:
            st.error(f"Lỗi kết nối mạng khi tải records: {e.reason}")
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Lỗi khi tải metadata: {str(e)}")
            return pd.DataFrame()

    @staticmethod
    def fetch_fasta(accession_id: str) -> Tuple[str, str]:
        """
        Fetch trình tự FASTA bằng Accession ID.
        """
        NCBIFetcher._setup_entrez()
        try:
            NCBIFetcher._apply_rate_limit()
            handle = Entrez.efetch(db="nucleotide", id=accession_id, rettype="fasta", retmode="text")
            raw_data = handle.read()
            if isinstance(raw_data, bytes):
                raw_data = raw_data.decode('utf-8')
                
            if "<html" in raw_data[:500].lower() or "ErrorBlockedDiagnostic" in raw_data:
                # Tự động chuyển hướng (Fallback) sang máy chủ Châu Âu (ENA) nếu NCBI chặn
                import requests
                ena_url = f"https://www.ebi.ac.uk/ena/browser/api/fasta/{accession_id}"
                try:
                    r = requests.get(ena_url, timeout=10)
                    if r.status_code == 200 and r.text.startswith(">"):
                        raw_data = r.text
                    else:
                        st.error("Lỗi từ NCBI (IP bị chặn) và máy chủ dự phòng Châu Âu (ENA) không phản hồi.")
                        return "", ""
                except:
                    st.error("Lỗi từ NCBI: Địa chỉ IP của bạn đã bị chặn tạm thời do truy cập quá tải. Vui lòng nhập NCBI API Key ở Cài đặt.")
                    return "", ""
            
            # Filter comments / extra blank lines before ">"
            first_index = raw_data.find('>')
            if first_index != -1:
                raw_data = raw_data[first_index:]
                
            from io import StringIO
            record = SeqIO.read(StringIO(raw_data), "fasta")
            handle.close()
            return record.description, str(record.seq)
        except Exception as e:
            # Fallback: Kích hoạt tải từ ENA (Châu Âu) nếu dính bất kỳ HTTP Error / Rate Limit nào từ NCBI
            import requests
            try:
                r = requests.get(f"https://www.ebi.ac.uk/ena/browser/api/fasta/{accession_id}", timeout=10)
                if r.status_code == 200 and r.text.startswith(">"):
                    from io import StringIO
                    record = SeqIO.read(StringIO(r.text[r.text.find('>'):]), "fasta")
                    return record.description, str(record.seq)
            except Exception as ena_e:
                pass
            st.error(f"Lỗi từ NCBI ({str(e)}) & Fallback lỗi. Hãy nhập API Key!")
            return "", ""
