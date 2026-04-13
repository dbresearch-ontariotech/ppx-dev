<script lang="ts">
	import type { MarkdownASTNode } from '$lib/appstate.svelte';
	import RenderMarkdownASTNode from './RenderMarkdownASTNode.svelte';

	type Props = { ast: MarkdownASTNode[]; baseurl: string };
	let { ast, baseurl }: Props = $props();
</script>

{#each ast as astNode (astNode.ast_index)}
	<RenderMarkdownASTNode {astNode} {baseurl} />
{/each}
