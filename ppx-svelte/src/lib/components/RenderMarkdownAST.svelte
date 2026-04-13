<script lang="ts">
	import { tick } from 'svelte';
	import { TOKEN_LEVEL_COLORS, type BlockAlignment, type MarkdownASTNode } from '$lib/appstate.svelte';
	import RenderMarkdownASTNode from './RenderMarkdownASTNode.svelte';

	type Segment = { nodes: MarkdownASTNode[]; highlighted: boolean };

	type Props = {
		ast: MarkdownASTNode[];
		baseurl: string;
		activeAlignments?: Promise<BlockAlignment[]>;
	};

	let { ast, baseurl, activeAlignments }: Props = $props();

	let container: HTMLElement | undefined = $state();

	$effect(() => {
		const promise = activeAlignments ?? Promise.resolve([]);
		promise.then(async (alignments) => {
			if (alignments.length === 0) return;
			await tick();
			const target = container?.querySelector('[data-highlighted]');
			target?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
		});
	});

	function buildSegments(alignments: BlockAlignment[]): Segment[] {
		const highlighted = new Set(
			alignments.flatMap((ba) =>
				Array.from({ length: ba.ast_end - ba.ast_start }, (_, i) => ba.ast_start + i)
			)
		);

		const segments: Segment[] = [];
		for (const node of ast) {
			const h = highlighted.has(node.ast_index);
			const last = segments.at(-1);
			if (last && last.highlighted === h) {
				last.nodes.push(node);
			} else {
				segments.push({ nodes: [node], highlighted: h });
			}
		}
		return segments;
	}
</script>

<div bind:this={container}>
{#await activeAlignments ?? Promise.resolve([]) then alignments}
	{@const segments = buildSegments(alignments)}
	{#each segments as segment (segment.nodes[0]?.ast_index)}
		{#if segment.highlighted}
			<div
				data-highlighted
				style:border="3px solid {TOKEN_LEVEL_COLORS['block']}"
				style:border-radius="4px"
				style:padding="0.25rem 0.5rem"
				style:margin-bottom="0.5rem"
			>
				{#each segment.nodes as astNode (astNode.ast_index)}
					<RenderMarkdownASTNode {astNode} {baseurl} />
				{/each}
			</div>
		{:else}
			{#each segment.nodes as astNode (astNode.ast_index)}
				<RenderMarkdownASTNode {astNode} {baseurl} />
			{/each}
		{/if}
	{/each}
{/await}
</div>
