# Performs OCR on a PDF file

`ppx ocr run -o <output_path> <pdf_file>`

- Performs ocr.ocr(...) and ocr.structv3(...) on all pages of the PDF file.

- Save all output artifacts in the directory: "{output_path}/{pdf_basename}/{page_index}/".

- The artifacts are:

  - the page image as "page.png"

  from OCROutput:
  - the texts dataframe as "ocr_texts.parquet"
  - the words dataframe as "ocr_words.parquet"

  from StructV3Output:
  - the layout dataframe as "structv3_layout.parquet"
  - the markdown and figures in "markdown_output/":
    - "markdown_output/markdown.md"
    - "markdown_output/imgs/..." (extracted figure images)

# Show annotated views

`ppx ocr annotate -o <output_file> --source ... --query ... <page_data_folder>`

- `output_file` is default to "<pdf_basename>_<page_number>.png"

- Draws rectangles on top of the "page.png" in the pdf page ocr output folder.

- the rectangles are given by the rows selected from the dataframe of the source.  The source is the basename of the parquet file.  All parquert files contain "x0", "x1", "y0", "y1" columns which are the rectangle corners.

- By default we use all rows in the dataframe.  But if `--query <query>` is present, then use the query to run `df.query(query)` to select the rows.