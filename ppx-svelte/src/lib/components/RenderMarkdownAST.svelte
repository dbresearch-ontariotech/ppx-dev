<script lang="ts">
	import { tick } from 'svelte';
	import { TOKEN_LEVEL_COLORS, type BlockAlignment, type LineAlignment, type MarkdownASTNode } from '$lib/appstate.svelte';
	import RenderMarkdownASTNode from './RenderMarkdownASTNode.svelte';

	type CharRange = { start: number; end: number };
	type Segment = { nodes: MarkdownASTNode[]; highlighted: boolean };

	type Props = {
		ast: MarkdownASTNode[];
		baseurl: string;
		activeAlignments?: Promise<BlockAlignment[]>;
		activeLineAlignments?: Promise<LineAlignment[]>;
	};

	let { ast, baseurl, activeAlignments, activeLineAlignments }: Props = $props();

	let container: HTMLElement | undefined = $state();

	$effect(() => {
		const blockPromise = activeAlignments ?? Promise.resolve([]);
		const linePromise = activeLineAlignments ?? Promise.resolve([]);
		Promise.all([blockPromise, linePromise]).then(async ([alignments, lineAlignments]) => {
			if (alignments.length === 0 && lineAlignments.length === 0) return;
			await tick();
			// Prefer the char-level span; fall back to the block-level div.
			const target =
				container?.querySelector('[data-line-highlight]') ??
				container?.querySelector('[data-highlighted]');
			target?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
		});
	});

	function buildSegments(alignments: BlockAlignment[]): Segment[] {
		const highlighted = new Set(
			alignments.flatMap((ba) =>
				Array.from({ length: ba.ast_end - ba.ast_start + 1 }, (_, i) => ba.ast_start + i)
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

	function getCharRanges(lineAlignments: LineAlignment[], astNode: MarkdownASTNode): CharRange[] {
		const i = astNode.ast_index;
		const len = astNode.markdown.length;
		const ranges: CharRange[] = [];

		for (const la of lineAlignments) {
			if (i < la.ast_index_start || i > la.ast_index_end) continue;

			const start = i === la.ast_index_start ? la.char_start : 0;
			const end   = i === la.ast_index_end   ? la.char_end + 1 : len;  // char_end inclusive → +1 for slice

			if (start < end) ranges.push({ start, end });
		}

		return ranges;
	}
</script>

<div bind:this={container}>
{#await Promise.all([activeAlignments ?? Promise.resolve([]), activeLineAlignments ?? Promise.resolve([])]) then [alignments, lineAlignments]}
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
					<div data-ast-index={astNode.ast_index}>
						<RenderMarkdownASTNode
							{astNode}
							{baseurl}
							charRanges={getCharRanges(lineAlignments, astNode)}
						/>
					</div>
				{/each}
			</div>
		{:else}
			{#each segment.nodes as astNode (astNode.ast_index)}
				<div data-ast-index={astNode.ast_index}>
					<RenderMarkdownASTNode
						{astNode}
						{baseurl}
						charRanges={getCharRanges(lineAlignments, astNode)}
					/>
				</div>
			{/each}
		{/if}
	{/each}
{/await}
</div>
