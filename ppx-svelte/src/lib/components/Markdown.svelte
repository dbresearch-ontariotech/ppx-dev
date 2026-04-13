<script lang="ts">
	import { marked } from 'marked';
	import markedKatex from 'marked-katex-extension';
	import 'katex/dist/katex.min.css';

	marked.use(markedKatex({ throwOnError: false }));

	type Props = { markdown: string; rawSource?: boolean };
	let { markdown, rawSource = false }: Props = $props();

	const html = $derived(rawSource ? '' : (marked.parse(markdown) as string));
</script>

{#if rawSource}
	<!-- eslint-disable-next-line svelte/no-at-html-tags -->
	<pre class="raw-source">{@html markdown}</pre>
{:else}
	<div class="markdown">
		<!-- eslint-disable-next-line svelte/no-at-html-tags -->
		{@html html}
	</div>
{/if}

<style>
	/* Headings */
	.markdown :global(h1) {
		font-size: 1.75rem;
		font-weight: 700;
		line-height: 1.25;
		margin-top: 1.25rem;
		margin-bottom: 0.5rem;
	}
	.markdown :global(h2) {
		font-size: 1.375rem;
		font-weight: 600;
		line-height: 1.3;
		margin-top: 1.1rem;
		margin-bottom: 0.4rem;
	}
	.markdown :global(h3) {
		font-size: 1.125rem;
		font-weight: 600;
		line-height: 1.4;
		margin-top: 1rem;
		margin-bottom: 0.35rem;
	}
	.markdown :global(h4),
	.markdown :global(h5),
	.markdown :global(h6) {
		font-size: 1rem;
		font-weight: 600;
		margin-top: 0.9rem;
		margin-bottom: 0.3rem;
	}

	/* Paragraphs & spacing */
	.markdown :global(p) {
		margin-bottom: 0.75rem;
		line-height: 1.7;
	}

	/* Inline text formatting */
	.markdown :global(strong) {
		font-weight: 700;
	}
	.markdown :global(em) {
		font-style: italic;
	}
	.markdown :global(del) {
		text-decoration: line-through;
		opacity: 0.6;
	}
	.markdown :global(u) {
		text-decoration: underline;
	}
	.markdown :global(mark) {
		background-color: oklch(0.97 0.14 100);
		padding: 0 0.15em;
		border-radius: 2px;
	}

	/* Links */
	.markdown :global(a) {
		color: oklch(0.5 0.2 264);
		text-decoration: underline;
		text-underline-offset: 2px;
	}
	.markdown :global(a:hover) {
		color: oklch(0.4 0.2 264);
	}

	/* Lists */
	.markdown :global(ul) {
		list-style-type: disc;
		padding-left: 1.5rem;
		margin-bottom: 0.75rem;
	}
	.markdown :global(ol) {
		list-style-type: decimal;
		padding-left: 1.5rem;
		margin-bottom: 0.75rem;
	}
	.markdown :global(li) {
		margin-bottom: 0.25rem;
		line-height: 1.6;
	}
	.markdown :global(li > ul),
	.markdown :global(li > ol) {
		margin-top: 0.25rem;
		margin-bottom: 0.25rem;
	}

	/* Blockquote */
	.markdown :global(blockquote) {
		border-left: 3px solid oklch(0.75 0 0);
		padding-left: 1rem;
		margin: 0.75rem 0;
		color: oklch(0.45 0 0);
		font-style: italic;
	}

	/* Inline code */
	.markdown :global(code) {
		font-family: ui-monospace, monospace;
		font-size: 0.85em;
		background-color: oklch(0.94 0 0);
		border-radius: 3px;
		padding: 0.1em 0.35em;
	}

	/* Code blocks */
	.markdown :global(pre) {
		background-color: oklch(0.94 0 0);
		border-radius: 6px;
		padding: 0.9rem 1rem;
		margin-bottom: 0.75rem;
		overflow-x: auto;
		font-size: 0.85rem;
		line-height: 1.6;
	}
	.markdown :global(pre code) {
		background: none;
		padding: 0;
		border-radius: 0;
		font-size: inherit;
	}

	/* Horizontal rule */
	.markdown :global(hr) {
		border: none;
		border-top: 1px solid oklch(0.88 0 0);
		margin: 1rem 0;
	}

	/* Tables */
	.markdown :global(table) {
		width: 100%;
		border-collapse: collapse;
		margin-bottom: 0.75rem;
		font-size: 0.9rem;
	}
	.markdown :global(thead) {
		background-color: oklch(0.95 0 0);
	}
	.markdown :global(th) {
		border: 1px solid oklch(0.85 0 0);
		padding: 0.45rem 0.75rem;
		font-weight: 600;
		text-align: left;
	}
	.markdown :global(td) {
		border: 1px solid oklch(0.88 0 0);
		padding: 0.4rem 0.75rem;
	}
	.markdown :global(tr:nth-child(even)) {
		background-color: oklch(0.975 0 0);
	}
	.markdown :global(tr:hover) {
		background-color: oklch(0.96 0 0);
	}

	/* Images */
	.markdown :global(img) {
		display: block;
		margin: 0.75rem auto;
		padding: 0.4rem;
		border: 1px solid oklch(0.88 0 0);
		border-radius: 4px;
		max-width: 100%;
	}

	.raw-source {
		font-family: ui-monospace, monospace;
		font-size: 0.8rem;
		line-height: 1.6;
		white-space: pre-wrap;
		word-break: break-word;
		margin-bottom: 0.75rem;
	}
</style>
