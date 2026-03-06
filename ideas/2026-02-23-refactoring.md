We want to have a @types.py to have the following types:


# Raw raster documents

This models rastered images of a multi-page document.

```python
@dataclass
class RasterDocument:
    pages: list[np.ndarray]
```

All existing functions that load PDF files into numpy arrays should be convered to use this class.

# Visual overlays

We introduce the concept of layers.  Each layer is an overlay over rastered page image.

This is the base class.

```python
@dataclass
class PageLayer:
    np_page: np.ndarray
    page_index: int
    continue_nextpage: bool # indicate if the page continues to the next page.
```

We have several overlay types.  Each type of overlay extends the base `PageOverlay` base class with an additional pandas dataframe.  Each row of the dataframe is a visual element, described as a rectangular region.

## Visual tokens:

The visual tokens are rectangle regions associated with text and confidence scores.  We want to use `pandera` for type annotation and checking.

```python
import pandera.pandas as pa
from pandera.typing import DataFrame, Series

class TokenSchema(pa.DataFrameModel):
    index: Series[int]
    x0: Series[int]
    y0: Series[int]
    x1: Series[int]
    y1: Series[int]
    text: Series[str]
    score: Series[float]

@dataclass
class VisualTokenLayer(PageLayer):
    tokens: pa.DataFrame[TokenSchema]
```

## Layout analysis

Layout analysis produces regions of interest similar to visual tokens except that each region is annotated with some additional columns for region type and optional reading order.

```python
class LayoutSchema(pa.DataFrameModel):
        index: Series[int]
    x0: Series[int]
    y0: Series[int]
    x1: Series[int]
    y1: Series[int]
    text: Series[str]
    order: Series[int|None]

@dataclass
class LayoutLayer(PageLayer):
    regions: pa.DataFrame[LayoutSchema]
```

