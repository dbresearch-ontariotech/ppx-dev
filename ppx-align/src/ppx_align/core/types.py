from dataclasses import dataclass
from markdown_it.tree import SyntaxTreeNode
import numpy as np
import pandas as pd
import pandera.pandas as pa
from pandera.typing import DataFrame, Series


@dataclass
class RasterDocument:
    pages: list[np.ndarray]

class LineTokenSchema(pa.DataFrameModel):
    x0: Series[int]
    y0: Series[int]
    x1: Series[int]
    y1: Series[int]
    text: Series[str]
    score: Series[float]

class WordTokenSchema(pa.DataFrameModel):
    x0: Series[int]
    y0: Series[int]
    x1: Series[int]
    y1: Series[int]
    text: Series[str]
    line_index: Series[int]

class LayoutSchema(pa.DataFrameModel):
    x0: Series[int]
    y0: Series[int]
    x1: Series[int]
    y1: Series[int]
    label: Series[str]
    score: Series[float]

class BlockSchema(pa.DataFrameModel):
    x0: Series[int]
    y0: Series[int]
    x1: Series[int]
    y1: Series[int]
    label: Series[str]
    order: Series[pd.Int64Dtype]
    content: Series[str]
    block_index: Series[int]

class FormulaSchema(pa.DataFrameModel):
    x0: Series[int]
    y0: Series[int]
    x1: Series[int]
    y1: Series[int]
    text: Series[str]
    formula_region_id: Series[int]

@dataclass
class PageLayer:
    np_page: np.ndarray
    page_index: int

@dataclass
class VisualLayers(PageLayer):
    regions: DataFrame[LayoutSchema]
    layout: DataFrame[LayoutSchema]
    blocks: DataFrame[BlockSchema]
    formulas: DataFrame[FormulaSchema]
    line_tokens: DataFrame[LineTokenSchema]
    word_tokens: DataFrame[WordTokenSchema]

class LayoutTreeSchema(pa.DataFrameModel):
    node_id: Series[str]
    level_index: Series[int]
    level_name: Series[str]
    parent_id: Series[str] = pa.Field(nullable=True)
    x0: Series[int]
    y0: Series[int]
    x1: Series[int]
    y1: Series[int]
    label: Series[str]
    content: Series[str]

@dataclass
class MarkdownDocument:
    markdown: str
    figures: dict[str, np.ndarray]

@dataclass
class ParsedDocument(MarkdownDocument):
    segments: list[SyntaxTreeNode]
    lines: list[str]
    
    # char_span for each segment
    seg_spans: list[tuple[int, int]]

    # for each segment, we have a list of tokens.
    # each token is a char_span
    word_spans: list[list[tuple[int, int]]]
