<script lang="ts">
	type Props = {
		promise: Promise<unknown>;
		label: string;
	};

	let { promise, label }: Props = $props();
</script>

{#await promise}
	<span class="text-muted-foreground bg-muted rounded px-1.5 py-0.5 text-xs">
		{label}
	</span>
{:then}
	<span class="rounded bg-green-100 px-1.5 py-0.5 text-xs text-green-700">
		{label}
	</span>
{:catch}
	<span class="rounded bg-red-100 px-1.5 py-0.5 text-xs text-red-700">
		{label}
	</span>
{/await}
