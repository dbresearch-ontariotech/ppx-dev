import { page } from '$app/state';
import { SvelteMap, SvelteSet } from 'svelte/reactivity';

// ---------------------------------------------------------------------------
// UI types
// ---------------------------------------------------------------------------

export type TokenLevel = 'block' | 'line' | 'word';

export const TOKEN_LEVEL_COLORS: Record<TokenLevel, string> = {
	block: '#3b82f6',  // blue-500
	line:  '#22c55e',  // green-500
	word:  '#fb923c',  // orange-400
};

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

export const fetchDocInfo = (f: string) => apiFetch<DocInfo>(api.docInfo(f));

const fetchDocuments = () => apiFetch<string[]>(api.documents());
const fetchMarkdownAst = (f: string, p: number) =>
	apiFetch<{ ast_nodes: MarkdownASTNode[] }>(api.markdownAst(f, p));
const fetchLayout = (f: string, p: number) =>
	apiFetch<{ visual_tokens: LayoutNode[] }>(api.layout(f, p));
const fetchAlignment = (f: string, p: number) =>
	apiFetch<DocAlignment>(api.alignment(f, p));

// ---------------------------------------------------------------------------
// App state
// Reactive derived state is held in a class so it can be exported safely.
// Consumers import `appState` and access e.g. `appState.filename`.
// ---------------------------------------------------------------------------

class AppState {
	// Route params — derived from SvelteKit's reactive page store
	readonly filename = $derived.by(() => page.params.filename ?? null);
	readonly pageIndex = $derived.by(() =>
		page.params.page_index != null ? +page.params.page_index : null
	);

	// Document list — fetched once at startup
	readonly documents: Promise<string[]> = fetchDocuments();

	// Per-page data — re-derived (and re-fetched) whenever params change
	readonly docInfo = $derived.by((): Promise<DocInfo | null> => {
		const f = this.filename;
		return f ? fetchDocInfo(f) : Promise.resolve(null);
	});

	readonly layout = $derived.by((): Promise<LayoutNode[] | null> => {
		const f = this.filename;
		const p = this.pageIndex;
		return f != null && p != null
			? fetchLayout(f, p).then((r) => r.visual_tokens)
			: Promise.resolve(null);
	});

	readonly markdownAst = $derived.by((): Promise<MarkdownASTNode[] | null> => {
		const f = this.filename;
		const p = this.pageIndex;
		return f != null && p != null
			? fetchMarkdownAst(f, p).then((r) => r.ast_nodes)
			: Promise.resolve(null);
	});

	// UI state
	readonly activatedVisualTokens = new SvelteSet<string>();
	rawSource = $state(true);

	readonly showVisualTokens = new SvelteMap<TokenLevel, boolean>([
		['block', false],
		['line', false],
		['word', false],
	]);

	readonly alignment = $derived.by((): Promise<DocAlignment | null> => {
		const f = this.filename;
		const p = this.pageIndex;
		return f != null && p != null
			? fetchAlignment(f, p)
			: Promise.resolve(null);
	});
}

export const appState = new AppState();
