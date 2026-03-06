# Layout tree

## Context

Layout analysis results are stored in different parquet files.
  ---
  regions.parquet

  High-level page regions detected by layout analysis.

  ┌─────────────┬─────────┬──────────────────────┐
  │   Column    │  Type   │     Description      │
  ├─────────────┼─────────┼──────────────────────┤
  │ index       │ str     │ e.g. region_0        │
  ├─────────────┼─────────┼──────────────────────┤
  │ x0/y0/x1/y1 │ int64   │ Bounding box         │
  ├─────────────┼─────────┼──────────────────────┤
  │ label       │ str     │ e.g. "Region"        │
  ├─────────────┼─────────┼──────────────────────┤
  │ score       │ float64 │ Detection confidence │
  └─────────────┴─────────┴──────────────────────┘

  ---
  blocks.parquet

  Text blocks with extracted content and reading order.

  ┌─────────────┬─────────┬────────────────────────────┐
  │   Column    │  Type   │        Description         │
  ├─────────────┼─────────┼────────────────────────────┤
  │ index       │ str     │ e.g. block_0               │
  ├─────────────┼─────────┼────────────────────────────┤
  │ x0/y0/x1/y1 │ int64   │ Bounding box               │
  ├─────────────┼─────────┼────────────────────────────┤
  │ label       │ str     │ e.g. "aside_text"          │
  ├─────────────┼─────────┼────────────────────────────┤
  │ order       │ float64 │ Reading order (may be NaN) │
  ├─────────────┼─────────┼────────────────────────────┤
  │ content     │ str     │ Full text content of block │
  ├─────────────┼─────────┼────────────────────────────┤
  │ block_index │ int64   │ Numeric index              │
  └─────────────┴─────────┴────────────────────────────┘

  ---
  line_tokens.parquet

  OCR-recognized text lines.

  ┌─────────────┬─────────┬──────────────────────┐
  │   Column    │  Type   │     Description      │
  ├─────────────┼─────────┼──────────────────────┤
  │ index       │ int64   │ Row index            │
  ├─────────────┼─────────┼──────────────────────┤
  │ x0/y0/x1/y1 │ int16   │ Bounding box         │
  ├─────────────┼─────────┼──────────────────────┤
  │ text        │ str     │ Recognized line text │
  ├─────────────┼─────────┼──────────────────────┤
  │ score       │ float64 │ OCR confidence       │
  └─────────────┴─────────┴──────────────────────┘

  ---
  word_tokens.parquet

  Individual word tokens linked to lines.

  ┌─────────────┬───────┬─────────────────────────────────┐
  │   Column    │ Type  │           Description           │
  ├─────────────┼───────┼─────────────────────────────────┤
  │ index       │ int64 │ Row index                       │
  ├─────────────┼───────┼─────────────────────────────────┤
  │ x0/y0/x1/y1 │ int64 │ Bounding box                    │
  ├─────────────┼───────┼─────────────────────────────────┤
  │ text        │ str   │ Word text                       │
  ├─────────────┼───────┼─────────────────────────────────┤
  │ line_index  │ int64 │ Foreign key → line_tokens.index │
  └─────────────┴───────┴─────────────────────────────────┘


We want to build a tree structure with the root being the entire page.
The next levels are regions, then blocks, then line_tokens, then word_tokens.
Formulas are linked to regions.

The hierarchy is to be stored as a pandas dataframe with columns:

```
node_id: str
level_index: number
level_name: str
parent_id: str|None
x0/y0/x1/y1: bounding box
label: str (used by region and blocks)
content: str (used by block, line and word)
```

For region nodes, the parent_id is `None`.
The `content` string is `text` for line and word nodes, and `content` for block nodes.

## Parent Child Relationship

The parent child relationship is defined as bounding box containment.  The containment is defined as a soft containment, i.e. the child bounding box must be contained in the parent bounding box with a certain tolerance.  The tolerance is defined as a fraction of the child bounding box area inside the parent bounding box. The default tolerance is 0.8.

## Sibling ordering

- Region siblings are ordered by their sizes.
- Block siblings are ordered by the `order`.  If the `order` is `NaN`, they will go to the end of the list of siblings in no particular order.  
- Line siblings are ordered by their `y0` coordinate.
- Word siblings are ordered by their original order in the line.