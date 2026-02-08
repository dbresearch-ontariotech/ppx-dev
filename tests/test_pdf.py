from pathlib import Path
import numpy as np
from ppx.core.helpers import get_page_tensors

FIXTURES = Path(__file__).parent / "fixtures"

def test_get_page_tensors_page_count():
    pages = list(get_page_tensors(FIXTURES / "paper.pdf"))
    assert len(pages) == 12
    for page in pages:
        assert type(page) == np.ndarray
        assert page.ndim == 3
        assert page.shape[-1] == 3
