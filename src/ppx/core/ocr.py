import os
from pathlib import Path
import os
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
from paddleocr import PaddleOCR, PPStructureV3
from functools import cache
from joblib.memory import Memory
import numpy as np
from pydantic import BaseModel
import pandas as pd

from .models import OCROutput, StructureV3Output

memory = Memory("./cache", verbose=0)

@cache
def get_ocr_model():
    return PaddleOCR(use_doc_unwarping=False)

@memory.cache
def ocr(
    np_page: np.ndarray,
    ocr_model: PaddleOCR|None = None,
) -> OCROutput:
    if not ocr_model:
        ocr_model = get_ocr_model()

    output = ocr_model.predict(np_page, return_word_box=True)
    result = output[0]
    # result.save_all(save_path="./output")
    data = result.json['res']
    return parse_ocr_data(data, result['doc_preprocessor_res']['output_img'])
    
def parse_ocr_data(data: dict, output_img: np.ndarray):
    rec_texts = data['rec_texts']
    rec_scores = data['rec_scores']
    rec_boxes = data['rec_boxes']
    rec_polys = data['rec_polys']
    word_boxes = data['text_word_boxes']
    word_text = data['text_word']

    # text dataframe (text, score, x0, y0, x1, y0)
    rows = []
    for i, (text, score, box) in enumerate(zip(rec_texts, rec_scores, rec_boxes)):
        rows.append([i, text, score] + box)
    df_text = pd.DataFrame(
        data=rows,
        columns=['seg_index', 'text', 'score', 'x0', 'y0', 'x1', 'y1']
    ).set_index('seg_index')
    
    # word dataframe (i, j) -> (text, x0, y0, x1, y1)
    rows = []
    for i, (words, boxes) in enumerate(zip(word_text, word_boxes)):
        for j, (text, box) in enumerate(zip(words, boxes)):
            rows.append([i, j, text] + box)
    df_words = pd.DataFrame(
        data=rows,
        columns=['seg_index', 'word_index', 'text', 'x0', 'y0', 'x1', 'y1']
    ).set_index(['seg_index', 'word_index'])

    return OCROutput(
        np_page=output_img.copy(),
        ocr_result=data,
        texts = df_text,
        words = df_words,
    )

@cache
def get_structv3_model() -> PPStructureV3:
    return PPStructureV3(use_doc_unwarping=False)

@memory.cache
def structv3(
    np_page: np.ndarray,
    model: PPStructureV3|None = None,
):
    model = model or get_structv3_model()
    output = model.predict(np_page)
    result = output[0]
    data = result.json['res']
    markdown = result._to_markdown()

    # get the layout
    parsing_res_list = data['parsing_res_list']
    layout_det_res = data['layout_det_res']['boxes']
    parsing_dict = dict()
    for block in parsing_res_list:
        box = tuple(block['block_bbox'])
        parsing_dict[box] = {
            "content": block['block_content'],
            "order": block['block_order'] or pd.NA
        }
    formula_dict = dict()
    for entry in data.get('formula_res_list', []):
        box = tuple(map(int, entry['dt_polys']))
        formula_dict[box] = {
            "content": entry['rec_formula'],
            "order": pd.NA,
        }
    
    rows = []
    for entry in layout_det_res:
        box = tuple(map(int, entry['coordinate']))
        x0, y0, x1, y1 = box
        row = {
            "label": entry['label'],
            "cls_id": entry['cls_id'],
            "x0": x0,
            "y0": y0,
            "x1": x1,
            "y1": y1,
        }
        
        if box in parsing_dict:
            row.update(parsing_dict[box])
        elif box in formula_dict:
            row.update(formula_dict[box])

        rows.append(row)

    df_layout = pd.DataFrame(data=rows)

    # get the markdown
    np_figures = {
        k: np.array(v)
        for k,v in markdown['markdown_images'].items()
    }
    markdown_text = markdown['markdown_texts']

    return StructureV3Output(
        np_page=result['doc_preprocessor_res']['output_img'].copy(),
        structv3_result=data,
        layout=df_layout,
        figures=np_figures,
        markdown=markdown_text
    )

