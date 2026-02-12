from dataclasses import dataclass
import pandas as pd
import numpy as np

@dataclass(slots=True)
class OCROutput:
    np_page: np.ndarray
    ocr_result: dict
    texts: pd.DataFrame # [i, text, score, x0, y0, x1, y1]
    words: pd.DataFrame # [(seg_index, word_index), text, x0, y0, x1, y1]

@dataclass(slots=True)
class VisualTokens:
    """Bounding boxes with text from OCR."""
    words: pd.DataFrame  # columns: text, x0, y0, x1, y1
    page_height: int
    page_width: int

@dataclass(slots=True)
class TextTokens:
    """1D word token sequence (e.g. from markdown)."""
    tokens: list[str]

@dataclass(slots=True)
class AlignmentResult:
    """Similarity matrix between page locations and text locations."""
    page_locs: np.ndarray   # (P, 2) — (x, y) per row
    text_locs: np.ndarray   # (T,) — text indices
    scores: np.ndarray      # (P, T) — similarity scores
    kx: float               # page neighborhood width (fraction of page width)
    ky: float               # page neighborhood height (fraction of page height)
    k2: int                 # text neighborhood size

@dataclass(slots=True)
class StructureV3Output:
    np_page: np.ndarray
    structv3_result: dict
    layout: pd.DataFrame # [id, label, content, order, score, x0, y0, x1, y1]
    figures: dict[str, np.ndarray]
    markdown: str
