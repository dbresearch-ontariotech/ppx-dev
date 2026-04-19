from __future__ import annotations
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode

from ppx_align.core.tokenizers import PPXTokenizer, TreebankTokenizer
from ppx_align.core.types import BlockAlignmentTarget, CharAlignmentTarget, ParsedDocument, MarkdownDocument


def build_parsed_doc(doc: MarkdownDocument, tokenizer: PPXTokenizer | None = None) -> ParsedDocument:
    parser = MarkdownIt('gfm-like')
    tokens = parser.parse(doc.markdown)
    lines = doc.markdown.splitlines(keepends=True)

    spans = []
    start = 0
    for line in lines:
        spans.append((start, start + len(line)))
        start += len(line)

    ast_nodes = SyntaxTreeNode(tokens).children
    ast_spans = [
        (spans[node.map[0]][0], spans[node.map[1] - 1][1]) for node in ast_nodes  # type: ignore
    ]

    if tokenizer is None:
        tokenizer = TreebankTokenizer()
    ast_word_spans = []
    for ast_span in ast_spans:
        word_spans = tokenizer.tokenize(doc.markdown[ast_span[0]:ast_span[1]])
        # word span is in character offset relative to the start of the ast node
        ast_word_spans.append(word_spans)

    return ParsedDocument(
        markdown=doc.markdown,
        figures=doc.figures,
        ast_nodes=ast_nodes,
        lines=lines,
        ast_spans=ast_spans,
        ast_word_spans=ast_word_spans
    )

def get_content(
    doc: ParsedDocument,
    *,
    ast_range: tuple[int, int]|None = None,
    ast_index: int|None = None,
    block_alignment_target: BlockAlignmentTarget|None = None,
    char_alignment_target: CharAlignmentTarget|None = None,
) -> str:
    if ast_range is not None:
        start = doc.ast_spans[ast_range[0]][0]
        end = doc.ast_spans[ast_range[1] - 1][1]
        return doc.markdown[start:end]
    elif ast_index is not None:
        start, end = doc.ast_spans[ast_index]
        return doc.markdown[start:end]
    elif block_alignment_target is not None:
        start = doc.ast_spans[block_alignment_target.ast_start][0]
        end = doc.ast_spans[block_alignment_target.ast_end][1]  # ast_end inclusive
        return doc.markdown[start:end]
    elif char_alignment_target is not None:
        abs_start = doc.ast_spans[char_alignment_target.ast_index_start][0] + char_alignment_target.char_start
        abs_end = doc.ast_spans[char_alignment_target.ast_index_end][0] + char_alignment_target.char_end + 1  # char_end inclusive
        return doc.markdown[abs_start:abs_end]
    else:
        raise ValueError("Exactly one keyword argument must be provided")
