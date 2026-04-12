<script lang="ts">
	import { page } from '$app/state';
	import { api } from '$lib/appstate.svelte';
</script>

<div class="flex justify-center">
	<img
		src={api.image(page.params.filename, +page.params.page_index)}
		alt="Page {+page.params.page_index + 1}"
		class="max-w-full rounded-md shadow-md"
	/>
</div>
