# Data Models

The core data models are defined in `src/ppx/core/models.py` as Python
dataclasses. They represent the outputs of the two main OCR pipeline stages.

---

## OCROutput

Produced by the `ocr()` function. Represents text recognition results from
PaddleOCR.

### Fields

| Field     | Type           | Description                                      |
|-----------|----------------|--------------------------------------------------|
| `np_page` | `np.ndarray`   | Preprocessed page image (H x W x 3, RGB, uint8). |
| `texts`   | `pd.DataFrame` | Segment-level recognized text with bounding boxes. |
| `words`   | `pd.DataFrame` | Word-level recognized text with bounding boxes.    |

### `texts` DataFrame

Indexed by `seg_index` (int). Each row is one detected text segment.

| Column  | Type    | Description                          |
|---------|---------|--------------------------------------|
| `text`  | `str`   | Recognized text string.              |
| `score` | `float` | Recognition confidence score (0–1).  |
| `x0`    | `int`   | Left x of bounding box.             |
| `y0`    | `int`   | Top y of bounding box.              |
| `x1`    | `int`   | Right x of bounding box.            |
| `y1`    | `int`   | Bottom y of bounding box.           |

### `words` DataFrame

Multi-indexed by `(seg_index, word_index)`. Each row is one word within a
text segment.

| Column  | Type  | Description                |
|---------|-------|----------------------------|
| `text`  | `str` | Word text.                 |
| `x0`    | `int` | Left x of bounding box.   |
| `y0`    | `int` | Top y of bounding box.    |
| `x1`    | `int` | Right x of bounding box.  |
| `y1`    | `int` | Bottom y of bounding box. |

Words are children of text segments — `seg_index` links a word back to its
parent row in `texts`.

---

## StructureV3Output

Produced by the `structv3()` function. Represents document structure analysis
from PPStructureV3, including layout detection, content extraction, and
markdown conversion.

### Fields

| Field      | Type                    | Description                                         |
|------------|-------------------------|-----------------------------------------------------|
| `np_page`  | `np.ndarray`            | Preprocessed page image (H x W x 3, RGB, uint8).   |
| `layout`   | `pd.DataFrame`          | Layout regions with labels, content, and ordering.  |
| `figures`  | `dict[str, np.ndarray]` | Extracted figure images keyed by name.              |
| `markdown` | `str`                   | Full page content as Markdown text.                 |

### `layout` DataFrame

Auto-indexed. Each row is one detected layout region.

| Column    | Type           | Description                                              |
|-----------|----------------|----------------------------------------------------------|
| `label`   | `str`          | Region type (e.g. `"text"`, `"title"`, `"table"`, `"figure"`). |
| `cls_id`  | `int`          | Numeric class ID for the region type.                    |
| `x0`      | `int`          | Left x of bounding box.                                 |
| `y0`      | `int`          | Top y of bounding box.                                   |
| `x1`      | `int`          | Right x of bounding box.                                 |
| `y1`      | `int`          | Bottom y of bounding box.                                |
| `content` | `str` or absent | Extracted text/HTML content for the region.             |
| `order`   | `int` or `NA`  | Reading order position. `NA` for regions without order (e.g. formulas). |

Content comes from two sources: `parsing_res_list` provides text and table
content with reading order, while `formula_res_list` provides recognized
LaTeX formulas (with order set to `NA`).

### `figures`

Maps figure names (as referenced in the markdown) to their image data as
NumPy arrays. These are the cropped figure regions extracted from the page.

### `markdown`

A Markdown rendering of the full page content, with image references pointing
to entries in `figures`.

---

## Pipeline Data Flow

```
Image / PDF page
      │
      ▼
  np.ndarray  (H x W x 3, RGB)
      │
      ├──► ocr()      → OCROutput      (text segments + words)
      │
      └──► structv3() → StructureV3Output  (layout + figures + markdown)
```

Both pipeline functions use `joblib.Memory` for disk caching, so repeated
calls with the same input image are served from cache.
