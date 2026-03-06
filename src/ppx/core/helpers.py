import fitz
from pathlib import Path
import numpy as np
import pandas as pd
import cv2

from .types import RasterDocument

def get_page_tensors(
    pdf_file: Path,
    dpi: int = 150,
) -> RasterDocument:
    pages = []
    doc = fitz.open(pdf_file)
    for page in doc:
        pix = page.get_pixmap(dpi=dpi)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        pages.append(img)
    doc.close()
    return RasterDocument(pages=pages)

def get_image_tensor(
    image_file: Path,
) -> np.ndarray:
    img = cv2.imread(str(image_file))
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

def draw_bboxes(
    np_image: np.ndarray,
    df_annotation: pd.DataFrame,
    color = None,                   # BGR encoding of color
    label_column: str | None = None,
    opacity: float = 0.5,
)->np.ndarray:
    color = color or (0, 0, 255)
    overlay = np_image.copy()

    cols = ['x0', 'y0', 'x1', 'y1']
    if label_column:
        cols.append(label_column)

    for row in df_annotation[cols].itertuples():
        x0, y0, x1, y1 = int(row.x0), int(row.y0), int(row.x1), int(row.y1)
        cv2.rectangle(
            overlay,
            (x0, y0),
            (x1, y1),
            color,
            thickness=1,
            lineType=cv2.LINE_AA,
        )
        if label_column:
            label = str(getattr(row, label_column))
            cv2.putText(
                overlay,
                label,
                (x0, y0 - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
                cv2.LINE_AA,
            )
    return cv2.addWeighted(np_image, 1 - opacity, overlay, opacity, 0)

def draw_graph(
    np_image: np.ndarray,
    df_graph_coords: pd.DataFrame,
    color = None,
    opacity: float = 0.5,
    line_width: int = 1,
    circle_size: int = 4,
)->np.ndarray:
    color = color or (255, 0, 0) # BGR encoding of color
    overlay = np_image.copy()
    nodes = set()
    for row in df_graph_coords.itertuples():
        x_s, y_s = int(row.x_s), int(row.y_s)
        x_t, y_t = int(row.x_t), int(row.y_t)
        cv2.line(overlay, (x_s, y_s), (x_t, y_t), color, thickness=line_width, lineType=cv2.LINE_AA)
        nodes.add((x_s, y_s))
        nodes.add((x_t, y_t))
    for (x, y) in nodes:
        cv2.circle(overlay, (x, y), radius=circle_size, color=color, thickness=-1, lineType=cv2.LINE_AA)
    return cv2.addWeighted(np_image, 1 - opacity, overlay, opacity, 0)