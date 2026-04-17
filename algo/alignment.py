import numpy as np
from typing import Tuple, List

class Alignment:
    """
    Triển khai thuật toán Quy hoạch động cho Sequence Alignment.
    Giúp tối ưu hóa thay vì dùng O(n^2) thuần với List, sử dụng ma trận Numpy.
    """
    def __init__(self, match: int = 1, mismatch: int = -1, gap: int = -2):
        self.match = match
        self.mismatch = mismatch
        self.gap = gap

    def needleman_wunsch(self, seq1: str, seq2: str) -> Tuple[float, str, str, str]:
        """
        Global Alignment (Needleman-Wunsch).
        Time / Space: O(mn)
        """
        n, m = len(seq1), len(seq2)
        score_matrix = np.zeros((n + 1, m + 1), dtype=float)

        # Khởi tạo gap penalties ở cột & dòng đầu
        for i in range(1, n + 1):
            score_matrix[i][0] = i * self.gap
        for j in range(1, m + 1):
            score_matrix[0][j] = j * self.gap

        # Tính toán ma trận
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                match_score = self.match if seq1[i-1] == seq2[j-1] else self.mismatch
                score_matrix[i][j] = max(
                    score_matrix[i-1][j-1] + match_score,      # Match/Mismatch
                    score_matrix[i-1][j] + self.gap,           # Deletion
                    score_matrix[i][j-1] + self.gap            # Insertion
                )

        # Backtracking
        align1, align2 = "", ""
        i, j = n, m
        while i > 0 or j > 0:
            if i > 0 and j > 0:
                match_score = self.match if seq1[i-1] == seq2[j-1] else self.mismatch
            else:
                match_score = None

            if i > 0 and j > 0 and score_matrix[i][j] == score_matrix[i-1][j-1] + match_score:
                align1 += seq1[i-1]
                align2 += seq2[j-1]
                i -= 1
                j -= 1
            elif i > 0 and score_matrix[i][j] == score_matrix[i-1][j] + self.gap:
                align1 += seq1[i-1]
                align2 += "-"
                i -= 1
            else:
                align1 += "-"
                align2 += seq2[j-1]
                j -= 1

        align1 = align1[::-1]
        align2 = align2[::-1]
        final_score = float(score_matrix[n][m])

        # Sợi tương đồng
        matching_str = "".join(["|" if a == b else " " for a, b in zip(align1, align2)])

        return final_score, align1, matching_str, align2

    def smith_waterman(self, seq1: str, seq2: str) -> Tuple[float, str, str, str]:
        """
        Local Alignment (Smith-Waterman).
        """
        n, m = len(seq1), len(seq2)
        score_matrix = np.zeros((n + 1, m + 1), dtype=float)
        max_score = 0
        max_pos = (0, 0)

        # Tính toán ma trận
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                match_score = self.match if seq1[i-1] == seq2[j-1] else self.mismatch
                score_matrix[i][j] = max(
                    0,
                    score_matrix[i-1][j-1] + match_score,      
                    score_matrix[i-1][j] + self.gap,           
                    score_matrix[i][j-1] + self.gap            
                )
                if score_matrix[i][j] > max_score:
                    max_score = score_matrix[i][j]
                    max_pos = (i, j)

        # Backtracking
        align1, align2 = "", ""
        i, j = max_pos
        while score_matrix[i][j] > 0:
            match_score = self.match if seq1[i-1] == seq2[j-1] else self.mismatch
            if i > 0 and j > 0 and score_matrix[i][j] == score_matrix[i-1][j-1] + match_score:
                align1 += seq1[i-1]
                align2 += seq2[j-1]
                i -= 1
                j -= 1
            elif i > 0 and score_matrix[i][j] == score_matrix[i-1][j] + self.gap:
                align1 += seq1[i-1]
                align2 += "-"
                i -= 1
            elif j > 0 and score_matrix[i][j] == score_matrix[i][j-1] + self.gap:
                align1 += "-"
                align2 += seq2[j-1]
                j -= 1
            else:
                break

        align1 = align1[::-1]
        align2 = align2[::-1]

        matching_str = "".join(["|" if a == b else " " for a, b in zip(align1, align2)])

        return float(max_score), align1, matching_str, align2
