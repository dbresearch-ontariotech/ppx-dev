<script lang="ts">
	import { TOKEN_LEVEL_COLORS, type MarkdownASTNode } from '$lib/appstate.svelte';
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

	const markdown = $derived(
		// Step 1: apply char highlights using original offsets from the backend.
		// Step 2: rewrite relative image URLs (after highlights, so offsets stay valid).
		// Step 3: fix OCR bug — missing space before opening $ of inline LaTeX.
		//         Match a complete $...$ span preceded by a non-space char and insert the space.
		//         Matching the full span avoids misidentifying a closing $ as an opener.
		applyHighlights(astNode.markdown, charRanges)
			.replace(
				/!\[([^\]]*)\]\((?!https?:\/\/|\/)([^)]+)\)/g,
				(_, alt, url) => `![${alt}](${baseurl}${url})`
			)
			.replace(
				/(<img\s[^>]*src=)(["'])(?!https?:\/\/|\/)([^"']+)\2/gi,
				(_, tag, quote, url) => `${tag}${quote}${baseurl}${url}${quote}`
			)
			.replace(/(?<![$\s\\])\$/g, ' $')
	);
</script>

<Markdown {markdown} />
