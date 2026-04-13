<script lang="ts">
	import type { MarkdownASTNode } from '$lib/appstate.svelte';
	import Markdown from './Markdown.svelte';

	type Props = { astNode: MarkdownASTNode; baseurl: string };
	let { astNode, baseurl }: Props = $props();

	// Prefix relative image URLs with baseurl.
	// Handles both markdown syntax ![alt](url) and HTML <img src="url"> / <img src='url'>
	const markdown = $derived(
		astNode.markdown
			.replace(
				/!\[([^\]]*)\]\((?!https?:\/\/|\/)([^)]+)\)/g,
				(_, alt, url) => `![${alt}](${baseurl}${url})`
			)
			.replace(
				/(<img\s[^>]*src=)(["'])(?!https?:\/\/|\/)([^"']+)\2/gi,
				(_, tag, quote, url) => `${tag}${quote}${baseurl}${url}${quote}`
			)
	);
</script>

<Markdown {markdown} />
