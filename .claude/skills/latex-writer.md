# LaTeX Writer Skill

You are helping the user write or improve LaTeX documents.

## What to do

When this skill is invoked:

1. **Understand the request** — Specifically limit to `\begin{instruction} ... \end{instruction}`.  Once an instruction is completed, comment out the instruction block.
2. **Check context** — look for existing `.tex` files in the project to understand document class, packages already in use, and style conventions
3. **Write the LaTeX** — produce well-structured, compilable LaTeX content
4. **Explain notable choices** — briefly note any package dependencies or compilation requirements (e.g., `bibtex`, `pdflatex`, `lualatex`)

## Guidelines

- Use standard LaTeX packages unless the user specifies otherwise (`amsmath`, `graphicx`, `hyperref`, etc.)
- Prefer `\includegraphics` over raw PDF embedding
- For bibliographies, default to BibTeX/`natbib` unless the user specifies `biblatex`
- Wrap environments correctly and ensure balanced braces
- Do not add packages already imported in the preamble
- For math-heavy content, use `align` or `equation` environments over `$$`
- Keep macro definitions minimal; only introduce `\newcommand` when reuse is clear

## User request

$ARGUMENTS
