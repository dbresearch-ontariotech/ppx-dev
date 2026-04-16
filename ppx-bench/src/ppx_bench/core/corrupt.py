import random
import string

from ppx_align.core.types import CharAlignmentTarget, ParsedDocument

REPLACEMENT_POOL = string.ascii_letters + string.digits + string.punctuation + " "


def spans_from_line_alignments(
    line_alignments: dict[str, CharAlignmentTarget],
    doc: ParsedDocument,
) -> list[tuple[int, int]]:
    """Resolve each line alignment to an absolute (start, end) character span in doc.markdown."""
    spans: list[tuple[int, int]] = []
    for target in line_alignments.values():
        abs_start = doc.ast_spans[target.ast_index_start][0] + target.char_start
        abs_end = doc.ast_spans[target.ast_index_end][0] + target.char_end
        spans.append((abs_start, abs_end))
    return spans


def corrupt_markdown(
    markdown: str,
    spans: list[tuple[int, int]],
    noise_level: float,
    seed: int | None = None,
) -> str:
    """Replace `noise_level` fraction of characters inside each span with a different random character.

    Operates per span so each aligned line receives ~noise_level corruption, which propagates
    proportionally to the block level (blocks = unions of line spans). Characters outside any
    span — structural markdown like '##', blank lines, HTML blocks — are left untouched.
    Overlapping spans do not double-corrupt the same character.
    """
    if not 0.0 <= noise_level <= 1.0:
        raise ValueError(f"noise_level must be in [0, 1], got {noise_level}")

    rng = random.Random(seed)
    chars = list(markdown)
    already_corrupted: set[int] = set()

    for abs_start, abs_end in spans:
        candidates = [i for i in range(abs_start, abs_end) if i not in already_corrupted]
        if not candidates:
            continue
        n_replace = int(round(len(candidates) * noise_level))
        if n_replace == 0:
            continue
        for pos in rng.sample(candidates, n_replace):
            original = chars[pos]
            new = rng.choice(REPLACEMENT_POOL)
            while new == original:
                new = rng.choice(REPLACEMENT_POOL)
            chars[pos] = new
            already_corrupted.add(pos)

    return "".join(chars)
