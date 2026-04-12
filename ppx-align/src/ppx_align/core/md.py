from __future__ import annotations
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
import nltk
from nltk.tokenize import TreebankWordTokenizer

nltk.download("punkt")
nltk.download("punkt_tab")

from ppx_align.core.types import BlockAlignmentTarget, CharAlignmentTarget, ParsedDocument, MarkdownDocument

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
        # word span is in character offset related to the start of the ast node
        word_spans.append([(a, b) for (a, b) in spans])
        
    return ParsedDocument(
        markdown=doc.markdown, 
        figures=doc.figures, 
        segments=segments, 
        lines=lines, 
        seg_spans=seg_spans, 
        word_spans=word_spans
    )

def get_content(
    doc: ParsedDocument,
    *,
    segment_range: tuple[int, int]|None = None, # segment index
    segment_index: int|None = None, # segment index
    block_alignment_target: BlockAlignmentTarget|None = None,
    char_alignment_target: CharAlignmentTarget|None = None,
) -> str:
    if segment_range is not None:
        start = doc.seg_spans[segment_range[0]][0]
        end = doc.seg_spans[segment_range[1] - 1][1]
        return doc.markdown[start:end]
    elif segment_index is not None:
        start, end = doc.seg_spans[segment_index]
        return doc.markdown[start:end]
    elif block_alignment_target is not None:
        start = doc.seg_spans[block_alignment_target.ast_start][0]
        end = doc.seg_spans[block_alignment_target.ast_end - 1][1]
        return doc.markdown[start:end]
    elif char_alignment_target is not None:
        abs_start = doc.seg_spans[char_alignment_target.segment_index_start][0] + char_alignment_target.char_start
        abs_end = doc.seg_spans[char_alignment_target.segment_index_end][0] + char_alignment_target.char_end
        return doc.markdown[abs_start:abs_end]
    else:
        raise ValueError("Exactly one keyword argument must be provided")