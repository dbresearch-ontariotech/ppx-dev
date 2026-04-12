import IPython
from importlib import reload
import pandas as pd
from pathlib import Path
from rich.progress import Progress, BarColumn, TaskProgressColumn, TimeElapsedColumn, TextColumn
import ppx_align.core.storage as storage
import ppx_align.core.md as md
import ppx_align.core.layout as layout
import ppx_align.core.align as align


pages = sorted(Path("../output/paper").iterdir(), key=lambda d: int(d.name))

vls = []
ocrs = []
docs = []
trees = []

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
        vls.append(vl)
        ocrs.append(ocr)
        docs.append(doc)
        trees.append(tree)
        progress.advance(task)

IPython.embed()
