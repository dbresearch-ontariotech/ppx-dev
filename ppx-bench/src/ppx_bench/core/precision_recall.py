import pandas as pd

from ppx_align.core.types import DocAlignment, ParsedDocument


def compute_line_precision_recall(
    tree: pd.DataFrame,
    gold_doc: ParsedDocument,
    noise_doc: ParsedDocument,
    gold_alignment: DocAlignment,
    noise_alignment: DocAlignment,
    noise_level: str,
) -> pd.DataFrame:
    """Compare a noise-level alignment to the 0% gold-standard alignment at the line level.

    For each visual line in the layout tree that has a gold alignment:
      1. Block check — if the parent block's AST range differs between gold and noise, this
         is a block alignment error -> (precision=0, recall=0, is_block_error=True).
      2. Span overlap — compute absolute character spans in each markdown's own coordinate
         system (gold uses gold_doc.ast_spans, noise uses noise_doc.ast_spans, since
         corruption can shift AST node boundaries when structural characters change).
         precision = |span_gold ∩ span_noise| / |span_noise|
         recall    = |span_gold ∩ span_noise| / |span_gold|

    Lines without a gold alignment are skipped (no ground truth to compare against).
    Lines with a gold alignment but no noise alignment get (0, 0).

    Returns a DataFrame with columns: noise_level, line_id, precision, recall, is_block_error.
    """
    lines = tree[tree["level_name"] == "line"]
    rows: list[dict] = []

    for _, line in lines.iterrows():
        line_id = line["node_id"]
        block_id = line["parent_id"]

        gold_target = gold_alignment.line_alignments.get(line_id)
        if gold_target is None:
            continue

        gold_block = gold_alignment.block_alignments.get(block_id)
        noise_block = noise_alignment.block_alignments.get(block_id)
        block_error = (
            gold_block is None
            or noise_block is None
            or (gold_block.ast_start, gold_block.ast_end) != (noise_block.ast_start, noise_block.ast_end)
        )
        if block_error:
            rows.append({
                "noise_level": noise_level,
                "line_id": line_id,
                "precision": 0.0,
                "recall": 0.0,
                "is_block_error": True,
            })
            continue

        noise_target = noise_alignment.line_alignments.get(line_id)
        if noise_target is None:
            rows.append({
                "noise_level": noise_level,
                "line_id": line_id,
                "precision": 0.0,
                "recall": 0.0,
                "is_block_error": False,
            })
            continue

        g_start = gold_doc.ast_spans[gold_target.ast_index_start][0] + gold_target.char_start
        g_end = gold_doc.ast_spans[gold_target.ast_index_end][0] + gold_target.char_end
        n_start = noise_doc.ast_spans[noise_target.ast_index_start][0] + noise_target.char_start
        n_end = noise_doc.ast_spans[noise_target.ast_index_end][0] + noise_target.char_end

        overlap = max(0, min(g_end, n_end) - max(g_start, n_start))
        gold_len = g_end - g_start
        noise_len = n_end - n_start
        precision = overlap / noise_len if noise_len > 0 else 0.0
        recall = overlap / gold_len if gold_len > 0 else 0.0

        rows.append({
            "noise_level": noise_level,
            "line_id": line_id,
            "precision": precision,
            "recall": recall,
            "is_block_error": False,
        })

    return pd.DataFrame(rows)
