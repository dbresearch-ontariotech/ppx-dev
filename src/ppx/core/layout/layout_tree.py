from dataclasses import dataclass, fields
from typing import Callable

import pandas as pd
import numpy as np
from thefuzz import fuzz
import nltk
from nltk.tokenize import word_tokenize

nltk.download("punkt")
nltk.download("punkt_tab")

from ppx.core.algo import dp_align_nodes


def _intersection_over_child(cx0, cy0, cx1, cy1, parents: pd.DataFrame) -> pd.Series:
    """Fraction of child bbox area that overlaps each parent bbox."""
    child_area = max(1, (cx1 - cx0) * (cy1 - cy0))
    ix0 = parents["x0"].clip(lower=cx0)
    iy0 = parents["y0"].clip(lower=cy0)
    ix1 = parents["x1"].clip(upper=cx1)
    iy1 = parents["y1"].clip(upper=cy1)
    inter = ((ix1 - ix0).clip(lower=0) * (iy1 - iy0).clip(lower=0))
    return inter / child_area


def _assign_parents(
    children: pd.DataFrame,
    parent_nodes: pd.DataFrame,
    tolerance: float = 0.8,
) -> list:
    """
    For each child row, find the parent_nodes row whose bbox contains it
    (intersection/child_area >= tolerance). Returns parent node_id or None.
    """
    result = []
    for _, crow in children.iterrows():
        cx0, cy0, cx1, cy1 = int(crow["x0"]), int(crow["y0"]), int(crow["x1"]), int(crow["y1"])
        fracs = _intersection_over_child(cx0, cy0, cx1, cy1, parent_nodes)
        valid = fracs[fracs >= tolerance]
        if len(valid) > 0:
            best_i = valid.idxmax()
            result.append(parent_nodes.loc[best_i, "node_id"])
        else:
            result.append(None)
    return result


def build_layout_tree(
    regions: pd.DataFrame,
    blocks: pd.DataFrame,
    lines: pd.DataFrame,
    words: pd.DataFrame,
    tolerance: float = 0.8,
) -> pd.DataFrame:
    """
    Build a flat tree dataframe from the four layout layers.

    Hierarchy: regions > blocks > lines > words

    Output columns:
        node_id, level_index, level_name, parent_id,
        x0, y0, x1, y1, label, content
    """
    # --- Region nodes (parent_id = None) ---
    area = ((regions["x1"] - regions["x0"]) * (regions["y1"] - regions["y0"])).clip(lower=0)
    regions_sorted = regions.iloc[area.argsort()[::-1]]

    region_nodes = pd.DataFrame({
        "node_id": regions_sorted.index.astype(str),
        "level_index": 0,
        "level_name": "region",
        "parent_id": None,
        "x0": regions_sorted["x0"].values,
        "y0": regions_sorted["y0"].values,
        "x1": regions_sorted["x1"].values,
        "y1": regions_sorted["y1"].values,
        "label": regions_sorted["label"].values,
        "content": "",
    })

    # --- Block nodes (parent = region, ordered by `order` NaN-last) ---
    block_parents = _assign_parents(blocks, region_nodes, tolerance)
    block_order = blocks["order"].values

    block_nodes = pd.DataFrame({
        "node_id": blocks.index.astype(str),
        "level_index": 1,
        "level_name": "block",
        "parent_id": block_parents,
        "x0": blocks["x0"].values,
        "y0": blocks["y0"].values,
        "x1": blocks["x1"].values,
        "y1": blocks["y1"].values,
        "label": blocks["label"].values,
        "content": blocks["content"].values,
        "_order": block_order,
    }).sort_values("_order", na_position="last").drop(columns="_order").reset_index(drop=True)

    # --- Line nodes (parent = block, ordered by y0) ---
    line_parents = _assign_parents(lines, block_nodes, tolerance)

    line_nodes = pd.DataFrame({
        "node_id": "line_" + lines.index.astype(str),
        "level_index": 2,
        "level_name": "line",
        "parent_id": line_parents,
        "x0": lines["x0"].values,
        "y0": lines["y0"].values,
        "x1": lines["x1"].values,
        "y1": lines["y1"].values,
        "label": "",
        "content": lines["text"].values,
        "_y0": lines["y0"].values,
    }).sort_values("_y0").drop(columns="_y0").reset_index(drop=True)

    # --- Word nodes (parent = line via line_index FK, original order preserved) ---
    line_id_map = {idx: f"line_{idx}" for idx in lines.index}
    word_parent_ids = words["line_index"].map(line_id_map)

    word_nodes = pd.DataFrame({
        "node_id": "word_" + words.index.astype(str),
        "level_index": 3,
        "level_name": "word",
        "parent_id": word_parent_ids.values,
        "x0": words["x0"].values,
        "y0": words["y0"].values,
        "x1": words["x1"].values,
        "y1": words["y1"].values,
        "label": "",
        "content": words["text"].values,
    })

    return pd.concat(
        [region_nodes, block_nodes, line_nodes, word_nodes],
        ignore_index=True,
    )

@dataclass
class VisualTokenNode:
    node_id: str
    level_index: int
    level_name: str
    parent_id: str
    x0: int
    y0: int
    x1: int
    y1: int
    label: str
    content: str

def get_node_by_id(df: pd.DataFrame, node_id: str) -> VisualTokenNode:
    row = df[df["node_id"] == node_id].iloc[0]
    return VisualTokenNode(**{f.name: row[f.name] for f in fields(VisualTokenNode)})

def get_children(df: pd.DataFrame, node_id: str) -> list[VisualTokenNode]:
    rows = df[df["parent_id"] == node_id]
    return [VisualTokenNode(**{f.name: row[f.name] for f in fields(VisualTokenNode)}) for _, row in rows.iterrows()]

def fuzz_sim(node: VisualTokenNode, tokens: list[str]) -> float:
    if not tokens:
        return 0.0
    span = " ".join(tokens)
    return fuzz.token_sort_ratio(node.content, span) / 100.0

@dataclass
class TreeAlignment:
    tokens: list[str]
    align: dict[str, tuple[int, int]]

def align_tree(
    df: pd.DataFrame,
    root_id: str,
    text: str,
    sim: Callable[[VisualTokenNode, list[str]], float] = None,
    align_fn: Callable[[list[VisualTokenNode], list[str], Callable[[VisualTokenNode, list[str]], float], int, int], list[tuple[int, int]]] = None,
) -> TreeAlignment:
    """Recursively align every node in the layout tree to an interval of text_tokens.

    sim(node, token_slice) -> float  (token_slice is the sublist, not indices)
    Returns a dict mapping node_id -> (start, end) absolute token indices.
    """
    if align_fn is None:
        align_fn = dp_align_nodes
    if sim is None:
        sim = fuzz_sim

    text_tokens = word_tokenize(text)

    def _recurse(node_id: str, a: int, b: int, result: dict):
        result[node_id] = (a, b)
        children = get_children(df, node_id)
        if not children:
            return
        intervals = align_fn(children, text_tokens, sim, a=a, b=b)
        for child, interval in zip(children, intervals):
            _recurse(child.node_id, interval[0], interval[1], result)

    result = {}
    _recurse(root_id, 0, len(text_tokens), result)
    return TreeAlignment(tokens=text_tokens, align=result)
    