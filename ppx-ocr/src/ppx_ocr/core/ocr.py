import os
from pathlib import Path
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
from paddleocr import PaddleOCR, PPStructureV3
from paddlex.inference.pipelines.layout_parsing.layout_objects import LayoutBlock
from paddlex.inference.pipelines.layout_parsing.result_v2 import LayoutParsingResultV2
from paddlex.inference.pipelines.table_recognition.result import SingleTableRecognitionResult
from paddlex.inference.models.formula_recognition.result import FormulaRecResult
from functools import cache
from joblib.memory import Memory
import numpy as np
import pandas as pd
from pandera.typing import DataFrame
import cv2

from dataclasses import dataclass
from .types import (
    VisualLayers,
    BlockSchema,
    FormulaSchema,
    LayoutSchema,
    LineTokenSchema,
    WordTokenSchema,
    MarkdownDocument,
)

@dataclass
class VisualTokenLayers:
    np_page: np.ndarray
    page_index: int
    line_tokens: DataFrame[LineTokenSchema]
    word_tokens: DataFrame[WordTokenSchema]

@dataclass
class LayoutLayers:
    np_page: np.ndarray
    page_index: int
    regions: DataFrame[LayoutSchema]
    layout: DataFrame[LayoutSchema]
    blocks: DataFrame[BlockSchema]
    formulas: DataFrame[FormulaSchema]

def merge_layers(vtl: VisualTokenLayers, ll: LayoutLayers) -> VisualLayers:
    return VisualLayers(
        np_page=ll.np_page,
        page_index=ll.page_index,
        regions=ll.regions,
        layout=ll.layout,
        blocks=ll.blocks,
        formulas=ll.formulas,
        line_tokens=vtl.line_tokens,
        word_tokens=vtl.word_tokens,
    )

memory = Memory(location=None, verbose=0)

@cache
def get_ocr_model():
    return PaddleOCR(use_doc_unwarping=False)

@memory.cache
def get_visual_tokens(
    np_page: np.ndarray,
    ocr_model: PaddleOCR | None = None,
    page_index: int = 0,
) -> VisualTokenLayers:
    if not ocr_model:
        ocr_model = get_ocr_model()

    output = ocr_model.predict(np_page, return_word_box=True)
    result = output[0]
    np_page = result['doc_preprocessor_res']['output_img']

    boxes = result['rec_boxes']
    line_tokens = pd.DataFrame({
        "x0": boxes[:, 0],
        "y0": boxes[:, 1],
        "x1": boxes[:, 2],
        "y1": boxes[:, 3],
        "text": pd.Series(result['rec_texts']),
        'score': pd.Series(result['rec_scores']),
    })

    rows = []
    for line_idx, (word_boxes, word_texts) in enumerate(zip(result['text_word_boxes'], result['text_word'])):
        for ((x0, y0, x1, y1), text) in zip(word_boxes.tolist(), word_texts):
            rows.append({'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1, 'text': text, 'line_index': line_idx})
    word_tokens = pd.DataFrame(rows)

    return VisualTokenLayers(
        np_page=np_page,
        page_index=page_index,
        line_tokens=line_tokens,
        word_tokens=word_tokens,
    )


@cache
def get_structv3_model() -> PPStructureV3:
    return PPStructureV3(use_doc_unwarping=False)

def schema_to_columns(schema) -> list[str]:
    return list(schema.to_schema().columns.keys())

def prefix_index(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    df = df.copy()
    df.index = df.index.map(lambda x: f"{prefix}_{x}")
    return df

def parse_layout(result: LayoutParsingResultV2) -> DataFrame[LayoutSchema]:
    rows = []
    for box in result['layout_det_res']['boxes']:
        x0, y0, x1, y1 = list(map(int, box['coordinate']))
        rows.append({'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1, 'label': box['label'], 'score': box['score']})
    return prefix_index(pd.DataFrame(rows, columns=schema_to_columns(LayoutSchema)), "layout")

def parse_regions(result: LayoutParsingResultV2) -> DataFrame[LayoutSchema]:
    rows = []
    for region in result['region_det_res']['boxes']:
        x0, y0, x1, y1 = list(map(int, region['coordinate']))
        rows.append({'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1, 'label': region['label'], 'score': region['score']})
    return prefix_index(pd.DataFrame(rows, columns=schema_to_columns(LayoutSchema)), "region")

def parse_blocks(result: LayoutParsingResultV2) -> tuple[DataFrame[BlockSchema], dict[int, np.ndarray]]:
    block: LayoutBlock
    rows = []
    images = {}
    for block in result['parsing_res_list']:
        x0, y0, x1, y1 = block.bbox
        rows.append({
            'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1,
            'label': block.label,
            'order': pd.NA if block.order_index is None else int(block.order_index),
            'content': block.content,
            'block_index': block.index,
        })
        if block.image is not None:
            images[block.index] = block.image['img']
    return prefix_index(pd.DataFrame(rows, columns=schema_to_columns(BlockSchema)), "block"), images

def parse_formulas(result: LayoutParsingResultV2) -> tuple[DataFrame[FormulaSchema], dict[int, np.ndarray]]:
    res: FormulaRecResult
    rows = []
    images = {}
    for res in result['formula_res_list']:
        x0, y0, x1, y1 = list(map(int, res['dt_polys']))
        rows.append({
            'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1,
            'text': res['rec_formula'],
            'formula_region_id': res['formula_region_id'],
        })
        if res['input_img'] is not None:
            images[res['formula_region_id']] = res['input_img']
    return prefix_index(pd.DataFrame(rows, columns=schema_to_columns(FormulaSchema)), "formula"), images

@memory.cache
def get_structv3(
    np_page: np.ndarray,
    model: PPStructureV3 | None = None,
    page_index: int = 0,
) -> tuple[LayoutLayers, MarkdownDocument]:
    model = model or get_structv3_model()
    output = model.predict(np_page, return_word_box=False)
    result = output[0]

    np_page = result['doc_preprocessor_res']['output_img'].copy()

    layout_layers = LayoutLayers(
        np_page=np_page,
        page_index=page_index,
        regions=parse_regions(result),
        layout=parse_layout(result),
        blocks=parse_blocks(result)[0],
        formulas=parse_formulas(result)[0],
    )

    markdown = result._to_markdown()
    figures = {k: cv2.cvtColor(np.array(v), cv2.COLOR_BGR2RGB) for k, v in markdown['markdown_images'].items()}
    markdown_doc = MarkdownDocument(markdown=markdown['markdown_texts'], figures=figures)
    return layout_layers, markdown_doc
