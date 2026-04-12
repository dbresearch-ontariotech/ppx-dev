// ---------------------------------------------------------------------------
// API types
// ---------------------------------------------------------------------------

export type DocInfo = {
	filename: string;
	pages: number;
};

export type MarkdownASTNode = {
	ast_index: number;
	type: string;
	markdown: string;
};

export type LayoutNode = {
	node_id: string;
	level_index: number;
	level_name: 'region' | 'block' | 'line' | 'word';
	parent_id: string | null;
	x0: number;
	y0: number;
	x1: number;
	y1: number;
	label: string;
	content: string;
};

export type BlockAlignment = {
	ast_start: number;
	ast_end: number;
	score: number;
};

export type LineAlignment = {
	ast_index_start: number;
	char_start: number;
	ast_index_end: number;
	char_end: number;
	score: number;
};

export type DocAlignment = {
	block_alignments: Record<string, BlockAlignment>;
	line_alignments: Record<string, LineAlignment>;
};

// ---------------------------------------------------------------------------
// API URL builders
// ---------------------------------------------------------------------------

export const api = {
	documents: () => '/api/ppx',
	docInfo: (f: string) => `/api/ppx/${f}/`,
	image: (f: string, p: number) => `/api/ppx/${f}/${p}/image`,
	thumbnail: (f: string, p: number) => `/api/ppx/${f}/${p}/thumbnail`,
	markdown: (f: string, p: number) => `/api/ppx/${f}/${p}/markdown/index.md`,
	markdownAst: (f: string, p: number) => `/api/ppx/${f}/${p}/markdown/ast`,
	markdownResource: (f: string, p: number, path: string) =>
		`/api/ppx/${f}/${p}/markdown/${path}`,
	layout: (f: string, p: number) => `/api/ppx/${f}/${p}/layout`,
	alignment: (f: string, p: number) => `/api/ppx/${f}/${p}/alignment`,
};

// ---------------------------------------------------------------------------
// Fetch helpers
// ---------------------------------------------------------------------------

async function apiFetch<T>(url: string): Promise<T> {
	const r = await fetch(url);
	if (!r.ok) throw new Error(`API error ${r.status}: ${url}`);
	return r.json();
}

export const fetchDocuments = () => apiFetch<string[]>(api.documents());
export const fetchDocInfo = (f: string) => apiFetch<DocInfo>(api.docInfo(f));
export const fetchMarkdownAst = (f: string, p: number) =>
	apiFetch<{ ast_nodes: MarkdownASTNode[] }>(api.markdownAst(f, p));
export const fetchLayout = (f: string, p: number) =>
	apiFetch<{ visual_tokens: LayoutNode[] }>(api.layout(f, p));
export const fetchAlignment = (f: string, p: number) =>
	apiFetch<DocAlignment>(api.alignment(f, p));
