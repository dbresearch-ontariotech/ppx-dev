from functools import cache
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from scipy.optimize import linear_sum_assignment
from ppx_align.core.types import ParsedDocument

@cache
def _get_model(name="all-MiniLM-L6-v2") -> SentenceTransformer:
    return SentenceTransformer(name)

def _get_embeddings(texts: list[str]) -> np.ndarray:
    model = _get_model()
    return model.encode(texts)

def get_doc_segment_embeddings(doc: ParsedDocument):
    texts = ["".join(doc.lines[seg.map[0]:seg.map[1]]) for seg in doc.segments]
    return _get_embeddings(texts)

def get_doc_range_embeddings(doc: ParsedDocument):
    texts = []
    rng = []
    n = len(doc.segments)
    for i in range(n):
        for j in range(i+1, n):
            start = doc.seg_spans[i][0]
            end = doc.seg_spans[j-1][1]
            texts.append(doc.markdown[start:end])
            rng.append((i,j))
    return _get_embeddings(texts), rng, texts

def get_visual_token_embeddings(rows: pd.DataFrame):
    texts = rows.content.tolist()
    return _get_embeddings(texts)

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Pairwise cosine similarity between rows of a (m,d) and b (n,d). Returns (m,n)."""
    return 1.0 - cdist(a, b, metric="cosine")

def max_matching(
    a: np.ndarray,
    b: np.ndarray,
    threshold: float = 0.0,
) -> list[tuple[int, int, float]]:
    """Max-weight bipartite matching between embedding matrices a (m,d) and b (n,d).
    Returns list of (row, col) index pairs with similarity >= threshold."""
    sim = cosine_similarity(a, b)
    row_idx, col_idx = linear_sum_assignment(sim, maximize=True)
    return [
        (int(r), int(c), sim[r,c]) for r, c in zip(row_idx, col_idx)
        if sim[r, c] >= threshold
    ]

def align_blocks(tree: pd.DataFrame, doc: ParsedDocument, threshold=0.2):
    blocks = tree[tree['level_name'] == 'block']
    ve = get_visual_token_embeddings(blocks)
    te, rng, texts = get_doc_range_embeddings(doc)
    match = max_matching(ve, te, threshold)
    for block_idx, rng_idx, score in match:
        node_id = blocks.iloc[block_idx].node_id
        yield {
            "node_id": node_id,
            "segment_range": rng[rng_idx],
            "score": score,
        }

def align_lines(tree: pd.DataFrame, doc:ParsedDocument, block_id: str, seg_rng: tuple[int,int], threshold=0.2):
    lines_df = tree[tree["parent_id"] == block_id]
    lines_emb = get_visual_token_embeddings(lines_df)
    word_spans = []
    texts = []
    rng = []
    for i in range(seg_rng[0], seg_rng[1]):
        word_spans += doc.word_spans[i]
    for i in range(len(word_spans)):
        for j in range(i+1, len(word_spans)):
            start = word_spans[i][0]
            end = word_spans[j-1][1]
            texts.append(doc.markdown[start:end])
            rng.append((start, end))
    txt_emb = _get_embeddings(texts)

    match = max_matching(lines_emb, txt_emb, threshold)
    for line_idx, rng_idx, score in match:
        line = lines_df.iloc[line_idx]
        r = rng[rng_idx]
        yield {
            "line": line,
            "char_range": r,
            "score": score,
        }

