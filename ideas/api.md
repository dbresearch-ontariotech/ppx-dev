# REST API Design

Read-only API serving OCR results produced by `ppx ocr run`. The server
reads from an output directory containing the pre-computed parquet files and
images.

## Configuration

The server requires a **data directory** — the root output path passed to
`ppx ocr run -o`. This is set via:

- CLI option: `ppx server start --data ./output`
- Environment variable: `PPX_DATA_DIR`

The data directory has the structure:

```
{data_dir}/{document}/{page}/
    page.png
    ocr.json
    ocr_texts.parquet
    ocr_words.parquet
    structv3.json
    structv3_layout.parquet
    markdown_output/
        markdown.md
        imgs/      (extracted figures)
```

---

## Endpoints

### Documents

#### `GET /documents`

List all processed documents.

**Response** `200 OK`
```json
["paper", "report"]
```

#### `GET /documents/{document}/pages`

List page indices for a document.

**Response** `200 OK`
```json
[0, 1, 2, 3]
```

---

### Images

#### `GET /documents/{document}/pages/{page}/page.png`

The original page image.

**Response** `200 OK` — `image/png`

#### `GET /documents/{document}/pages/{page}/imgs/{name}`

An extracted figure image from `markdown_output/imgs/`. The browser
resolves the relative `imgs/foo.jpg` in the markdown source against
the parent of the `markdown` endpoint URL, yielding
`.../pages/{page}/imgs/foo.jpg`.

**Response** `200 OK` — `image/png` or `image/jpeg`

---

### DataFrames

All DataFrame endpoints return JSON and accept an optional `q` query
parameter. When provided, `q` is passed directly to `df.query(q)` to filter
rows before returning results.

#### `GET /documents/{document}/pages/{page}/ocr/texts`

Returns `ocr_texts.parquet` as JSON.

**Query params**

| Param  | Type   | Description |
|--------|--------|-------------|
| `q`    | string | Pandas query expression (e.g. `score > 0.9`) |

**Response** `200 OK`
```json
{
  "columns": ["text", "score", "x0", "y0", "x1", "y1"],
  "index": [0, 1, 2],
  "data": [
    ["Hello", 0.98, 10, 20, 200, 50],
    ["World", 0.95, 10, 60, 180, 90]
  ]
}
```

The response format is Pandas `split` orientation — compact and preserves
column names and index.

#### `GET /documents/{document}/pages/{page}/ocr/words`

Returns `ocr_words.parquet` as JSON.

**Query params** — same as above.

**Response** `200 OK` — same `split` format. Index is multi-level
`[seg_index, word_index]`.

#### `GET /documents/{document}/pages/{page}/structv3/layout`

Returns `structv3_layout.parquet` as JSON.

**Query params** — same as above.

#### `GET /documents/{document}/pages/{page}/markdown`

Returns the markdown text from `markdown_output/markdown.md`.

**Response** `200 OK`
```json
{
  "markdown": "# Title\n\nBody text..."
}
```

---

## Error Responses

All errors return JSON:

```json
{"detail": "Document not found: xyz"}
```

| Status | Meaning |
|--------|---------|
| `404`  | Document, page, or file not found. |
| `400`  | Invalid query expression (syntax error in `q`). |

---

## URL Summary

```
GET /health
GET /documents
GET /documents/{document}/pages
GET /documents/{document}/pages/{page}/page.png
GET /documents/{document}/pages/{page}/ocr/texts?q=...
GET /documents/{document}/pages/{page}/ocr/words?q=...
GET /documents/{document}/pages/{page}/structv3/layout?q=...
GET /documents/{document}/pages/{page}/markdown
GET /documents/{document}/pages/{page}/imgs/{name}
```
