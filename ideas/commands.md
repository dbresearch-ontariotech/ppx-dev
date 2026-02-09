# Performs OCR on a PDF file

`ppx ocr run -o <output_path> <pdf_file>`

- Performs ocr.ocr(...) and ocr.structv3(...) on all pages of the PDF file.

- Save all output artifacts in the directory: "{output_path}/{pdf_basename}/{page_index}/".

- The artifacts are:

  from OCROutput:
  - the page image as "ocr.png"
  - the texts dataframe as "ocr_texts.parquet"
  - the words dataframe as "ocr_words.parquet"

  from StructV3Output:
  - the page image as "structv3.png"
  - the layout dataframe as "structv3_layout.parquet"
  - the `figures:dict[str, np.ndarray]` as files named by the key, and the image as defined by the `np.ndarray` value.
  - the markdown as "structv3_markdown.md"

# Show annotated views

`ppx ocr annotate -o <output_file> --source ... --query ... <pdf_file> <page_number>`

- `output_file` is default to "<pdf_basename>_<page_number>.png"

- Draws rectangles on top of the "ocr.png" in the pdf page ocr output folder.

- the rectangles are given by the rows selected from the dataframe of the source.  The source is the basename of the parquet file.  All parquert files contain "x0", "x1", "y0", "y1" columns which are the rectangle corners.

- By default we use all rows in the dataframe.  But if `--query <query>` is present, then use the query to run `df.query(query)` to select the rows.