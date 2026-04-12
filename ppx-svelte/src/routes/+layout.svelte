<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { page } from '$app/state';
	import {
		Sidebar,
		SidebarContent,
		SidebarGroup,
		SidebarGroupContent,
		SidebarGroupLabel,
		SidebarHeader,
		SidebarInset,
		SidebarMenu,
		SidebarMenuButton,
		SidebarMenuItem,
		SidebarMenuSub,
		SidebarMenuSubButton,
		SidebarMenuSubItem,
		SidebarProvider,
		SidebarRail,
		SidebarTrigger,
	} from '$lib/components/ui/sidebar';
	import {
		Accordion,
		AccordionContent,
		AccordionItem,
		AccordionTrigger,
	} from '$lib/components/ui/accordion';
	import { Spinner } from '$lib/components/ui/spinner';
	import { Separator } from '$lib/components/ui/separator';
	import { fetchDocuments, fetchDocInfo } from '$lib/appstate.svelte';

	let { children } = $props();

	const filename = $derived(page.params.filename ?? null);
	const pageIndex = $derived(page.params.page_index != null ? +page.params.page_index : null);

	const documents = fetchDocuments();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<SidebarProvider>
	<Sidebar>
		<SidebarHeader>
			<span class="px-2 text-base font-semibold">Documents</span>
		</SidebarHeader>
		<SidebarContent>
			<SidebarGroup>
				<SidebarGroupLabel>Files</SidebarGroupLabel>
				<SidebarGroupContent>
					{#await documents}
						<div class="text-muted-foreground flex items-center gap-2 px-2 py-4 text-sm">
							<Spinner class="size-4" />
							Loading...
						</div>
					{:then docs}
						<Accordion type="multiple" value={filename ? [filename] : []}>
							{#each docs as doc (doc)}
								<AccordionItem value={doc} class="border-none">
									<SidebarMenu>
										<SidebarMenuItem>
											<AccordionTrigger class="py-0 hover:no-underline">
												<SidebarMenuButton isActive={filename === doc}>
													{#snippet child({ props })}
														<a href="/{doc}/" {...props}>{doc}</a>
													{/snippet}
												</SidebarMenuButton>
											</AccordionTrigger>
										</SidebarMenuItem>
									</SidebarMenu>
									<AccordionContent class="pb-0">
										{#await fetchDocInfo(doc)}
											<div class="text-muted-foreground flex items-center gap-2 px-4 py-2 text-xs">
												<Spinner class="size-3" />
											</div>
										{:then info}
											<SidebarMenu>
												<SidebarMenuSub>
													{#each { length: info.pages } as _, i (i)}
														<SidebarMenuSubItem>
															<SidebarMenuSubButton
																href="/{doc}/{i}/"
																isActive={filename === doc && pageIndex === i}
															>
																Page {i + 1}
															</SidebarMenuSubButton>
														</SidebarMenuSubItem>
													{/each}
												</SidebarMenuSub>
											</SidebarMenu>
										{/await}
									</AccordionContent>
								</AccordionItem>
							{/each}
						</Accordion>
					{:catch}
						<p class="text-destructive px-2 py-4 text-sm">Failed to load documents.</p>
					{/await}
				</SidebarGroupContent>
			</SidebarGroup>
		</SidebarContent>
		<SidebarRail />
	</Sidebar>

	<SidebarInset>
		<header class="flex h-12 items-center gap-2 border-b px-4">
			<SidebarTrigger />
			<Separator orientation="vertical" class="h-4" />
			<span class="text-muted-foreground text-sm">
				{#if filename}
					{filename}{#if pageIndex != null}&nbsp;/&nbsp;page {pageIndex + 1}{/if}
				{:else}
					Select a document
				{/if}
			</span>
		</header>
		<main class="flex-1 p-4">
			{@render children()}
		</main>
	</SidebarInset>
</SidebarProvider>
