from pathlib import Path
import typer
import pandas as pd
import numpy as np
from PIL import Image

app = typer.Typer(help="Draw annotation layers on page images")


@app.command(name="boxes")
def DrawBoxes(
    page_dir: Path = typer.Option(..., "--page-dir", help="Input directory containing page image and parquet files"),
    output: Path = typer.Option(..., "-o", "--output", help="Output file"),
    layer: str = typer.Option(..., "--layer", help="Layer name (parquet file without extension)"),
    label: str | None = typer.Option(None, "--label", help="Label column in the parquet file"),
    color: str = typer.Option("red", "--color", help="Color name"),
    query: str | None = typer.Option(None, "--query", help="Pandas query string to filter rows"),
    input: Path | None = typer.Option(None, "-i", "--input", help="Input image file (default: np_page.png in page-dir)"),
):
    """Draw annotation layer bounding boxes on top of a page image."""
    from ppx.core.helpers import draw_bboxes
    from matplotlib.colors import to_rgb

    img = np.array(Image.open(input or page_dir / "np_page.png").convert("RGB"))
    df = pd.read_parquet(page_dir / f"{layer}.parquet", engine="fastparquet")

    if query:
        df = df.query(query)

    rgb = tuple(int(c * 255) for c in to_rgb(color))
    result = draw_bboxes(img, df, color=rgb, label_column=label)

    output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(result.astype(np.uint8), mode="RGB").save(str(output))
    typer.echo(f"Saved: {output}")

@app.command(name="graph")
def DrawGraph(
    page_dir: Path = typer.Option(..., "--page-dir", help="Input directory containing page image and parquet files"),
    output: Path = typer.Option(..., "-o", "--output", help="Output file"),
    layers: list[str] = typer.Option(..., "--layers", help="Layer names (parquet file without extension)"),
    color: str = typer.Option("red", "--color", help="Color name"),
    k: int = typer.Option(5, "-k", help="Number of nearest neighbors"),
    input: Path | None = typer.Option(None, "-i", "--input", help="Input image file (default: np_page.png in page-dir)"),
    line_width: int = typer.Option(1, "--line-width", help="Width of graph edges in pixels"),
    circle_size: int = typer.Option(4, "--circle-size", help="Radius of node circles in pixels"),
    opacity: float = typer.Option(0.5, "--opacity", help="Opacity of the drawn layer (0.0–1.0)"),
):
    from ppx.core.storage import load_bboxes
    from ppx.core.layout_graph import build_layout_knn_graph, get_graph_coordinates
    from ppx.core.helpers import draw_graph
    from matplotlib.colors import to_rgb

    df = load_bboxes(page_dir, *layers)
    graph = build_layout_knn_graph(df, k=k)
    graph_coords = get_graph_coordinates(df, graph)
    img = np.array(Image.open(input or page_dir / "np_page.png").convert("RGB"))
    rgb = tuple(int(c * 255) for c in to_rgb(color))
    result = draw_graph(img, graph_coords, color=rgb, line_width=line_width, circle_size=circle_size, opacity=opacity)
    output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(result.astype(np.uint8), mode="RGB").save(str(output))
    typer.echo(f"Saved: {output}")