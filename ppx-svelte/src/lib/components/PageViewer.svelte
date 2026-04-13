<script lang="ts">
	import { api, type LayoutNode } from '$lib/appstate.svelte';
	import PageImage from './PageImage.svelte';

	type Props = {
		filename: string;
		pageIndex: number;
		visibleTokens?: Promise<LayoutNode[]>;
	};

	let { filename, pageIndex, visibleTokens }: Props = $props();
</script>

<div class="relative inline-block">
	{#key `${filename}-${pageIndex}`}
		<PageImage
			src={api.image(filename, pageIndex)}
			alt="Page {pageIndex + 1}"
			{visibleTokens}
		/>
	{/key}
</div>
