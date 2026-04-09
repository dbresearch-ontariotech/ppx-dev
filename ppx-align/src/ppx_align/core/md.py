from __future__ import annotations
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
import nltk
from nltk.tokenize import TreebankWordTokenizer

nltk.download("punkt")
nltk.download("punkt_tab")

from ppx_align.core.types import ParsedDocument, MarkdownDocument

def build_parsed_doc(doc: MarkdownDocument) -> ParsedDocument:
    parser = MarkdownIt('gfm-like')
    tokens = parser.parse(doc.markdown)
    lines = doc.markdown.splitlines(keepends=True)

    spans = []
    start = 0
    for line in lines:
        spans.append((start, start + len(line)))
        start += len(line)

    segments = SyntaxTreeNode(tokens).children
    seg_spans = [
        (spans[seg.map[0]][0], spans[seg.map[1] - 1][1]) for seg in segments  # type: ignore
    ]

    tokenizer = TreebankWordTokenizer()
    word_spans = []
    for seg_span in seg_spans:
        spans = list(tokenizer.span_tokenize(doc.markdown[seg_span[0]:seg_span[1]]))
        word_spans.append([(a+seg_span[0], b+seg_span[0]) for (a, b) in spans])
        
    return ParsedDocument(
        markdown=doc.markdown, 
        figures=doc.figures, 
        segments=segments, 
        lines=lines, 
        seg_spans=seg_spans, 
        word_spans=word_spans
    )
