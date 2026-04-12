<script lang="ts">
	import { page } from '$app/state';
	import { api, fetchDocInfo } from '$lib/appstate.svelte';
	import { Spinner } from '$lib/components/ui/spinner';

	const docInfo = $derived(fetchDocInfo(page.params.filename));
</script>

{#await docInfo}
	<div class="text-muted-foreground flex items-center gap-2 py-8 text-sm">
		<Spinner class="size-4" />
		Loading pages...
	</div>
{:then info}
	<div class="grid grid-cols-[repeat(auto-fill,minmax(160px,1fr))] gap-4">
		{#each { length: info.pages } as _, i (i)}
			<a href="/{page.params.filename}/{i}/" class="group flex flex-col items-center gap-2">
				<div
					class="border-border bg-muted w-full overflow-hidden rounded-md border shadow-sm transition-shadow group-hover:shadow-md"
				>
					<img
						src={api.thumbnail(page.params.filename, i)}
						alt="Page {i + 1}"
						class="h-auto w-full object-contain"
						loading="lazy"
					/>
				</div>
				<span class="text-muted-foreground text-xs">Page {i + 1}</span>
			</a>
		{/each}
	</div>
{:catch err}
	<p class="text-destructive text-sm">{err.message}</p>
{/await}
