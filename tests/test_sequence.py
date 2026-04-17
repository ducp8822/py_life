import pytest
from algo.sequence_analysis import calculate_gc_content, get_basic_stats, validate_sequence, translate_sequence

def test_validate_sequence():
    assert validate_sequence("ATGC") == True
    assert validate_sequence("atgcn") == True
    assert validate_sequence("ATGCX") == False
    assert validate_sequence("123") == False

def test_calculate_gc_content():
    assert calculate_gc_content("GCGC") == 100.0
    assert calculate_gc_content("ATAT") == 0.0
    assert calculate_gc_content("ATGC") == 50.0
    assert calculate_gc_content("") == 0.0

def test_get_basic_stats():
    stats = get_basic_stats("AATTCG")
    assert stats["Độ dài (bp)"] == 6
    assert stats["%A"] == (2 / 6) * 100
    assert pytest.approx(stats["GC Content (%)"], 0.1) == 33.33

def test_get_basic_stats_invalid():
    with pytest.raises(ValueError):
        get_basic_stats("AATTCGX")

def test_translate_sequence():
    assert translate_sequence("ATG") == "M"
    assert translate_sequence("ATGCGA") == "MR"
    # Not multiple of 3
    assert translate_sequence("ATGCG") == "M" 
    assert translate_sequence("123") == "Lỗi: Trình tự đầu vào không hợp lệ."
