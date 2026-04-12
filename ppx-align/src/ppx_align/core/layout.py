from dataclasses import dataclass, fields
from typing import Protocol

from pydantic import BaseModel

import pandas as pd
import numpy as np
from thefuzz import fuzz
import nltk
from nltk.tokenize import TreebankWordTokenizer

from ppx_align.core.types import VisualLayers, LayoutTreeSchema
from ppx_align.core.algo import dp_align_nodes, hybrid_align_nodes, greedy_align_nodes
from pandera.typing import DataFrame

nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

def _intersection_over_child(cx0, cy0, cx1, cy1, parents: pd.DataFrame) -> pd.Series:
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
    vl: VisualLayers,
    tolerance: float = 0.8,
) -> DataFrame[LayoutTreeSchema]:
    area = ((vl.regions["x1"] - vl.regions["x0"]) * (vl.regions["y1"] - vl.regions["y0"])).clip(lower=0)
    regions_sorted = vl.regions.iloc[area.argsort()[::-1]]

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

    block_parents = _assign_parents(vl.blocks, region_nodes, tolerance)
    block_order = vl.blocks["order"].values

    block_nodes = pd.DataFrame({
        "node_id": vl.blocks.index.astype(str),
        "level_index": 1,
        "level_name": "block",
        "parent_id": block_parents,
        "x0": vl.blocks["x0"].values,
        "y0": vl.blocks["y0"].values,
        "x1": vl.blocks["x1"].values,
        "y1": vl.blocks["y1"].values,
        "label": vl.blocks["label"].values,
        "content": vl.blocks["content"].values,
        "_order": block_order,
    }).sort_values("_order", na_position="last").drop(columns="_order").reset_index(drop=True)

    line_parents = _assign_parents(vl.line_tokens, block_nodes, tolerance)

    line_nodes = pd.DataFrame({
        "node_id": "line_" + vl.line_tokens.index.astype(str),
        "level_index": 2,
        "level_name": "line",
        "parent_id": line_parents,
        "x0": vl.line_tokens["x0"].values,
        "y0": vl.line_tokens["y0"].values,
        "x1": vl.line_tokens["x1"].values,
        "y1": vl.line_tokens["y1"].values,
        "label": "",
        "content": vl.line_tokens["text"].values,
        "_y0": vl.line_tokens["y0"].values,
    }).sort_values("_y0").drop(columns="_y0").reset_index(drop=True)

    line_id_map = {idx: f"line_{idx}" for idx in vl.line_tokens.index}
    word_parent_ids = vl.word_tokens["line_index"].map(line_id_map)

    word_nodes = pd.DataFrame({
        "node_id": "word_" + vl.word_tokens.index.astype(str),
        "level_index": 3,
        "level_name": "word",
        "parent_id": word_parent_ids.values,
        "x0": vl.word_tokens["x0"].values,
        "y0": vl.word_tokens["y0"].values,
        "x1": vl.word_tokens["x1"].values,
        "y1": vl.word_tokens["y1"].values,
        "label": "",
        "content": vl.word_tokens["text"].values,
    })

    return pd.concat(
        [region_nodes, block_nodes, line_nodes, word_nodes],
        ignore_index=True,
    )  # type: ignore

def get_largest_region(tree: DataFrame[LayoutTreeSchema]) -> str:
    regions = tree[tree["level_name"] == "region"]
    areas = (regions["x1"] - regions["x0"]) * (regions["y1"] - regions["y0"])
    return regions.loc[areas.idxmax(), "node_id"]  # type: ignore

def get_visual_token(tree: DataFrame, node_id: str) -> pd.Series:
    matches = tree[tree["node_id"] == node_id]
    if matches.empty:
        raise KeyError(f"node_id {node_id!r} not found in tree")
    return matches.iloc[0]