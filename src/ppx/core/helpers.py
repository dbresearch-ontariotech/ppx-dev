import fitz
from pathlib import Path
import numpy as np
import pandas as pd
from typing import Iterable
import cv2

def get_page_tensors(
    pdf_file: Path,
    dpi:int = 150,
) -> Iterable[np.ndarray]:
    doc = fitz.open(pdf_file)
    for page in doc:
        pix = page.get_pixmap(dpi=dpi)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )
        yield img
    doc.close()

def get_image_tensor(
    image_file: Path,
) -> np.ndarray:
    img = cv2.imread(str(image_file))
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

def annotate(
    np_image: np.ndarray,
    df_annotation: pd.DataFrame,
    color = None,                   # BGR encoding of color
):
    color = color or (0, 0, 255)
    overlay = np_image.copy()
    for row in df_annotation[['x0', 'y0', 'x1', 'y1']].itertuples():
        x0, y0, x1, y1 = int(row.x0), int(row.y0), int(row.x1), int(row.y1)
        cv2.rectangle(
            overlay,
            (x0, y0),
            (x1, y1),
            color,
            thickness=2,
            lineType=cv2.LINE_AA,
        )
    return overlay

