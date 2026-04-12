# PPX API Reference

Base URL: `http://localhost:8000`

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
| Parameter  | Type   | Description        |
|------------|--------|--------------------|
| `filename` | string | Document name      |

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
| Parameter    | Type    | Description              |
|--------------|---------|--------------------------|
| `filename`   | string  | Document name            |
| `page_index` | integer | Zero-based page number   |

**Response** `200 OK` — `image/png`

**Errors**
- `404` — image not found

---

## `GET /api/ppx/{filename}/{page_index}/thumbnail`

Return a thumbnail of the page image (fits within 256×256) as PNG.

**Path parameters**
| Parameter    | Type    | Description              |
|--------------|---------|--------------------------|
| `filename`   | string  | Document name            |
| `page_index` | integer | Zero-based page number   |

**Response** `200 OK` — `image/png`

**Errors**
- `404` — image not found

---

## `GET /api/ppx/{filename}/{page_index}/markdown/index.md`

Return the markdown text for a page as plain text.

**Path parameters**
| Parameter    | Type    | Description              |
|--------------|---------|--------------------------|
| `filename`   | string  | Document name            |
| `page_index` | integer | Zero-based page number   |

**Response** `200 OK` — `text/plain`

**Errors**
- `404` — markdown file not found

---

## `GET /api/ppx/{filename}/{page_index}/markdown/{path}`

Return a binary resource (image, audio, etc.) referenced by the markdown of a page.

**Path parameters**
| Parameter    | Type    | Description                                          |
|--------------|---------|------------------------------------------------------|
| `filename`   | string  | Document name                                        |
| `page_index` | integer | Zero-based page number                               |
| `path`       | string  | Relative path to the resource within the markdown directory |

**Response** `200 OK` — file content with inferred media type

**Errors**
- `404` — resource not found
