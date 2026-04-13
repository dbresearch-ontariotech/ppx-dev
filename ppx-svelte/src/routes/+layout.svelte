<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
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
	import { appState, fetchDocInfo, type TokenLevel, TOKEN_LEVEL_COLORS } from '$lib/appstate.svelte';
	import StatusBadge from '$lib/components/StatusBadge.svelte';
	import { Checkbox } from '$lib/components/ui/checkbox';

	let { children } = $props();
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
					{#await appState.documents}
						<div class="text-muted-foreground flex items-center gap-2 px-2 py-4 text-sm">
							<Spinner class="size-4" />
							Loading...
						</div>
					{:then docs}
						<Accordion type="multiple" value={appState.filename ? [appState.filename] : []}>
							{#each docs as doc (doc)}
								<AccordionItem value={doc} class="border-none">
									<SidebarMenu>
										<SidebarMenuItem>
											<AccordionTrigger class="py-0 hover:no-underline">
												<SidebarMenuButton isActive={appState.filename === doc}>
													{#snippet child({ props })}
														<a href="/{doc}/" {...props}>{doc}</a>
													{/snippet}
												</SidebarMenuButton>
											</AccordionTrigger>
										</SidebarMenuItem>
									</SidebarMenu>
									<AccordionContent class="pb-0">
										{#await fetchDocInfo(doc)}
											<div
												class="text-muted-foreground flex items-center gap-2 px-4 py-2 text-xs"
											>
												<Spinner class="size-3" />
											</div>
										{:then info}
											<SidebarMenu>
												<SidebarMenuSub>
													{#each { length: info.pages } as _, i (i)}
														<SidebarMenuSubItem>
															<SidebarMenuSubButton
																href="/{doc}/{i}/"
																isActive={appState.filename === doc &&
																	appState.pageIndex === i}
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

	<SidebarInset class="h-screen flex flex-col">
		<header class="flex h-12 shrink-0 items-center gap-2 border-b px-4">
			<SidebarTrigger />
			<Separator orientation="vertical" class="h-4" />
			<span class="text-muted-foreground truncate text-sm">
				{#if appState.filename}
					{appState.filename}{#if appState.pageIndex != null}&nbsp;/&nbsp;page {appState.pageIndex + 1}{/if}
				{:else}
					Select a document
				{/if}
			</span>
			{#if appState.pageIndex != null}
				<div class="ml-auto flex items-center gap-4">
					<div class="flex items-center gap-3">
						{#each (['block', 'line', 'word'] as TokenLevel[]) as level (level)}
							<label
								class="flex cursor-pointer items-center gap-1.5 rounded px-1.5 py-0.5"
								style:border="1.5px solid {TOKEN_LEVEL_COLORS[level]}"
							>
								<Checkbox
									checked={appState.showVisualTokens.get(level) ?? false}
									onCheckedChange={(v) => appState.showVisualTokens.set(level, !!v)}
								/>
								<span class="text-sm capitalize">{level}</span>
							</label>
						{/each}
					</div>
					<Separator orientation="vertical" class="h-4" />
					<div class="flex items-center gap-2">
						<StatusBadge promise={appState.markdownAst} label="MD" />
						<StatusBadge promise={appState.layout} label="Layout" />
						<StatusBadge promise={appState.alignment} label="Align" />
					</div>
				</div>
			{/if}
		</header>
		<main class="min-h-0 flex-1">
			{@render children()}
		</main>
	</SidebarInset>
</SidebarProvider>
