<script lang="ts">
	import { onMount } from 'svelte';

	export let colorMap: Map<string, string> = new Map();
	export let showAddClassModal: boolean; // boolean
	export let availableClasses: string[]; // string[]
	export let addedClasses: string[]; // string[]
	export let showModals: boolean[]; // boolean[]

	let dialog: HTMLDialogElement; // HTMLDialogElement
	let classInput = '';
	// Function to generate a random color
	function getRandomColor() {
		return `hsla(${~~(360 * Math.random())}, 70%,  72%, 0.8)`;
	}

	function addClass(value: string) {
		// if (!prohibitedProfessors.has(value)) {
		// 	prohibitedProfessors.set(value, []);
		// }
		addedClasses.push(value);
		colorMap.set(value, getRandomColor());
		addedClasses = [...new Set(addedClasses)];
		availableClasses = availableClasses.filter((x) => x !== value);
		const index = addedClasses.indexOf(value);
		showModals[index] = true;
		classInput = '';
		showAddClassModal = false;
		dialog.close();

		console.log('Added Classes:', addedClasses);

		// force reload
		addedClasses = [...addedClasses];
	}

	$: if (dialog && showAddClassModal) dialog.showModal();

	$: filteredClasses = availableClasses.filter((x) => x.includes(classInput.toUpperCase()));
</script>

<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
<!-- svelte-ignore a11y-click-events-have-key-events -->
<dialog
	bind:this={dialog}
	on:close={() => (showAddClassModal = false)}
	on:click|self={() => dialog.close()}
>
	<header>
		<h1>Add A Class</h1>
		<button
			class="header-button"
			on:click={() => {
				// removeClasses(className);
				dialog.close();
			}}>Cancel</button
		>
	</header>

	<div id="search-column">
		<input class="class-search-bar" bind:value={classInput} placeholder="Add Classes" />
		{#if classInput.length}
			<div class="filtered-class-list">
				{#each filteredClasses as value}
					<button class="filtered-class-list-item" on:click={() => addClass(value)}>
						{value}
					</button>
				{/each}
			</div>
		{/if}
	</div>
</dialog>

<style>
	header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1vh;
		/* background-color: #f6f6f6; */
		border-bottom: 1px solid #e9e9e9;
	}

	.filtered-class-list-item {
		padding-left: 1vh;
		text-align: center;
		justify-self: center;
		height: 4vh;
		margin-top: -1px; /* Prevent double borders */
		background-color: #f6f6f6; /* Grey background color */
		text-decoration: none; /* Remove default text underline */
		font-size: 16px; /* Increase the font-size */
		white-space: nowrap;
		color: black; /* Add a black text color */
		/* display: block; Make it into a block element to fill the whole list */
		width: inherit;

		border: 0px;
	}

	.filtered-class-list-item:hover {
		background-color: #e9e9e9; /* Add a darker background color on hover */
		height: 6vh;
	}

	.filtered-class-list {
		display: grid;
		grid-template-columns: repeat(1, minmax(10vh, 1fr));
		width: 100%;
		/* max-height: 10.5vh; */
		height: fit-content; /* Set to your desired height */
		/* max-height: 60%; */
		overflow-y: auto;
		scrollbar-width: none; /* Hide scrollbar for Firefox */
		-ms-overflow-style: none; /* Hide scrollbar for IE and Edge */
		&::-webkit-scrollbar {
			width: 0; /* Hide scrollbar for Chrome, Safari, and Opera */
		}
		overflow-x: hidden;
	}

	input {
		width: 100%;
	}

	h1 {
		font-size: 48px;
	}

	.header-button {
		height: 5vh;
		background-color: rgba(51, 51, 51, 0.1);
		border-radius: 8px;
		border-width: 0;
		color: #333333;
		cursor: pointer;
		display: inline-block;
		font-family: 'Haas Grot Text R Web', 'Helvetica Neue', Helvetica, Arial, sans-serif;
		font-size: 18px;
		font-weight: 500;
		line-height: 20px;
		list-style: none;
		margin: 0;
		padding: 10px 12px;
		text-align: center;
		transition: all 200ms;
		vertical-align: baseline;
		white-space: nowrap;
		user-select: none;
		-webkit-user-select: none;
		touch-action: manipulation;
	}

	.class-search-bar {
		height: 5vh;
		max-height: 5vh;
		font-size: 20px; /* Increase font-size */
		border: 2px solid #646464b2; /* Add a grey border */
		padding: 10px; /* Adjust padding as needed */

		justify-content: start;
		border-radius: 25px;
		background-color: #ededed;
		box-sizing: border-box;
	}

	#search-column {
		display: flex;
		flex-direction: column;
		max-height: 65vh;
		margin-right: 1vw;
		/* overflow-y: auto; */
	}

	dialog:not([open]) {
		display: none;
	}

	dialog {
		width: 35vw;
		height: 50vh;
		/* padding: 10px; */
		/* box-sizing: border-box; */
		display: flex;
		flex-direction: column;
		/* justify-content: space-between; */
		overflow: hidden;
	}
</style>
