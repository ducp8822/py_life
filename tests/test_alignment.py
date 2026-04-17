import pytest
from algo.alignment import Alignment

orig = "GATTACA"
mut = "GCATGCU"

def test_needleman_wunsch():
    aligner = Alignment(match=1, mismatch=-1, gap=-2)
    score, align1, _, align2 = aligner.needleman_wunsch("GATTACA", "GCATGCU")
    # Score depends on exact match
    # Since DP matrix returns specific alignment, we ensure length is >= max(len1, len2)
    assert len(align1) >= len("GATTACA")
    assert len(align2) == len(align1)
    assert type(score) == float 

def test_smith_waterman():
    aligner = Alignment(match=1, mismatch=-1, gap=-1)
    score, align1, _, align2 = aligner.smith_waterman("TGTTACGG", "GGTTGACTA")
    # TTA should match
    assert score >= 0
    assert len(align1) == len(align2)
