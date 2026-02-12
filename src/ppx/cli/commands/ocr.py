import os
import json
from pathlib import Path
from typing import Optional

import typer
import cv2
from rich import print as rprint
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn

from ppx.core import helpers

app = typer.Typer()

@app.command("run")
def RunCommand(
    pdf_file: Path = typer.Argument(..., help="PDF file"),
    output_path: Path = typer.Option(..., "-o", help="Directory to store the OCR output"),
):
    from ppx.core import ocr

    pdf_basename = pdf_file.stem
    pages = list(helpers.get_page_tensors(pdf_file))
    os.makedirs(output_path, exist_ok=True)

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
    ) as progress:
        page_task = progress.add_task("Processing pages", total=len(pages))

        for page_index, np_page in enumerate(pages):
            page_dir = output_path / pdf_basename / str(page_index)

            if page_dir.exists():
                progress.console.print(f"  Page {page_index}: [yellow]already exists, skipping[/yellow]")
                progress.advance(page_task)
                continue

            page_dir.mkdir(parents=True, exist_ok=True)

            # Save page image once
            cv2.imwrite(str(page_dir / "page.png"), cv2.cvtColor(np_page, cv2.COLOR_RGB2BGR))

            # OCR
            progress.update(page_task, description=f"Page {page_index}: OCR")
            ocr_result = ocr.ocr(np_page)
            ocr_result.texts.to_parquet(page_dir / "ocr_texts.parquet")
            ocr_result.words.to_parquet(page_dir / "ocr_words.parquet")
            (page_dir / "ocr.json").write_text(json.dumps(ocr_result.ocr_result, ensure_ascii=False, indent=2))

            # Structure V3
            progress.update(page_task, description=f"Page {page_index}: StructureV3")
            sv3_result = ocr.structv3(np_page)
            sv3_result.layout.to_parquet(page_dir / "structv3_layout.parquet")
            (page_dir / "structv3.json").write_text(json.dumps(sv3_result.structv3_result, ensure_ascii=False, indent=2))
            md_dir = page_dir / "markdown_output"
            md_dir.mkdir(parents=True, exist_ok=True)
            (md_dir / "markdown.md").write_text(sv3_result.markdown)
            for name, np_fig in sv3_result.figures.items():
                fig_path = md_dir / name
                fig_path.parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(fig_path), cv2.cvtColor(np_fig, cv2.COLOR_RGB2BGR))

            progress.advance(page_task)

    rprint("[green]Done.[/green]")


@app.command("annotate")
def AnnotateCommand(
    page_dir: Path = typer.Argument(..., help="Page output directory (e.g. ./output/paper/5)"),
    output_file: Path = typer.Option(None, "-o", help="Output image file"),
    source: str = typer.Option("ocr_texts", "--source", help="Parquet file basename (without .parquet)"),
    query: str | None = typer.Option(None, "-q", help="Pandas query to filter rows"),
    label_column: str | None = typer.Option(None, "-l", help="Column name to use as text label on each bounding box"),
):
    import pandas as pd

    if not page_dir.exists():
        rprint(f"[red]Page directory not found:[/red] {page_dir}")
        raise typer.Exit(1)

    # Load base image
    image_path = page_dir / "page.png"
    np_image = cv2.cvtColor(cv2.imread(str(image_path)), cv2.COLOR_BGR2RGB)

    # Load parquet source
    parquet_path = page_dir / f"{source}.parquet"
    if not parquet_path.exists():
        rprint(f"[red]Parquet file not found:[/red] {parquet_path}")
        raise typer.Exit(1)

    df = pd.read_parquet(parquet_path)
    if query:
        df = df.query(query)

    # Annotate
    annotated = helpers.annotate(np_image, df, (0, 0, 255), label_column=label_column)

    # Save
    if output_file is None:
        # Derive default name from parent (pdf basename) and dir name (page number)
        output_file = Path(f"{page_dir.parent.name}_{page_dir.name}.png")
    cv2.imwrite(str(output_file), cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR))
    rprint(f"[green]Saved:[/green] {output_file} ({len(df)} rectangles)")