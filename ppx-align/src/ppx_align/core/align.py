from functools import cache
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from scipy.optimize import linear_sum_assignment
from rich.progress import Progress, BarColumn, TaskProgressColumn, TimeRemainingColumn, TimeElapsedColumn, TextColumn
from ppx_align.core.types import BlockAlignment, BlockAlignmentTarget, CharAlignment, CharAlignmentTarget, ParsedDocument, DocAlignment
from ppx_align.core.layout import get_visual_token
from ppx_align.core.md import get_content

@cache
def get_model(name="all-MiniLM-L6-v2") -> SentenceTransformer:
    return SentenceTransformer(name)

def get_embeddings(texts: list[str]) -> np.ndarray:
    model = get_model()
    return model.encode(texts)

def get_doc_ast_node_embeddings(doc: ParsedDocument):
    texts = ["".join(doc.lines[node.map[0]:node.map[1]]) for node in doc.ast_nodes] # type: ignore
    return get_embeddings(texts)

def get_doc_range_embeddings(doc: ParsedDocument):
    texts = []
    rng = []
    n = len(doc.ast_nodes)
    for i in range(n):
        for j in range(i+1, n+1):
            start = doc.ast_spans[i][0]
            end = doc.ast_spans[j-1][1]
            texts.append(doc.markdown[start:end])
            rng.append((i,j))
    return get_embeddings(texts), rng, texts

def get_visual_token_embeddings(rows: pd.DataFrame):
    texts = rows.content.tolist()
    return get_embeddings(texts)

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
        (int(r), int(c), float(sim[r,c])) for r, c in zip(row_idx, col_idx)
        if sim[r, c] >= threshold
    ]

def align_blocks(
        tree: pd.DataFrame,
        doc: ParsedDocument,
        threshold=0.2
    ) -> dict[str, BlockAlignmentTarget]:
    blocks = tree[tree['level_name'] == 'block']
    ve = get_visual_token_embeddings(blocks)
    te, rng, texts = get_doc_range_embeddings(doc)
    match = max_matching(ve, te, threshold)
    alignment: dict[str, BlockAlignmentTarget] = dict()
    for block_idx, rng_idx, score in match:
        node_id = blocks.iloc[block_idx].node_id
        target = BlockAlignmentTarget(ast_start=rng[rng_idx][0], ast_end=rng[rng_idx][1], score=score)
        alignment[node_id] = target

    return alignment

def align_lines(
        tree: pd.DataFrame,
        doc: ParsedDocument,
        block_id: str,
        ast_rng: tuple[int,int],
        threshold=0.2
    ) -> dict[str, CharAlignmentTarget]:
    lines_df = tree[tree["parent_id"] == block_id]
    if len(lines_df) == 0:
        return {}

    lines_emb = get_visual_token_embeddings(lines_df)

    line_lengths = lines_df["content"].str.len()
    min_chars = int(line_lengths.min()) // 2
    max_chars = int(line_lengths.max()) * 2

    # Collect word spans with their originating ast_node index
    ast_word_spans: list[tuple[int, int]] = []
    word_ast_indices: list[int] = []
    for i in range(ast_rng[0], ast_rng[1]):
        for span in doc.ast_word_spans[i]:
            ast_word_spans.append(span)
            word_ast_indices.append(i)

    texts = []
    rng: list[tuple[int, int, int, int]] = []  # (char_start, ast_idx_start, char_end, ast_idx_end)
    for i in range(len(ast_word_spans)):
        ast_idx_i = word_ast_indices[i]
        abs_start = doc.ast_spans[ast_idx_i][0] + ast_word_spans[i][0]
        for j in range(i+1, len(ast_word_spans) + 1):
            ast_idx_j = word_ast_indices[j-1]
            end = ast_word_spans[j-1][1]
            abs_end = doc.ast_spans[ast_idx_j][0] + end
            span_len = abs_end - abs_start
            if span_len > max_chars:
                break
            if span_len < min_chars:
                continue
            texts.append(doc.markdown[abs_start:abs_end])
            rng.append((ast_word_spans[i][0], ast_idx_i, end, ast_idx_j))
    if not texts:
        return {}
    txt_emb = get_embeddings(texts)

    match = max_matching(lines_emb, txt_emb, threshold)
    alignment: dict[str, CharAlignmentTarget] = dict()
    for line_idx, rng_idx, score in match:
        line = lines_df.iloc[line_idx]
        char_start, ast_idx_start, char_end, ast_idx_end = rng[rng_idx]
        alignment[line.node_id] = CharAlignmentTarget(
            ast_index_start=ast_idx_start,
            char_start=char_start,
            ast_index_end=ast_idx_end,
            char_end=char_end,
            score=score,
        )

    return alignment


def align_tree(
        tree: pd.DataFrame,
        doc: ParsedDocument,
        block_threshold: float = 0.2,
        line_threshold: float = 0.2,
        blocks_only: bool = False,
    ) -> DocAlignment:
    block_alignments = align_blocks(tree, doc, threshold=block_threshold)

    line_alignments: dict[str, CharAlignmentTarget] = {}
    if not blocks_only:
        total_lines = sum(
            len(tree[tree["parent_id"] == block_id])
            for block_id in block_alignments
        )
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        ) as progress:
            task = progress.add_task("Aligning lines", total=total_lines)
            for block_id, block_target in block_alignments.items():
                block = get_visual_token(tree, block_id) # type: ignore
                # if block['label'] == "table":
                #     continue
                ast_rng = (block_target.ast_start, block_target.ast_end)
                block_line_alignments = align_lines(
                    tree, doc, block_id, ast_rng, threshold=line_threshold
                )
                line_alignments.update(block_line_alignments)
                n_lines = len(tree[tree["parent_id"] == block_id])
                progress.advance(task, n_lines)

    return DocAlignment(
        block_alignments=block_alignments,
        line_alignments=line_alignments,
    )

def get_match_content(tree: pd.DataFrame, doc: ParsedDocument, node_id: str, target: BlockAlignmentTarget|CharAlignmentTarget) -> tuple[str, str]:
    visual = get_visual_token(tree, node_id)["content"] # type: ignore
    if isinstance(target, BlockAlignmentTarget):
        markdown = get_content(doc, block_alignment_target=target)
    else:
        markdown = get_content(doc, char_alignment_target=target)
    return visual, markdown
