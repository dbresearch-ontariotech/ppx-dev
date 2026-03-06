from pathlib import Path
from ppx.core.helpers import get_page_tensors
from ppx.core.ocr import get_structv3_model, structv3

FIXTURES = Path(__file__).parent / "fixtures"


def test_structv3_first_three_pages():
    doc = get_page_tensors(FIXTURES / "paper.pdf")
    model = get_structv3_model()
    for page in doc.pages[0:5]:
        output = model.predict(page)
        try:
            output[0].save_all(save_path="./output")
        except ModuleNotFoundError:
            pass