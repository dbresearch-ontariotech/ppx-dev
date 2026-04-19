<script lang="ts">
	import { api, type DocAlignment, type LayoutNode, type SelectedMarkdownRange } from '$lib/appstate.svelte';
	import PageImage from './PageImage.svelte';

	type Props = {
		filename: string;
		pageIndex: number;
		visibleTokens?: Promise<LayoutNode[]>;
		alignment?: Promise<DocAlignment | null>;
		selectedMarkdownRange?: SelectedMarkdownRange;
	};

	let { filename, pageIndex, visibleTokens, alignment, selectedMarkdownRange = null }: Props = $props();
</script>

<div class="relative inline-block">
	{#key `${filename}-${pageIndex}`}
		<PageImage
			src={api.image(filename, pageIndex)}
			alt="Page {pageIndex + 1}"
			{visibleTokens}
			{alignment}
			{selectedMarkdownRange}
		/>
	{/key}
</div>
