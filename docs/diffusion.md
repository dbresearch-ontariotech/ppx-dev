# Thesis diffusion

This is an incremental refinement stable diffusion of generating a complete thesis paper.

The paper is written in Latex in @arxiv_md_align/main.tex

## Fixtures:

- Paper author list is fixed.

## Diffusion Context

### Template paper

Refer to @2506.07001v2.pdf as a template to follow in paper organization, section layout, and writing style.

### Historic development documents

Refer to @../ideas for the incremental design documents of the system

### Fully functional implementation

Refer to @../src/ppx-ocr and @../src/ppx-align for the python implementation.  In particular,

- @../ppx-ocr/src/ppx-ocr/core/ocr.py describes the OCR service that powers the underlying layout analysis and OCR text extraction.
- @../ppx-ocr/src/ppx-ocr/core/ocr.py describes the data structures
- @../ppx-align/src/ppx-align/core/layout.py is the layout tree and related algorithms.
- @../ppx-align/src/ppx-align/core/algo.py is the collection of general purpose algorithms used for a previous experiment.
- @../ppx-align/src/ppx-align/core/align.py is the new alignment algorithms used for embedding alignment.

### References

The bibtex file contains possible references to be included in the citations.  @arxiv_md_align/references.bib

## Reverse Diffusion Steps:

The following steps are the reverse diffusion process, going from high level structural content generation to lower level detailed content generation.

!!! important generation guideline:
Do not generate full paragraphs by default.  Instead, rely on nested bullets and short passages by default.  Exceptions to this rule can be made, especially for generating pseudo-code, table and figure descriptions.  Explicit instruction for full text generation will be given only at later stages of the reverse diffusion process.

Be liberal at applying formatting and latex layout to make the document appealing.

### Step 1: Thesis outline

1. Generating only the paper sections and do not include any content.

2. Inspect the context and fill in the title and abstract only.

### Step 2: References of each section

For each section, go through the @references.bib and select suitable references that can be cited for that particular section.  Do not include citations that are not necessary, or not relevant.  Not all sections need to have citations.

### Step 3: Detailed generation of "Problem Formulation"

Formulate the problem of multimodal alignment.

- Provide clear definitions of all concepts
- Write in set-theoretic and formal logic mathematical exposition style.
- Use standard mathematical symbols and notations in amsmath.
- Use definition environments to separate the concepts.

Use tikz to draw illustrative diagrams with captions as labeled figures.

- Include a diagram of the visual tokens (already there)
- Include a diagram of the text tokens (layout vertically)
- Include a diagram to illustrate the matching between visual tokens and text tokens as a mapping.

### Step 4: Detailed generation of "Alignment Algorithms"

Write the section in detail.  Use algorithm environment.  Refer to the template paper.  Provide amble amount of explanation.

Present the algorithms in the sequence:

- dynamic programming to obtain optimal alignment, but argue that it's not scalable.

- greedy approximation for large scale alignment situations.

- hybrid version to switch to greedy only when the alignment problem instance is large.

Use tikz diagram to illustrate difficult algorithmic designs.

### Step 5: Detailed generation of "System Implementation"

Write this section in detail.  Expand placeholder item lists with full text.

Use tikz to draw system architecture diagrams.

Provide python sample code to illustrate implementation details, but not full python code list (too much space).

Dedicate a subsection to especially describe paddle-ocr integration with the paddlepaddle neural network platform.

Dedicate a subsection to describe the client/server architecture to support intelligent AI-powered Web application for advanced document reading.

