# API endpoints

## list the files

GET /api/ppx

- returns the list of filenames in JSON.

## list the pages

GET /api/ppx/<filename>/
- returns the number of pages in JSON

## page image

GET /api/ppx/<filename>/<page_index>/image
GET /api/ppx/<filename>/<page_index>/thumbnail
- returns image as png that is loaded from output path: <filename>/<page_index>/np_page.png

## page markdown

GET /api/ppx/<filename>/<page_index>/markdown/index.md
- returns the markdown text as plain text that is located in the output path: <filename>/<page_index>/markdown/markdown.md

GET /api/ppx/<filename>/<page_index>/markdown/ast
- returns the markdown as a `MarkdownASTNode` array in JSON:
  ```json
  {
    ast_nodes: [ ... ]
  }
  ```
  Entries in `ast_nodes` should be instances of `MarkdownASTNode`.

GET /api/ppx/<filename>/<page_index>/markdown/<path>
- returns the binary resources (image, audio etc) located in the output path: <filename>/<page_index>/markdown/<path>


## Layout

GET /api/ppx/<filename>/<page_index>/layout
- returns the layout_tree obtained from `layout.build_layout_tree` in JSON in the form of:
   ```json
   {
    "visual_tokens": [
        {...}
    ]
   }
   ```
   Each entry in "visual_tokens" is an object with `LayoutTreeSchema`.

## Alignment

GET /api/ppx/<filename>/<page_index>/alignment
- returns the alignment result in JSON that is already stored in the output path: <filename>/<page_index>/alignment.json