<script lang="ts">
	import { appState, api, type LayoutNode, type TokenLevel, type BlockAlignment, type LineAlignment } from '$lib/appstate.svelte';
	const activeLevel = $derived.by((): TokenLevel | null => {
		for (const [level, on] of appState.showVisualTokens) {
			if (on) return level as TokenLevel;
		}
		return null;
	});
	import {
		ResizablePaneGroup,
		ResizablePane,
		ResizableHandle,
	} from '$lib/components/ui/resizable';
	import PageViewer from '$lib/components/PageViewer.svelte';
	import RenderMarkdownAST from '$lib/components/RenderMarkdownAST.svelte';

	const visibleTokens: Promise<LayoutNode[]> = $derived.by(() => {
		const show = {
			block: appState.showVisualTokens.get('block') ?? false,
			line:  appState.showVisualTokens.get('line')  ?? false,
			word:  appState.showVisualTokens.get('word')  ?? false,
		};
		return appState.layout.then(
			(tokens) => (tokens ?? []).filter((t) => show[t.level_name as TokenLevel] ?? false)
		);
	});

	// Read activatedVisualTokens synchronously to establish reactive dependency,
	// then resolve the alignment for each activated node.
	const activeAlignments: Promise<BlockAlignment[]> = $derived.by(() => {
		const activatedIds = [...appState.activatedVisualTokens];
		return appState.alignment.then((alignment) => {
			if (!alignment || activatedIds.length === 0) return [];
			return activatedIds
				.map((id) => alignment.block_alignments[id])
				.filter((ba): ba is BlockAlignment => ba != null);
		});
	});

	const activeLineAlignments: Promise<LineAlignment[]> = $derived.by(() => {
		const activatedIds = [...appState.activatedVisualTokens];
		return appState.alignment.then((alignment) => {
			if (!alignment || activatedIds.length === 0) return [];
			return activatedIds
				.map((id) => alignment.line_alignments[id])
				.filter((la): la is LineAlignment => la != null);
		});
	});
</script>

<ResizablePaneGroup direction="horizontal" class="h-full">
	<ResizablePane defaultSize={50} minSize={20}>
		<div class="h-full overflow-auto p-4">
			{#if appState.filename != null && appState.pageIndex != null}
				<PageViewer
					filename={appState.filename}
					pageIndex={appState.pageIndex}
					{visibleTokens}
					alignment={appState.alignment}
					selectedMarkdownRange={appState.selectedMarkdownRange}
				/>
			{/if}
		</div>
	</ResizablePane>

	<ResizableHandle withHandle />

	<ResizablePane defaultSize={50} minSize={20}>
		<div class="h-full overflow-auto p-4">
			{#await appState.markdownAst}
				<!-- loading: status badge in header already indicates this -->
			{:then ast}
				{#if ast && appState.filename != null && appState.pageIndex != null}
					<RenderMarkdownAST
						{ast}
						{activeAlignments}
						{activeLineAlignments}
						{activeLevel}
						baseurl={api.markdownResource(appState.filename, appState.pageIndex, '')}
					/>
				{/if}
			{:catch err}
				<p class="text-destructive text-sm">{err.message}</p>
			{/await}
		</div>
	</ResizablePane>
</ResizablePaneGroup>
