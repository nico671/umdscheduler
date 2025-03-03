<script lang="ts">
	import { createEventDispatcher } from "svelte";
	import { onMount } from "svelte";

	export let colorMap: Map<string, string> = new Map();
	export let showAddClassModal: boolean;
	export let availableClasses: string[] = [];
	export let addedClasses: string[] = [];
	export let showModals: boolean[] = [];

	const dispatch = createEventDispatcher();
	let dialog: HTMLDialogElement;
	let classInput = "";

	// Function to generate a random color
	function getRandomColor() {
		return `hsla(${~~(360 * Math.random())}, 70%,  72%, 0.8)`;
	}

	function addClass(value: string) {
		if (!addedClasses.includes(value)) {
			// Dispatch event to parent
			dispatch("add", value);
		}
		classInput = "";
	}

	function handleCancel() {
		dispatch("close");
		dialog.close();
	}

	$: if (dialog && showAddClassModal) dialog.showModal();

	$: filteredClasses = availableClasses
		.filter((x) => x.includes(classInput.toUpperCase()))
		.slice(0, 50); // Limit to prevent performance issues
</script>

<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
<!-- svelte-ignore a11y-click-events-have-key-events -->
<dialog
	bind:this={dialog}
	on:close={() => dispatch("close")}
	on:click|self={handleCancel}
	class="class-modal"
>
	<div class="modal-content" on:click|stopPropagation>
		<header>
			<h1>Add A Class</h1>
			<button class="header-button" on:click={handleCancel}>Cancel</button
			>
		</header>

		<div id="search-column">
			<input
				class="class-search-bar"
				bind:value={classInput}
				placeholder="Search for classes (e.g. CMSC131)"
				autofocus
			/>
			{#if classInput.length}
				<div class="filtered-class-list">
					{#if filteredClasses.length === 0}
						<div class="no-results">No matches found</div>
					{:else}
						{#each filteredClasses as value}
							<button
								class="filtered-class-list-item"
								on:click={() => addClass(value)}
							>
								{value}
							</button>
						{/each}
					{/if}
				</div>
			{/if}
		</div>
	</div>
</dialog>

<style>
	.class-modal {
		width: 500px;
		max-width: 95vw;
		height: auto;
		max-height: 80vh;
		padding: 0;
		border-radius: 12px;
		border: none;
		box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
		overflow: hidden;
	}

	.modal-content {
		padding: 24px;
		display: flex;
		flex-direction: column;
		height: 100%;
	}

	header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;
		border-bottom: 1px solid #e9e9e9;
		padding-bottom: 12px;
	}

	h1 {
		font-size: clamp(24px, 5vw, 36px);
		margin: 0;
	}

	.header-button {
		background-color: rgba(51, 51, 51, 0.1);
		border-radius: 8px;
		border: none;
		color: #333333;
		cursor: pointer;
		font-size: 16px;
		font-weight: 500;
		padding: 8px 16px;
		transition: all 200ms;
	}

	.header-button:hover {
		background-color: rgba(51, 51, 51, 0.2);
	}

	#search-column {
		display: flex;
		flex-direction: column;
		gap: 12px;
		flex-grow: 1;
	}

	.class-search-bar {
		height: 50px;
		font-size: 18px;
		border: 2px solid #646464b2;
		padding: 8px 16px;
		border-radius: 25px;
		background-color: #f8f8f8;
		width: 100%;
		box-sizing: border-box;
	}

	.class-search-bar:focus {
		outline: none;
		border-color: var(--umd-red);
		background-color: white;
	}

	.filtered-class-list {
		display: flex;
		flex-direction: column;
		width: 100%;
		max-height: 400px;
		overflow-y: auto;
		border: 1px solid #e9e9e9;
		border-radius: 8px;
	}

	.filtered-class-list-item {
		padding: 12px 16px;
		text-align: left;
		background-color: white;
		border: none;
		border-bottom: 1px solid #f0f0f0;
		font-size: 16px;
		color: #333;
		cursor: pointer;
		transition: background-color 0.2s;
	}

	.filtered-class-list-item:hover {
		background-color: #f6f6f6;
	}

	.filtered-class-list-item:last-child {
		border-bottom: none;
	}

	.no-results {
		padding: 16px;
		text-align: center;
		color: #666;
	}

	dialog::backdrop {
		background-color: rgba(0, 0, 0, 0.5);
		backdrop-filter: blur(2px);
	}
</style>
