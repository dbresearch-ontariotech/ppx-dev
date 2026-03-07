# Align layout tree:

Given a dataframe of layout tree, and a list of text tokens, we want to align the layout tree nodes to intervals of text tokens.

The similarity function will be given as:

`sim(node: VisualTokenNode, interval: tuple[int, int]) -> float`

## Already have:

- `dp_align_nodes(X: list, Y: list, sim, a:int, b:int) -> list[tuple[int, int]]`.

This function aligns a list of nodes $X$ to a list of tokens $Y[a:b]$.

## Objective:

Want a function:

- `align_tree(df: DataFrame, root_id: str, text_tokens: list[str], sim) -> list[tuple[int, int]]`

## Solution:

General approach:

- the root is by definition aligned to the entire text_tokens list.
- recursively align the children of a node to the interval of the node using `dp_align_nodes`.