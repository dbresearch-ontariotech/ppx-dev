<script lang="ts">
	import { TOKEN_LEVEL_COLORS, appState, type MarkdownASTNode } from '$lib/appstate.svelte';
	import Markdown from './Markdown.svelte';

	type CharRange = { start: number; end: number };

	type Props = {
		astNode: MarkdownASTNode;
		baseurl: string;
		charRanges?: CharRange[];
	};

	let { astNode, baseurl, charRanges = [] }: Props = $props();

	// Inject highlight spans around char ranges in the raw markdown source.
	// Ranges are sorted and merged before injection to handle overlaps.
	function applyHighlights(src: string, ranges: CharRange[]): string {
		if (ranges.length === 0) return src;

		const sorted = [...ranges].sort((a, b) => a.start - b.start);
		const merged: CharRange[] = [];
		for (const r of sorted) {
			const last = merged.at(-1);
			if (last && r.start <= last.end) {
				last.end = Math.max(last.end, r.end);
			} else {
				merged.push({ ...r });
			}
		}

		const color = TOKEN_LEVEL_COLORS['line'];
		let result = '';
		let cursor = 0;
		for (const { start, end } of merged) {
			result += src.slice(cursor, start);
			result += `<span data-line-highlight style="background-color:${color}33;border-radius:2px;padding:0 0.1em">${src.slice(start, end)}</span>`;
			cursor = end;
		}
		result += src.slice(cursor);
		return result;
	}

	// Rewrite relative image URLs (both markdown and HTML img syntax).
	function rewriteImageUrls(src: string): string {
		return src
			.replace(
				/!\[([^\]]*)\]\((?!https?:\/\/|\/)([^)]+)\)/g,
				(_, alt, url) => `![${alt}](${baseurl}${url})`
			)
			.replace(
				/(<img\s[^>]*src=)(["'])(?!https?:\/\/|\/)([^"']+)\2/gi,
				(_, tag, quote, url) => `${tag}${quote}${baseurl}${url}${quote}`
			);
	}

	// For rendered mode: highlights → URL rewrite → LaTeX space fix → marked parses everything.
	const markdown = $derived(
		rewriteImageUrls(applyHighlights(astNode.markdown, charRanges))
			.replace(/(?<![$\s\\])\$/g, ' $')
	);

	// For raw mode: highlights → URL rewrite → convert ![alt](url) to <img> for display in <pre>.
	const rawMarkdown = $derived(
		rewriteImageUrls(applyHighlights(astNode.markdown, charRanges))
			.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1">')
	);
</script>

<Markdown
	markdown={appState.rawSource ? rawMarkdown : markdown}
	rawSource={appState.rawSource}
/>
