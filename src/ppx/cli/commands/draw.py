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
    from ppx.core.layout.layout_graph import build_layout_knn_graph, get_graph_coordinates
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

@app.command(name="tree")
def DrawTree(
    page_dir: Path = typer.Argument(..., help="Page directory containing layout-tree.parquet"),
    output: Path = typer.Option(..., "-o", "--output", help="Output .html file"),
):
    """Render the layout tree as a self-contained interactive HTML page."""
    import json

    tree = pd.read_parquet(page_dir / "layout-tree.parquet")

    # Serialise rows; replace NaN parent_id with null
    nodes = []
    for _, row in tree.iterrows():
        parent = row["parent_id"]
        nodes.append({
            "node_id":    str(row["node_id"]),
            "level_name": str(row["level_name"]),
            "level_index": int(row["level_index"]),
            "parent_id":  None if (parent is None or (isinstance(parent, float) and pd.isna(parent))) else str(parent),
            "content":    str(row["content"]) if row["content"] else "",
        })

    data_json = json.dumps(nodes)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Layout Tree — {page_dir}</title>
<style>
  body {{ font-family: monospace; font-size: 13px; margin: 1em 2em; background: #fafafa; }}
  h1   {{ font-size: 1.1em; color: #333; }}
  .node        {{ margin: 0; padding: 0; }}
  .header      {{ display: flex; align-items: baseline; gap: 0.5em;
                  cursor: pointer; padding: 2px 4px; border-radius: 3px;
                  user-select: none; white-space: nowrap; }}
  .header:hover {{ background: #e8e8e8; }}
  .toggle      {{ width: 1em; text-align: center; flex-shrink: 0; color: #888; }}
  .children    {{ margin-left: 1.6em; border-left: 1px solid #ddd; padding-left: 4px; }}
  .badge       {{ border-radius: 3px; padding: 0px 5px; font-size: 11px; flex-shrink: 0; }}
  .content     {{ color: #444; overflow: hidden; text-overflow: ellipsis; }}
  .node-id     {{ font-weight: bold; flex-shrink: 0; }}
  .level-region .badge {{ background:#dae8fc; }}
  .level-block  .badge {{ background:#d5e8d4; }}
  .level-line   .badge {{ background:#fff2cc; }}
  .level-word   .badge {{ background:#f8cecc; }}
</style>
</head>
<body>
<h1>Layout Tree &mdash; <code>{page_dir}</code></h1>
<div id="root"></div>
<script>
const data = {data_json};

// Build node map and children lists
const byId = {{}};
data.forEach(n => {{ byId[n.node_id] = {{ ...n, children: [] }}; }});
const roots = [];
data.forEach(n => {{
  if (n.parent_id && byId[n.parent_id]) byId[n.parent_id].children.push(byId[n.node_id]);
  else roots.push(byId[n.node_id]);
}});

function renderNode(node) {{
  const div = document.createElement('div');
  div.className = `node level-${{node.level_name}}`;

  const header = document.createElement('div');
  header.className = 'header';

  const toggle = document.createElement('span');
  toggle.className = 'toggle';

  const nodeId = document.createElement('span');
  nodeId.className = 'node-id';
  nodeId.textContent = node.node_id;

  const badge = document.createElement('span');
  badge.className = 'badge';
  badge.textContent = node.level_name;

  const content = document.createElement('span');
  content.className = 'content';
  content.textContent = node.content;

  header.appendChild(toggle);
  header.appendChild(nodeId);
  header.appendChild(badge);
  header.appendChild(content);
  div.appendChild(header);

  if (node.children.length > 0) {{
    const childrenDiv = document.createElement('div');
    childrenDiv.className = 'children';
    node.children.forEach(c => childrenDiv.appendChild(renderNode(c)));
    div.appendChild(childrenDiv);

    // Collapse line and word levels by default
    const collapsed = node.level_name === 'line' || node.level_name === 'block';
    childrenDiv.style.display = collapsed ? 'none' : '';
    toggle.textContent = collapsed ? '▶' : '▼';

    header.addEventListener('click', () => {{
      const isHidden = childrenDiv.style.display === 'none';
      childrenDiv.style.display = isHidden ? '' : 'none';
      toggle.textContent = isHidden ? '▼' : '▶';
    }});
  }} else {{
    toggle.textContent = '·';
  }}

  return div;
}}

const root = document.getElementById('root');
roots.forEach(n => root.appendChild(renderNode(n)));
</script>
</body>
</html>"""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    typer.echo(f"Saved: {output} ({output.stat().st_size:,} B)")