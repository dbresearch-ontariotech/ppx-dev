<script lang="ts">
	import { Spinner } from '$lib/components/ui/spinner';
	import { appState, TOKEN_LEVEL_COLORS, type LayoutNode, type TokenLevel } from '$lib/appstate.svelte';

	type Props = {
		src: string;
		alt: string;
		visibleTokens?: Promise<LayoutNode[]>;
	};

	let { src, alt, visibleTokens }: Props = $props();

	let loading = $state(true);
	let naturalWidth = $state(0);
	let naturalHeight = $state(0);

	// Clear hover state whenever this component mounts (page navigation remounts via {#key})
	appState.activatedVisualTokens.clear();

	function onLoad(e: Event) {
		const img = e.currentTarget as HTMLImageElement;
		naturalWidth = img.naturalWidth;
		naturalHeight = img.naturalHeight;
		loading = false;
	}
</script>

<div class="relative inline-block">
	{#if loading}
		<div class="flex items-center justify-center p-16">
			<Spinner class="size-8" />
		</div>
	{/if}

	<img
		{src}
		{alt}
		class="block max-w-full rounded-md shadow-md"
		class:hidden={loading}
		onload={onLoad}
		onerror={() => (loading = false)}
	/>

	{#if !loading && visibleTokens && naturalWidth > 0 && naturalHeight > 0}
		{#await visibleTokens then tokens}
			{#each tokens as token (token.node_id)}
				{@const color = TOKEN_LEVEL_COLORS[token.level_name as TokenLevel]}
				{@const active = appState.activatedVisualTokens.has(token.node_id)}
				<div
					role="region"
					aria-label="{token.level_name} {token.node_id}"
					style:position="absolute"
					style:left="{(token.x0 / naturalWidth) * 100}%"
					style:top="{(token.y0 / naturalHeight) * 100}%"
					style:width="{((token.x1 - token.x0) / naturalWidth) * 100}%"
					style:height="{((token.y1 - token.y0) / naturalHeight) * 100}%"
					style:border="1.5px solid {color}"
					style:background-color={active ? `${color}33` : 'transparent'}
					style:box-sizing="border-box"
					style:cursor="default"
					onmouseenter={() => appState.activatedVisualTokens.add(token.node_id)}
					onmouseleave={() => appState.activatedVisualTokens.delete(token.node_id)}
				></div>
			{/each}
		{/await}
	{/if}
</div>
