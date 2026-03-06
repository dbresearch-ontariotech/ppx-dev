from dataclasses import dataclass
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
    order: Series[pd.Int64Dtype()]
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
class VisualTokenLayers(PageLayer):
    line_tokens: DataFrame[LineTokenSchema]
    word_tokens: DataFrame[WordTokenSchema]

@dataclass
class LayoutLayers(PageLayer):
    regions: DataFrame[LayoutSchema]
    layout: DataFrame[LayoutSchema]
    blocks: DataFrame[BlockSchema]
    formulas: DataFrame[FormulaSchema]

@dataclass
class MarkdownDocument:
    markdown: str
    figures: dict[str, np.ndarray]
