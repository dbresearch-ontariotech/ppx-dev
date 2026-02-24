from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from ppx.core.storage import store, load, WriteStatus
from ppx.core.types import VisualTokenLayer, LayoutLayers, MarkdownDocument

FIGURES = {
    "fig_0.png": np.random.randint(0, 256, (32, 32, 3), dtype=np.uint8),
    "imgs/fig_1.jpg": np.random.randint(0, 256, (16, 48, 3), dtype=np.uint8),
}
MARKDOWN_TEXT = "# Page\n\n![fig 0](fig_0.png)\n\n![fig 1](imgs/fig_1.jpg)\n"

# Total yields per store call: 6 base + 1 markdown.md + len(FIGURES) figure pngs
EXPECTED_STORE_COUNT = 6 + 1 + len(FIGURES)


def make_fixtures(page_index: int = 0):
    np_page = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)

    line_tokens = pd.DataFrame({
        "x0": [10], "y0": [20], "x1": [100], "y1": [40],
        "text": ["hello"], "score": [0.99],
    })
    word_tokens = pd.DataFrame({
        "x0": [10], "y0": [20], "x1": [50], "y1": [40],
        "text": ["hello"], "line_index": [0],
    })
    layout = pd.DataFrame({
        "x0": [0], "y0": [0], "x1": [64], "y1": [64],
        "label": ["text"], "score": [0.95],
    })
    blocks = pd.DataFrame({
        "x0": [0], "y0": [0], "x1": [64], "y1": [64],
        "label": ["paragraph"], "order": pd.array([1], dtype=pd.Int64Dtype()),
        "content": ["hello"], "block_index": [0],
    })
    formulas = pd.DataFrame({
        "x0": [5], "y0": [5], "x1": [30], "y1": [20],
        "text": ["E=mc^2"], "formula_region_id": [0],
    })

    vtl = VisualTokenLayer(
        np_page=np_page, page_index=page_index,
        line_tokens=line_tokens, word_tokens=word_tokens,
    )
    ll = LayoutLayers(
        np_page=np_page, page_index=page_index,
        layout=layout, blocks=blocks, formulas=formulas,
    )
    md = MarkdownDocument(markdown=MARKDOWN_TEXT, figures=dict(FIGURES))
    return vtl, ll, md


# --- store tests ---

def test_store_yields_correct_count(tmp_path):
    vtl, ll, md = make_fixtures()
    statuses = list(store(tmp_path, vtl, ll, md))
    assert len(statuses) == EXPECTED_STORE_COUNT


def test_store_status_types(tmp_path):
    vtl, ll, md = make_fixtures()
    for s in store(tmp_path, vtl, ll, md):
        assert isinstance(s, WriteStatus)
        assert s.path.exists()
        assert s.size > 0
        assert isinstance(s.message, str)


def test_store_creates_correct_files(tmp_path):
    vtl, ll, md = make_fixtures(page_index=3)
    list(store(tmp_path, vtl, ll, md))

    page_dir = tmp_path / "3"
    expected = [
        "np_page.png",
        "line_tokens.parquet",
        "word_tokens.parquet",
        "layout.parquet",
        "blocks.parquet",
        "formulas.parquet",
        "markdown/markdown.md",
        "markdown/fig_0.png",
        "markdown/imgs/fig_1.jpg",
    ]
    for name in expected:
        assert (page_dir / name).exists(), f"missing {name}"


def test_store_status_order(tmp_path):
    vtl, ll, md = make_fixtures()
    messages = [s.message for s in store(tmp_path, vtl, ll, md)]
    assert messages[:6] == [
        "np_page.png",
        "line_tokens.parquet",
        "word_tokens.parquet",
        "layout.parquet",
        "blocks.parquet",
        "formulas.parquet",
    ]
    assert "markdown/markdown.md" in messages
    for fname in FIGURES:
        assert f"markdown/{fname}" in messages


def test_store_markdown_message_prefix(tmp_path):
    vtl, ll, md = make_fixtures()
    messages = [s.message for s in store(tmp_path, vtl, ll, md)]
    md_messages = [m for m in messages if m.startswith("markdown/")]
    assert "markdown/markdown.md" in md_messages
    assert len(md_messages) == 1 + len(FIGURES)


def test_store_raises_on_existing_dir(tmp_path):
    vtl, ll, md = make_fixtures()
    list(store(tmp_path, vtl, ll, md))
    with pytest.raises(FileExistsError):
        list(store(tmp_path, vtl, ll, md))


def test_store_overwrite_succeeds(tmp_path):
    vtl, ll, md = make_fixtures()
    list(store(tmp_path, vtl, ll, md))
    statuses = list(store(tmp_path, vtl, ll, md, overwrite=True))
    assert len(statuses) == EXPECTED_STORE_COUNT


def test_store_raises_on_page_index_mismatch(tmp_path):
    vtl, ll, md = make_fixtures()
    ll.page_index = 99
    with pytest.raises(ValueError, match="page_index mismatch"):
        list(store(tmp_path, vtl, ll, md))


def test_store_uses_page_index_as_subdir(tmp_path):
    vtl, ll, md = make_fixtures(page_index=7)
    list(store(tmp_path, vtl, ll, md))
    assert (tmp_path / "7").is_dir()


def test_store_figure_subdir_created(tmp_path):
    vtl, ll, _ = make_fixtures()
    md = MarkdownDocument(
        markdown="![x](sub/fig.png)",
        figures={"sub/fig.png": np.zeros((8, 8, 3), dtype=np.uint8)},
    )
    list(store(tmp_path, vtl, ll, md))
    assert (tmp_path / "0" / "markdown" / "sub" / "fig.png").exists()


def test_store_jpeg_format(tmp_path):
    vtl, ll, _ = make_fixtures()
    arr = np.full((16, 16, 3), 128, dtype=np.uint8)
    md = MarkdownDocument(
        markdown="![x](fig.jpg)",
        figures={"fig.jpg": arr},
    )
    list(store(tmp_path, vtl, ll, md))
    dest = tmp_path / "0" / "markdown" / "fig.jpg"
    assert dest.exists()
    # Verify it is actually a JPEG (starts with FFD8 magic bytes)
    assert dest.read_bytes()[:2] == b"\xff\xd8"


def test_store_no_figures(tmp_path):
    vtl, ll, _ = make_fixtures()
    md_empty = MarkdownDocument(markdown="# empty", figures={})
    statuses = list(store(tmp_path, vtl, ll, md_empty))
    # 6 base + 1 markdown.md, no figure files
    assert len(statuses) == 7
    assert (tmp_path / "0" / "markdown" / "markdown.md").exists()


# --- load tests ---

def test_load_returns_correct_types(tmp_path):
    vtl, ll, md = make_fixtures()
    list(store(tmp_path, vtl, ll, md))
    vtl2, ll2, md2 = load(tmp_path / "0")
    assert isinstance(vtl2, VisualTokenLayer)
    assert isinstance(ll2, LayoutLayers)
    assert isinstance(md2, MarkdownDocument)


def test_load_page_index(tmp_path):
    vtl, ll, md = make_fixtures(page_index=5)
    list(store(tmp_path, vtl, ll, md))
    vtl2, ll2, md2 = load(tmp_path / "5")
    assert vtl2.page_index == 5
    assert ll2.page_index == 5


def test_load_np_page_shape(tmp_path):
    vtl, ll, md = make_fixtures()
    list(store(tmp_path, vtl, ll, md))
    vtl2, ll2, _ = load(tmp_path / "0")
    assert vtl2.np_page.shape == vtl.np_page.shape
    assert ll2.np_page.shape == vtl.np_page.shape


def test_load_np_page_values(tmp_path):
    vtl, ll, md = make_fixtures()
    list(store(tmp_path, vtl, ll, md))
    vtl2, _, _ = load(tmp_path / "0")
    np.testing.assert_array_equal(vtl2.np_page, vtl.np_page)


def test_load_dataframe_shapes(tmp_path):
    vtl, ll, md = make_fixtures()
    list(store(tmp_path, vtl, ll, md))
    vtl2, ll2, _ = load(tmp_path / "0")
    assert vtl2.line_tokens.shape == vtl.line_tokens.shape
    assert vtl2.word_tokens.shape == vtl.word_tokens.shape
    assert ll2.layout.shape == ll.layout.shape
    assert ll2.blocks.shape == ll.blocks.shape
    assert ll2.formulas.shape == ll.formulas.shape


def test_load_dataframe_values(tmp_path):
    vtl, ll, md = make_fixtures()
    list(store(tmp_path, vtl, ll, md))
    vtl2, ll2, _ = load(tmp_path / "0")

    # fastparquet may normalise string columns to object dtype; check values only
    pd.testing.assert_frame_equal(vtl2.line_tokens.reset_index(drop=True),
                                   vtl.line_tokens.reset_index(drop=True), check_dtype=False)
    pd.testing.assert_frame_equal(vtl2.word_tokens.reset_index(drop=True),
                                   vtl.word_tokens.reset_index(drop=True), check_dtype=False)
    pd.testing.assert_frame_equal(ll2.layout.reset_index(drop=True),
                                   ll.layout.reset_index(drop=True), check_dtype=False)
    pd.testing.assert_frame_equal(ll2.blocks.reset_index(drop=True),
                                   ll.blocks.reset_index(drop=True), check_dtype=False)
    pd.testing.assert_frame_equal(ll2.formulas.reset_index(drop=True),
                                   ll.formulas.reset_index(drop=True), check_dtype=False)


def test_load_markdown_text(tmp_path):
    vtl, ll, md = make_fixtures()
    list(store(tmp_path, vtl, ll, md))
    _, _, md2 = load(tmp_path / "0")
    assert md2.markdown == MARKDOWN_TEXT


def test_load_figures_keys(tmp_path):
    vtl, ll, md = make_fixtures()
    list(store(tmp_path, vtl, ll, md))
    _, _, md2 = load(tmp_path / "0")
    assert set(md2.figures.keys()) == set(FIGURES.keys())


def test_load_figures_values(tmp_path):
    vtl, ll, md = make_fixtures()
    list(store(tmp_path, vtl, ll, md))
    _, _, md2 = load(tmp_path / "0")
    for fname, arr in FIGURES.items():
        if Path(fname).suffix.lower() in (".jpg", ".jpeg"):
            # JPEG is lossy; only shape is checked here — exact values tested by test_load_jpeg_roundtrip
            assert md2.figures[fname].shape == arr.shape
        else:
            np.testing.assert_array_equal(md2.figures[fname], arr)


def test_load_figures_shapes(tmp_path):
    vtl, ll, md = make_fixtures()
    list(store(tmp_path, vtl, ll, md))
    _, _, md2 = load(tmp_path / "0")
    for fname, arr in FIGURES.items():
        assert md2.figures[fname].shape == arr.shape


def test_load_figures_subdir_key(tmp_path):
    vtl, ll, _ = make_fixtures()
    arr = np.zeros((8, 8, 3), dtype=np.uint8)
    md = MarkdownDocument(markdown="![x](sub/fig.png)", figures={"sub/fig.png": arr})
    list(store(tmp_path, vtl, ll, md))
    _, _, md2 = load(tmp_path / "0")
    assert "sub/fig.png" in md2.figures
    np.testing.assert_array_equal(md2.figures["sub/fig.png"], arr)


def test_load_jpeg_roundtrip(tmp_path):
    vtl, ll, _ = make_fixtures()
    # Use a uniform colour so lossy JPEG compression is lossless in practice
    arr = np.full((16, 16, 3), 128, dtype=np.uint8)
    md = MarkdownDocument(markdown="![x](fig.jpg)", figures={"fig.jpg": arr})
    list(store(tmp_path, vtl, ll, md))
    _, _, md2 = load(tmp_path / "0")
    assert "fig.jpg" in md2.figures
    np.testing.assert_array_equal(md2.figures["fig.jpg"], arr)


def test_load_no_figures(tmp_path):
    vtl, ll, _ = make_fixtures()
    md_empty = MarkdownDocument(markdown="# empty", figures={})
    list(store(tmp_path, vtl, ll, md_empty))
    _, _, md2 = load(tmp_path / "0")
    assert md2.markdown == "# empty"
    assert md2.figures == {}


def test_roundtrip_multiple_pages(tmp_path):
    for i in range(3):
        vtl, ll, md = make_fixtures(page_index=i)
        list(store(tmp_path, vtl, ll, md))

    for i in range(3):
        vtl2, ll2, md2 = load(tmp_path / str(i))
        assert vtl2.page_index == i
        assert ll2.page_index == i
        assert md2.markdown == MARKDOWN_TEXT
