<script lang="ts">
	import { createEventDispatcher } from "svelte";
	import { onMount } from "svelte";

	export let colorMap: Map<string, string>;
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
			// Dispatch event to parent with additional parameter to show modal
			dispatch("add", { className: value, showModal: true });
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
	class="modal"
>
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<div class="modal-content" on:click|stopPropagation>
		<div class="modal-header">
			<h1>Add A Class</h1>
			<button class="close-btn" on:click={handleCancel}>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="24"
					height="24"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
				>
					<line x1="18" y1="6" x2="6" y2="18"></line>
					<line x1="6" y1="6" x2="18" y2="18"></line>
				</svg>
			</button>
		</div>

		<div id="search-column">
			<!-- svelte-ignore a11y-autofocus -->
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
	.modal {
		max-width: 600px;
		width: 90%;
		border-radius: 12px;
		border: none;
		padding: 0;
		box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
		overflow: hidden;
	}

	.modal-content {
		padding: 24px;
		max-height: 80vh;
		overflow-y: auto;
	}

	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 24px;
		border-bottom: 1px solid #eee;
		padding-bottom: 16px;
	}

	.modal-header h1 {
		margin: 0;
		font-size: 1.8rem;
		color: #e21833;
	}

	.close-btn {
		background: transparent;
		border: none;
		cursor: pointer;
		padding: 6px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 50%;
		transition: background-color 0.2s;
	}

	.close-btn:hover {
		background-color: rgba(0, 0, 0, 0.05);
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
		background: rgba(0, 0, 0, 0.5);
		backdrop-filter: blur(2px);
	}

	dialog[open] {
		animation: zoom 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
	}

	@keyframes zoom {
		from {
			transform: scale(0.95);
			opacity: 0;
		}
		to {
			transform: scale(1);
			opacity: 1;
		}
	}
</style>
