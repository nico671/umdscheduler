<script lang="ts">
	import { onMount } from 'svelte';
	export let addedClasses: string[];
	export let showModal: boolean; // boolean
	let dialog: HTMLDialogElement; // HTMLDialogElement
	export let profName: string;
	let instructorType: string;
	let courses: string[];
	let reviews: any[];
	let averageRating: number | string;
	export let index: number;
	export let closeModal: (index: number) => void;
	export let reAddProfessor: (className: string) => void;

	// let loaded = false;
	// Check if all data is loaded
	// no check for reviews because reviews could be empty
	$: loaded = instructorType && courses && courses.length != 0 && averageRating;

	$: if (dialog && showModal) dialog.showModal();

	onMount(async () => {
		console.log(showModal);
		const url = new URL('https://planetterp.com/api/v1/professor');
		url.searchParams.append('name', profName);
		url.searchParams.append('reviews', 'true');

		fetch(url)
			.then((response) => response.json())
			.then((data) => {
				console.log(data);

				reviews = data.reviews;
				if (reviews.length == 0) {
					reviews = [];
				}
				averageRating = data.average_rating;
				if (averageRating == null) {
					averageRating = 'N/A';
				}
				instructorType = data.type;
				if (instructorType == 'Professor') {
					instructorType = 'Professor';
				} else if (instructorType == 'TA') {
					instructorType = 'TA';
				} else {
					instructorType = 'N/A';
				}
				courses = data.courses;
				if (courses.length == 0) {
					courses = [];
				}
			})
			.catch((error) => {
				console.log(error);
				dialog.close();
				return [];
			});
	});
</script>

<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
<!-- svelte-ignore a11y-click-events-have-key-events -->
<dialog
	bind:this={dialog}
	on:close={() => (showModal = false)}
	on:click|self={() => dialog.close()}
>
	{#if !loaded}
		<div class="loader"></div>
	{/if}
	{#if loaded}
		<div>
			<div class="modal-header">
				<h1>{profName}</h1>
				<button
					on:click={() => {
						closeModal(index);
						dialog.close();
					}}>Close</button
				>
				<button
					on:click={() => {
						reAddProfessor(profName);
						dialog.close();
					}}>Allow {instructorType.toLocaleLowerCase()}</button
				>
			</div>
		</div>
		<div>
			<h2>Average Rating: {averageRating}</h2>
			<h2>Reviews</h2>
			{#each reviews as review}
				{#if addedClasses.includes(review.course)}
					<div class="review-div">
						<h3>{review.course}</h3>
						<h4>{review.created}</h4>
						<p>Expected Grade: {review.expected_grade}</p>
						<p>Rating: {review.rating}</p>
						<p>{review.review}</p>
					</div>
				{/if}
			{/each}
		</div>
	{/if}
</dialog>

<style>
	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.modal-header h1 {
		margin: 0;
		flex-grow: 1;
	}

	.modal-header button {
		margin-left: 10px;
	}

	.review-div {
		border: 1px solid #a8a8a8;
		border-radius: 4px;
		padding: 10px;
		margin-top: 10px;
		flex-wrap: wrap;
		flex-direction: column;
	}

	dialog {
		max-width: 90%;
		border-radius: 0.2em;
		border: none;
		padding: 0;
		overflow: hidden; /* Add this line to handle overflow */
	}
	dialog > div {
		padding: 1em;
		overflow-y: auto; /* Add this line to enable vertical scrolling */
		max-height: 80vh; /* Add this line to limit the height of the content */
	}
	dialog::backdrop {
		background: rgba(0, 0, 0, 0.3);
	}
	dialog > div {
		padding: 1em;
		overflow-y: auto; /* Add this line to enable vertical scrolling */
		max-height: 80vh; /* Add this line to limit the height of the content */
	}
	dialog[open] {
		animation: zoom 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
	}
	@keyframes zoom {
		from {
			transform: scale(0.95);
		}
		to {
			transform: scale(1);
		}
	}
	dialog[open]::backdrop {
		animation: fade 0.2s ease-out;
	}
	@keyframes fade {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}
	button {
		background-color: #a8a8a8; /* Green */
		border: none;
		color: white;
		padding: 15px 32px;
		text-align: center;
		text-decoration: none;
		display: inline-block;
		font-size: 16px;
		margin: 4px 2px;
		cursor: pointer;
		border-radius: 4px;
	}

	button:hover {
		background-color: #585858;
	}

	/* p {
		margin: 0;
		color: #333333;
	}

	h2 {
		font-size: 1.5em;
		font-weight: bold;
	}

	h3 {
		font-size: 1.2em;
		font-weight: bold;
	}

	p {
		font-size: 1em;
		line-height: 1.5;
		margin-bottom: 0.5em;
	} */
</style>
