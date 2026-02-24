import typer
from pathlib import Path
from typing import Annotated

app = typer.Typer()


@app.command()
def run(
    pdf_file: Annotated[Path, typer.Argument(help="PDF file to process")],
    output: Annotated[Path, typer.Option("-o", "--output", help="Output directory")] = Path("."),
    overwrite: Annotated[bool, typer.Option("--overwrite", help="Overwrite existing output")] = False,
):
    """Run OCR and layout analysis on a PDF file, storing results to disk."""
    from ppx.core.helpers import get_page_tensors
    from ppx.core.ocr import get_visual_tokens, get_structv3
    from ppx.core.storage import store

    doc_dir = output / pdf_file.stem
    typer.echo(f"Input:  {pdf_file}")
    typer.echo(f"Output: {doc_dir}")

    doc = get_page_tensors(pdf_file)
    n = len(doc.pages)
    typer.echo(f"Pages:  {n}")

    for i, np_page in enumerate(doc.pages):
        typer.echo(f"\n[page {i}/{n - 1}]")

        typer.echo("  Running OCR ...")
        vtl = get_visual_tokens(np_page, page_index=i)

        typer.echo("  Running layout analysis ...")
        ll, md = get_structv3(np_page, page_index=i)

        typer.echo("  Storing ...")
        for status in store(doc_dir, vtl, ll, md, overwrite=overwrite):
            typer.echo(f"    {status.message}  ({status.size:,} B)")

    typer.echo("\nDone.")
