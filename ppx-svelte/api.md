# PPX API Reference

Base URL: `http://localhost:8000` (proxied via SvelteKit at `/api/ppx/...`)

---

## `GET /api/ppx`

List all document names available in the output directory.

**Response** `200 OK` — JSON array of strings
```json
["paper", "report", "thesis"]
```

---

## `GET /api/ppx/{filename}/`

Get the page count for a document.

**Path parameters**
| Parameter  | Type   | Description   |
|------------|--------|---------------|
| `filename` | string | Document name |

**Response** `200 OK`
```json
{
  "filename": "paper",
  "pages": 12
}
```

**Errors**
- `404` — document not found

---

## `GET /api/ppx/{filename}/{page_index}/image`

Return the full-resolution page image as PNG.

**Path parameters**
| Parameter    | Type    | Description            |
|--------------|---------|------------------------|
| `filename`   | string  | Document name          |
| `page_index` | integer | Zero-based page number |

**Response** `200 OK` — `image/png`

**Errors**
- `404` — image not found

---

## `GET /api/ppx/{filename}/{page_index}/thumbnail`

Return a thumbnail of the page image (fits within 256×256) as PNG.

**Path parameters**
| Parameter    | Type    | Description            |
|--------------|---------|------------------------|
| `filename`   | string  | Document name          |
| `page_index` | integer | Zero-based page number |

**Response** `200 OK` — `image/png`

**Errors**
- `404` — image not found

---

## `GET /api/ppx/{filename}/{page_index}/markdown/index.md`

Return the raw markdown text for a page as plain text.

**Path parameters**
| Parameter    | Type    | Description            |
|--------------|---------|------------------------|
| `filename`   | string  | Document name          |
| `page_index` | integer | Zero-based page number |

**Response** `200 OK` — `text/plain`

**Errors**
- `404` — markdown file not found

---

## `GET /api/ppx/{filename}/{page_index}/markdown/ast`

Return the markdown parsed as an array of AST nodes. Each node corresponds to a top-level block in the markdown AST (paragraph, heading, code fence, etc.).

**Path parameters**
| Parameter    | Type    | Description            |
|--------------|---------|------------------------|
| `filename`   | string  | Document name          |
| `page_index` | integer | Zero-based page number |

**Response** `200 OK`
```json
{
  "ast_nodes": [
    {
      "ast_index": 0,
      "type": "paragraph",
      "markdown": "This is the first paragraph."
    },
    {
      "ast_index": 1,
      "type": "heading",
      "markdown": "## Introduction"
    }
  ]
}
```

**Fields**
| Field       | Type    | Description                                                        |
|-------------|---------|--------------------------------------------------------------------|
| `ast_index` | integer | Stable zero-based index identifying this node within the page      |
| `type`      | string  | markdown-it block type (`paragraph`, `heading`, `fence`, etc.)     |
| `markdown`  | string  | Raw markdown text for this node, sliced from the source            |

**Errors**
- `404` — page not found

---

## `GET /api/ppx/{filename}/{page_index}/markdown/{path}`

Return a binary resource (image, audio, etc.) referenced by the page markdown.

**Path parameters**
| Parameter    | Type    | Description                                                  |
|--------------|---------|--------------------------------------------------------------|
| `filename`   | string  | Document name                                                |
| `page_index` | integer | Zero-based page number                                       |
| `path`       | string  | Relative path to the resource within the markdown directory  |

**Response** `200 OK` — file content with inferred media type

**Errors**
- `404` — resource not found

---

## `GET /api/ppx/{filename}/{page_index}/layout`

Return the visual layout tree for a page. Each entry represents a node in the layout hierarchy (region → block → line → word).

**Path parameters**
| Parameter    | Type    | Description            |
|--------------|---------|------------------------|
| `filename`   | string  | Document name          |
| `page_index` | integer | Zero-based page number |

**Response** `200 OK`
```json
{
  "visual_tokens": [
    {
      "node_id": "0",
      "level_index": 0,
      "level_name": "region",
      "parent_id": null,
      "x0": 10, "y0": 20, "x1": 500, "y1": 300,
      "label": "text",
      "content": ""
    }
  ]
}
```

**Fields** — each entry follows `LayoutTreeSchema`
| Field        | Type    | Description                                      |
|--------------|---------|--------------------------------------------------|
| `node_id`    | string  | Unique node identifier                           |
| `level_index`| integer | Depth: 0=region, 1=block, 2=line, 3=word         |
| `level_name` | string  | `"region"`, `"block"`, `"line"`, or `"word"`     |
| `parent_id`  | string\|null | Parent node id, null for root nodes         |
| `x0,y0,x1,y1`| integer | Bounding box in pixel coordinates               |
| `label`      | string  | Layout label (e.g. `"text"`, `"table"`)          |
| `content`    | string  | OCR text content (populated for block and below) |

**Errors**
- `404` — page not found

---

## `GET /api/ppx/{filename}/{page_index}/alignment`

Return the pre-computed alignment between visual layout tokens and markdown AST nodes.

**Path parameters**
| Parameter    | Type    | Description            |
|--------------|---------|------------------------|
| `filename`   | string  | Document name          |
| `page_index` | integer | Zero-based page number |

**Response** `200 OK`
```json
{
  "block_alignments": {
    "<node_id>": {
      "ast_start": 2,
      "ast_end": 5,
      "score": 0.87
    }
  },
  "line_alignments": {
    "<node_id>": {
      "ast_index_start": 2,
      "char_start": 14,
      "ast_index_end": 2,
      "char_end": 61,
      "score": 0.91
    }
  }
}
```

**Fields — `block_alignments`**
| Field       | Type    | Description                                                  |
|-------------|---------|--------------------------------------------------------------|
| `ast_start` | integer | Index of the first matched AST node (inclusive)              |
| `ast_end`   | integer | Index of the last matched AST node (inclusive)               |
| `score`     | float   | Cosine similarity score                                      |

**Fields — `line_alignments`**
| Field             | Type    | Description                                                      |
|-------------------|---------|------------------------------------------------------------------|
| `ast_index_start` | integer | AST node index where the matched char span starts                |
| `char_start`      | integer | Char offset within `ast_index_start` node (relative to node)    |
| `ast_index_end`   | integer | AST node index where the matched char span ends                  |
| `char_end`        | integer | Char offset within `ast_index_end` node (relative to node, inclusive) |
| `score`           | float   | Cosine similarity score                                          |

**Errors**
- `404` — alignment file not found
