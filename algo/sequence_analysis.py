from Bio.Seq import Seq
from Bio.SeqUtils import gc_fraction
from typing import List, Dict, Tuple, Any

def validate_sequence(sequence: str) -> bool:
    """Xác thực chuỗi xem có phải sequence hợp lệ không (hỗ trợ mã IUPAC Nucleotide)."""
    valid_chars = set("ATGCURYSWKMBDHVN-")
    seq_upper = sequence.upper()
    # Kiểm tra chỉ chứa các kí tự hợp lệ
    return all(char in valid_chars for char in seq_upper)

def calculate_gc_content(sequence: str) -> float:
    """Tính % GC content."""
    if not sequence:
        return 0.0
    return gc_fraction(sequence) * 100

def find_orfs(sequence: str, min_length: int = 100) -> List[Tuple[int, int, int]]:
    """Tìm ORFs trên sợi thuận."""
    if not validate_sequence(sequence):
        return []
    
    seq_obj = Seq(sequence).upper()
    orfs = []
    
    for frame in range(3):
        trans = str(seq_obj[frame:].translate(to_stop=False))
        trans_len = len(trans)
        
        start_aa_pos = -1
        for i in range(trans_len):
            if trans[i] == 'M' and start_aa_pos == -1:
                start_aa_pos = i  
            elif trans[i] == '*' and start_aa_pos != -1:
                orf_length = (i - start_aa_pos) * 3
                if orf_length >= min_length:
                    start_nt = frame + start_aa_pos * 3
                    end_nt = start_nt + orf_length + 3 
                    orfs.append((start_nt, end_nt, frame + 1))
                start_aa_pos = -1
                
    return sorted(orfs, key=lambda x: x[0])

def get_basic_stats(sequence: str) -> Dict[str, Any]:
    """Các số liệu thống kê cơ bản."""
    seq = sequence.upper()
    length = len(seq)
    
    if length == 0:
        return {}
    if not validate_sequence(seq):
        raise ValueError("Invalid nucleotide sequence provided.")

    a_count = seq.count('A')
    t_count = seq.count('T')
    g_count = seq.count('G')
    c_count = seq.count('C')
    n_count = seq.count('N')
    
    at_count = a_count + t_count
    gc_count = g_count + c_count
    
    return {
        "Độ dài (bp)": length,
        "%A": (a_count / length) * 100,
        "%T": (t_count / length) * 100,
        "%G": (g_count / length) * 100,
        "%C": (c_count / length) * 100,
        "%N (Unknown)": (n_count / length) * 100,
        "GC Content (%)": calculate_gc_content(seq),
        "AT/GC Ratio": (at_count / gc_count) if gc_count > 0 else float('inf'),
        "Codon ATG": seq.count('ATG')
    }

def translate_sequence(sequence: str) -> str:
    """Dịch trình tự DNA sang chuỗi protein."""
    if not validate_sequence(sequence):
        return "Lỗi: Trình tự đầu vào không hợp lệ."
    try:
        seq_obj = Seq(sequence)
        remainder = len(seq_obj) % 3
        if remainder != 0:
            seq_obj = seq_obj[:-remainder]
        return str(seq_obj.translate())
    except Exception as e:
        return f"Lỗi dịch mã: {str(e)}"
