# ppx-dev

Document analysis pipeline: OCR a PDF, build semantic alignments between the visual layout and the markdown AST, and explore the results in an interactive viewer.

```
ppx-ocr   →   ppx-align build   →   ppx-align serve
                                           ↑
                                      ppx-svelte (browser)
```

---

## Prerequisites

- Python ≥ 3.10 with [uv](https://docs.astral.sh/uv/)
- Node.js ≥ 18 with [pnpm](https://pnpm.io/) (for the Svelte client)
- CUDA-capable GPU (required by PaddleOCR)

---

## Step 1 — OCR a PDF (`ppx-ocr`)

Install dependencies (first time only):

```bash
cd ppx-ocr
make install
```

Run OCR on a PDF file:

```bash
uv run ppx-ocr -o ../output/ path/to/mydoc.pdf
```

This produces one subdirectory per page under `../output/mydoc/`:

```
output/mydoc/
  0/    ← page 0
  1/    ← page 1
  ...
```

Each page directory contains the page image, extracted markdown, and raw OCR data.

Options:

| Flag | Description |
|------|-------------|
| `-o PATH` | Output directory (required) |
| `--overwrite` | Re-process pages that already have output |

---

## Step 2 — Build alignments (`ppx-align`)

Install dependencies (first time only):

```bash
cd ppx-align
make install
```

Build the layout tree and semantic alignment for all pages:

```bash
uv run ppx-align build ../output/mydoc
```

To process a single page (useful during development):

```bash
uv run ppx-align build ../output/mydoc --page 0
```

To skip line-level alignment and only align blocks:

```bash
uv run ppx-align build ../output/mydoc --blocks-only
```

---

## Step 3 — Start the API server (`ppx-align serve`)

The server exposes the OCR and alignment data over HTTP and is required by the Svelte client.

```bash
uv run ppx-align serve ../output
```

The server starts on port 8000 by default. To use a different port:

```bash
uv run ppx-align serve ../output --port 9000
```

The `output` directory should be the **parent** of the per-document directories — the server discovers all documents inside it automatically.

To simulate a slow connection (useful for testing loading states in the UI):

```bash
uv run ppx-align serve ../output --slow
```

---

## Step 4 — Start the viewer (`ppx-svelte`)

In a separate terminal:

```bash
cd ppx-svelte
pnpm install        # first time only
pnpm dev
```

Open [http://localhost:5173](http://localhost:5173) in a browser.

The client proxies all `/api/ppx/...` requests to the server on port 8000. If the server is running on a different port, update `vite.config.ts` accordingly.

---

## Viewer features

- **Two-panel layout**: page image on the left, markdown on the right
- **Visual token overlays**: enable Block / Line / Word bounding boxes with the checkboxes in the header
- **Hover alignment**: hovering a layout token highlights the corresponding markdown span; the right panel scrolls to it automatically
- **Raw source mode**: toggle **Raw** in the header to view the original markdown source instead of rendered HTML — enables text selection for reverse alignment
- **Selection tracking**: selecting text in raw source mode displays the `ast_index:char_offset` span in the header
