import IPython
from importlib import reload
import pandas as pd
import ppx_align.core.storage as storage
import ppx_align.core.md as md
import ppx_align.core.layout as layout
import ppx_align.core.align as align

vl, ocr = storage.load("../output/paper/0")
doc = md.build_parsed_doc(ocr)

IPython.embed()
