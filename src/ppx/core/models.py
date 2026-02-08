from dataclasses import dataclass
import pandas as pd
import numpy as np

@dataclass(slots=True)
class OCRDataFrames:
    output_image: np.ndarray
    texts: pd.DataFrame # [i, text, score, x0, y0, x1, y1]
    words: pd.DataFrame # [(seg_index, word_index), text, x0, y0, x1, y1]

@dataclass(slots=True)
class StructureV3DataFrames:
    output_image: np.ndarray
    layout: pd.DataFrame # [id, label, content, order, score, x0, y0, x1, y1]

