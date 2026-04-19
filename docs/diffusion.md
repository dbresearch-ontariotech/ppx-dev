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
- @../ppx-align/src/ppx-align/core/md.py is the collection of method to build the AST and markdown content.

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

- Include a diagram of the visual tokens
- Include a diagram of the text tokens (layout vertically)
- Include a diagram to illustrate the matching between visual tokens and text tokens as a mapping.

### Step 4: Detailed generation of "Alignment Algorithms"

Write the section in detail by expanding the placeholder item lists with full text.  Use algorithm environment.  Refer to the template paper.  Provide amble amount of explanation.

Present the algorithms in the sequence:

1. Semantic Embeddings of Visual and Textual Tokens — SentenceTransformer encoding of both modalities.
2. Cosine Similarity and Max-Weight Bipartite Matching — the shared Hungarian-algorithm primitive.
3. Block-Level Alignment over AST-Node Ranges — matching visual blocks to contiguous AST-node ranges.
4. Line-Level Alignment over Word-Bounded Sub-Spans — refining within each matched block using word-span candidates with min/max length filtering.
5. Hierarchical Composition and Thresholding — how the two stages compose and how the similarity threshold governs rejection.

Use tikz diagram to illustrate difficult algorithmic designs.

### Step 5: Detailed generation of "System Implementation"

Write this section in detail.  Expand placeholder item lists with full text.

Use tikz to draw system architecture diagrams.

Provide python sample code to illustrate implementation details, but not full python code list (too much space).

Dedicate a subsection to especially describe paddle-ocr integration with the paddlepaddle neural network platform.

Dedicate a subsection to describe the client/server architecture in `ppx-align` and `ppx-svelte` to support intelligent AI-powered Web application for advanced document reading.

### Step 6: Detailed generation of Section 6 "Benchmark"

Write this section in detail. Expand the placeholder item lists with full text.

Use relevant tables from @docs/analysis.md to create tables to support the discussion of benchmarking in the paper.

- Include the diagram of the Precision, recall, F1, and error boundary.
- Include the diagrams for line benchmark uncorrupted
- Include the diagram for the line benchmark with noise.

### Step 7: Write the abstract

Expand on the bulleted list items into a detailed and coherent abstract. The abstract will reference this new desription combined with what we already have:

```
Navigating the boundaries between vast document spaces—textbooks, papers, and articles—and abstract concepts represents the grand challenge of agentic knowledge distillation. To help humanity learn faster, AI agents need specialized tools to traverse these layers. A critical missing link is the exact alignment between raw information (source text) and structured text (Markdown), which is essential for agents to translate raw data into actionable concepts and abstractions.
This thesis tackles this specific bottleneck by focusing on the navigation mechanism between documents and information. I introduce the Parsed Page eXplorer, a foundational tool that facilitates agentic learning through strict alignment between source text and Markdown. Establishing this foundation with semantic provenance empowers AI agents to seamlessly bridge the gap from documents to accessible information. Ultimately, this mechanism provides the foundation for highly efficient, agent-driven human knowledge distillation.
```

### Step 8: Detailed generation of Section 1: Introduction

Expand the introduction section in detail. Expand the placeholder item lists with full text.

In particular, ensure that an addition of the following is provided to the points already listed:

- Grant challenge of agentic knowledge distillation
- Document space (text books, papers, articles)
- Information and text (markdown)
- Concepts and abstractions
- An agent needs to have tools to navigate across the boundaries of documents, information, concepts.
- This thesis is this navigation mechanism between documents and information.


### Step 9: Related work

Expand the related work section in detail. Expand the placeholder item lists with full text.


### Step 10: Conclusion

Expand the conclusion section in detail. Expand the placeholder item lists with full text.

### Step 11: Comprehensive review of the entire document

The final step in diffusion is to do a comprehensive reivew of the entire document. This requires:

- Checking each section for logical consistency.
- Review algorithms, mathematical models, and benchmark results.
- Review section by section to ensure there are no contradictions.