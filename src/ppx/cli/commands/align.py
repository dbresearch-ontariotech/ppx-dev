from pathlib import Path

import typer
from rich import print as rprint

app = typer.Typer()


@app.command("run")
def RunCommand(
    page_dir: Path = typer.Argument(..., help="Page output directory containing page.png"),
    source: str = typer.Option(..., "--source", help="Parquet file stem in page_dir (e.g. ocr_words)"),
    text: str = typer.Option(..., "--text", help="Query text to compute similarity against"),
    kx: float = typer.Option(..., "--kx", help="Neighborhood width as fraction of page width"),
    ky: float = typer.Option(..., "--ky", help="Neighborhood height as fraction of page height"),
    dx: float = typer.Option(..., "--dx", help="Grid spacing as fraction of page width"),
    dy: float = typer.Option(..., "--dy", help="Grid spacing as fraction of page height"),
    opacity: float = typer.Option(0.3, "--opacity", help="Heatmap overlay opacity"),
    output_file: Path = typer.Option(..., "-o", help="Output image file"),
):
    import cv2
    import numpy as np
    import pandas as pd
    import matplotlib.cm as cm

    from ppx.core.alignment import compute_similarity
    from ppx.core.models import VisualTokens

    # Load page image
    image_path = page_dir / "page.png"
    if not image_path.exists():
        rprint(f"[red]Page image not found:[/red] {image_path}")
        raise typer.Exit(1)
    np_image = cv2.cvtColor(cv2.imread(str(image_path)), cv2.COLOR_BGR2RGB)
    h, w = np_image.shape[:2]

    # Load visual tokens
    parquet_path = page_dir / f"{source}.parquet"
    if not parquet_path.exists():
        rprint(f"[red]Parquet file not found:[/red] {parquet_path}")
        raise typer.Exit(1)
    df = pd.read_parquet(parquet_path)
    vtokens = VisualTokens(words=df, page_height=h, page_width=w)

    # Build meshgrid of page locations
    step_x = int(dx * w)
    step_y = int(dy * h)
    xs = np.arange(0, w, step_x)
    ys = np.arange(0, h, step_y)
    grid_x, grid_y = np.meshgrid(xs, ys)
    page_locs = np.column_stack([grid_x.ravel(), grid_y.ravel()])

    # Compute similarity scores
    scores = compute_similarity(vtokens, page_locs, text, kx=kx, ky=ky)

    # Reshape scores to grid
    score_grid = scores.reshape(len(ys), len(xs))

    # Resize score grid to full image dimensions
    heatmap_resized = cv2.resize(score_grid, (w, h), interpolation=cv2.INTER_LINEAR)

    # Normalize to [0, 1] for colormap
    vmax = heatmap_resized.max()
    if vmax > 0:
        heatmap_norm = heatmap_resized / vmax
    else:
        heatmap_norm = heatmap_resized

    # Apply colormap (jet) and convert to RGB uint8
    heatmap_color = (cm.jet(heatmap_norm)[:, :, :3] * 255).astype(np.uint8)

    # Blend with original image
    blended = cv2.addWeighted(np_image, 1 - opacity, heatmap_color, opacity, 0)

    # Save
    cv2.imwrite(str(output_file), cv2.cvtColor(blended, cv2.COLOR_RGB2BGR))
    rprint(f"[green]Saved:[/green] {output_file} (grid {len(xs)}x{len(ys)}, max score {vmax:.3f})")
