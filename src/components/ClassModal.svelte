<script lang="ts">
	import { onMount } from 'svelte';

	export let showModal: boolean; // boolean
	export let className: string; // string
	export let prohibitedProfessors: string[]; // string[]
	let dialog: HTMLDialogElement; // HTMLDialogElement
	let courseTitle: string;
	let courseProfs: Map<String, any> = new Map<string, any>();
	let averageGPA: string;
	let courseDescription: string;
	let courseCredits: number;
	let htmlContent = '';
	export let index: number;
	export let showProfessorModals: boolean[] = [];
	export let closeModal: (index: number) => void;
	export let removeClasses: (className: string) => void;
	export let prohibitProf: (prof: string) => void;

	$: loaded = courseProfs.size && courseTitle && courseCredits && averageGPA && htmlContent;

	$: if (dialog && showModal) dialog.showModal();

	onMount(async () => {
		const url = new URL('https://planetterp.com/api/v1/course');

		url.searchParams.append('name', className);

		fetch(url)
			.then((response) => response.json())
			.then((data) => {
				courseTitle = data.title;
				if (data.average_gpa == null) {
					averageGPA = 'N/A';
				} else {
					averageGPA = data.average_gpa;
				}

				const parser = new DOMParser();
				const htmlDoc = parser.parseFromString(data.description, 'text/html');

				htmlContent = htmlDoc.body.innerHTML;

				// courseDescription = htmlDoc.body.textContent || '';
				courseCredits = data.credits;
			})
			.catch((error) => {
				console.log(error);
				return [];
			});
		var uniqueProfs = [] as string[];
		const url2 = new URL(`https://api.umd.io/v1/courses/${className}/sections`);
		url2.searchParams.append('semester', '202501');
		fetch(url2, {
			method: 'GET'
		})
			.then((response) => response.json())
			.then((data) => {
				// console.log(data);
				data.forEach((element: any) => {
					const instructors = element.instructors;
					if (instructors != null) {
						instructors.forEach((prof: string) => {
							if (!uniqueProfs.includes(prof)) {
								uniqueProfs.push(prof);
							}
						});
					}
				});
				// console.log(uniqueProfs);
			})
			.catch((error) => {
				console.log(error);
				return [];
			})
			.then(() => {
				uniqueProfs.forEach((element: string) => {
					const url = new URL('https://planetterp.com/api/v1/professor');
					url.searchParams.append('name', element);
					fetch(url)
						.then((response) => response.json())
						.then((data) => {
							courseProfs.set(element, data);
							courseProfs = new Map(
								[...courseProfs.entries()].sort((a, b) => b[1].average_rating - a[1].average_rating)
							);
						})
						.catch((error) => {
							console.log(error);
							// return [];
						});
				});
			});

		// console.log(prohibitedProfessors);
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
				<h1>{className}</h1>
				<button
					on:click={() => {
						closeModal(index);
						dialog.close();
					}}>Close</button
				>
				<button
					on:click={() => {
						removeClasses(className);
						dialog.close();
					}}>Remove {className}</button
				>
			</div>
			<h3>{courseTitle}</h3>
			<div id="description">
				{@html htmlContent}
			</div>
			<p><b>Credits</b>: {courseCredits}</p>
			<p><b>Average GPA</b>: {averageGPA}</p>
			<div class="available-professors">
				<h2 style="margin-bottom:2vh">Available Professors</h2>
				{#each Array.from(courseProfs.keys()) as prof}
					{#if !prohibitedProfessors.includes(prof.toString())}
						<div class="prof-planet-terp">
							<div class="prof-info">
								<h3 style="margin-right:2vh">{prof}</h3>
								<p style="margin-right:2vh">
									{parseFloat(courseProfs.get(prof).average_rating).toFixed(2)} Average Rating
								</p>
								<a
									href="https://planetterp.com/professor/{courseProfs.get(prof).slug}"
									target="_blank">Planet Terp Page</a
								>
							</div>

							<button
								class="button prohibit"
								on:click={() => {
									if (!prohibitedProfessors.includes(prof.toString()) && courseProfs.size > 1) {
										prohibitProf(prof.toString());
										console.log(prof);
										showProfessorModals[Array.from(courseProfs.keys()).indexOf(prof)] = true;
										showProfessorModals = [...showProfessorModals];
										showModal = false;
										// dialog.close();
									}
								}}>Remove</button
							>
						</div>
					{/if}
				{/each}
			</div>
		</div>
	{/if}
</dialog>

<style>
	.prof-info {
		display: flex;
		flex-direction: column;
	}

	.button.prohibit {
		justify-self: center;
		background-color: rgb(167, 0, 0);
		width: fit-content;
		height: fit-content;
		font-size: 12px;
		padding: 0.5vh;
		margin-right: 1vh;
	}

	.button.prohibit:hover {
		background-color: rgb(255, 0, 0);
	}

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

	.prof-planet-terp {
		display: flex;
		flex-direction: row;
		margin-bottom: 1vh;
		background-color: rgba(177, 177, 177, 0.25);
		border: 2px solid rgba(177, 177, 177, 0.808);
		border-radius: 15px;
		padding: 1vh;
		width: max-content;
	}
	dialog {
		max-width: 50%;
		border-radius: 0.2em;
		border: none;
		padding: 0;
	}
	dialog::backdrop {
		background: rgba(0, 0, 0, 0.3);
	}
	dialog > div {
		padding: 1em;
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
	h2,
	h3,
	p {
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
	}

	/* Styling for the available professors section */
	.available-professors {
		margin-top: 1em;
	}

	.available-professors a {
		margin-top: 0.5em;
	}

	.available-professors p {
		margin-bottom: 0.2em;
	}

	.loader {
		border: 16px solid #f3f3f3; /* Light grey */
		border-top: 16px solid #3498db; /* Blue */
		border-radius: 50%;
		width: 120px;
		height: 120px;
		animation: spin 2s linear infinite;
	}

	@keyframes spin {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
	}
</style>
