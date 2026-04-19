import IPython
from importlib import reload
import pandas as pd
from pathlib import Path
from rich.progress import Progress, BarColumn, TaskProgressColumn, TimeElapsedColumn, TextColumn
import ppx_align.core.storage as storage
import ppx_align.core.md as md
import ppx_align.core.layout as layout
import ppx_align.core.align as align
from ppx_align.core.types import DocAlignment
import sys

output = sys.argv[1] if len(sys.argv) > 1 else "../output/resnet"

pages = sorted(Path(output).iterdir(), key=lambda d: int(d.name))

vls = []
ocrs = []
docs = []
trees = []
alignments = []

with Progress(
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TaskProgressColumn(),
    TimeElapsedColumn(),
) as progress:
    task = progress.add_task("Loading pages", total=len(pages))
    for page in pages:
        vl, ocr = storage.load(str(page))
        doc = md.build_parsed_doc(ocr)
        tree = layout.build_layout_tree(vl)
        with open(page / "alignment.json") as f:
            alignment = DocAlignment.model_validate_json(f.read())
        vls.append(vl)
        ocrs.append(ocr)
        docs.append(doc)
        trees.append(tree)
        alignments.append(alignment)
        progress.advance(task)

IPython.embed()
