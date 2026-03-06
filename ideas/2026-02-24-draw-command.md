Create a typer app "draw" that draws layers of bounding boxes and text on top of the original PDF raster page images.

```python
ppx draw --page-dir <input_dir> -o <output_filename.png> --layer <layer_name> --color <color_name> --label <label_column> --query <query>
```

It should look something like this:

```
@app.command()
def draw(
    page_dir: Path = typer.Option(..., "--page-dir", help="Input directory containing files"),
    output: Path = typer.Option(..., "-o", "--output", help="Output file"),
    layer: str = typer.Option(..., "--layer", help="Layer name"),
    color: str = typer.Option("red", "--color", help="Color name"),
    label: str = typer.Option(..., "--label", help="Label column"),
    query: str | None = typer.Option(None, "--query", help="Query"),
):
    ...
```

Explanation of options:

"--page-dir": Input directory containing page image, and parquet files representing the layers.
"-o": Output file: The page image with the layer drawn on top.
"--layer": Layer name: The layer to draw.  The corresponding parquet file is "<page_dir>/<layer_name>.parquet".
"--label": Label column: The column to use for the label.  Must be a column in the parquet file.
"--query": Query: A query to filter the rows of the parquet file.  It is a pandas query string.