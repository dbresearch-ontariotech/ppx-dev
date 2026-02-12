from collections import Counter
import numpy as np

from .models import VisualTokens, TextTokens, AlignmentResult, OCROutput


def ngram_3(words: list[str]) -> Counter:
    """Pad each word with $$ and extract character 3-grams into a Counter (multiset)."""
    bag = Counter()
    for word in words:
        padded = "$$" + word.lower() + "$$"
        bag.update(padded[i:i+3] for i in range(len(padded) - 2))
    return bag


def jaccard(bag1: Counter, bag2: Counter) -> float:
    """Multiset Jaccard using Counter & (min) and | (max)."""
    intersection = sum((bag1 & bag2).values())
    union = sum((bag1 | bag2).values())
    if union == 0:
        return 0.0
    return intersection / union


def text_from_page_neighborhood(vtokens: VisualTokens, x: int, y: int, mx: int, my: int) -> list[str]:
    """Find visual tokens whose bbox intersects the rectangle N(x,y|mx,my), return their text."""
    nx0, ny0 = x - mx // 2, y - my // 2
    nx1, ny1 = x + mx // 2, y + my // 2

    words = vtokens.words
    mask = (words['x1'] >= nx0) & (words['x0'] <= nx1) & \
           (words['y1'] >= ny0) & (words['y0'] <= ny1)
    return list(words.loc[mask, 'text'])


def text_from_text_neighborhood(ttokens: TextTokens, i: int, m: int) -> list[str]:
    """Slice tokens[i-m//2 : i+m//2+1], return as list."""
    half = m // 2
    start = max(0, i - half)
    end = min(len(ttokens.tokens), i + half + 1)
    return ttokens.tokens[start:end]


def compute_alignment(
    vtokens: VisualTokens,
    ttokens: TextTokens,
    page_locs: np.ndarray,
    text_locs: np.ndarray,
    kx: float,
    ky: float,
    k2: int,
) -> AlignmentResult:
    """Compute similarity matrix between page locations and text locations.

    Args:
        vtokens: Visual tokens from OCR.
        ttokens: Text tokens from markdown.
        page_locs: (P, 2) array of (x, y) page coordinates.
        text_locs: (T,) array of text indices.
        kx: Page neighborhood width as a fraction of page width.
        ky: Page neighborhood height as a fraction of page height.
        k2: Text neighborhood size.

    Returns:
        AlignmentResult with the full similarity matrix.
    """
    P = len(page_locs)
    T = len(text_locs)
    mx = int(kx * vtokens.page_width)
    my = int(ky * vtokens.page_height)

    # Pre-compute text-side 3-gram bags (reused across all page locations)
    text_bags = [
        ngram_3(text_from_text_neighborhood(ttokens, int(text_locs[j]), k2))
        for j in range(T)
    ]

    scores = np.zeros((P, T), dtype=np.float64)
    for i in range(P):
        x, y = int(page_locs[i, 0]), int(page_locs[i, 1])
        page_text = text_from_page_neighborhood(vtokens, x, y, mx, my)
        page_bag = ngram_3(page_text)
        for j in range(T):
            scores[i, j] = jaccard(page_bag, text_bags[j])

    return AlignmentResult(
        page_locs=page_locs,
        text_locs=text_locs,
        scores=scores,
        kx=kx,
        ky=ky,
        k2=k2,
    )


def compute_similarity(
    vtokens: VisualTokens,
    page_locs: np.ndarray,
    text: str,
    kx: float,
    ky: float,
) -> np.ndarray:
    """Compute similarity scores of page locations against a single text string.

    Args:
        vtokens: Visual tokens from OCR.
        page_locs: (P, 2) array of (x, y) page coordinates.
        text: Text to compare against (whitespace-split into words, then 3-grammed).
        kx: Page neighborhood width as a fraction of page width.
        ky: Page neighborhood height as a fraction of page height.

    Returns:
        (P,) array of similarity scores.
    """
    mx = int(kx * vtokens.page_width)
    my = int(ky * vtokens.page_height)
    text_bag = ngram_3(text.split())

    scores = np.zeros(len(page_locs), dtype=np.float64)
    for i in range(len(page_locs)):
        x, y = int(page_locs[i, 0]), int(page_locs[i, 1])
        page_bag = ngram_3(text_from_page_neighborhood(vtokens, x, y, mx, my))
        scores[i] = jaccard(page_bag, text_bag)
    return scores


def visual_tokens_from_ocr(ocr_output: OCROutput) -> VisualTokens:
    """Extract VisualTokens from an OCROutput."""
    h, w = ocr_output.np_page.shape[:2]
    return VisualTokens(
        words=ocr_output.words.reset_index(),
        page_height=h,
        page_width=w,
    )


def text_tokens_from_markdown(markdown: str) -> TextTokens:
    """Whitespace-split markdown into word tokens."""
    return TextTokens(tokens=markdown.split())
