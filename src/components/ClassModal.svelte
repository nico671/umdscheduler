<script lang="ts">
	import { onMount, createEventDispatcher } from "svelte";

	export let className: string;
	export let showModal: boolean;
	export let prohibitedProfessors: string[] = [];
	export let showProfessorModals: boolean[] = [];
	export let index: number;
	export let closeModal: (index: number) => void;
	export let removeClasses: (className: string) => void;
	export let prohibitProf: (prof: string) => void;
	export let reAddProfessor: (prof: string) => void;

	// Create event dispatcher for custom events
	const dispatch = createEventDispatcher();

	let dialog: HTMLDialogElement;
	let courseDescription: string = "";
	let courseTitle: string = "";
	let instructors: string[] = [];
	let sections: any[] = [];
	let isLoading = true;

	// Show modal when the showModal prop is true
	$: if (dialog && showModal) dialog.showModal();

	onMount(async () => {
		isLoading = true;
		await fetchCourseData();
	});

	async function fetchCourseData() {
		try {
			// Fetch course info
			const url = new URL(`https://api.umd.io/v1/courses/${className}`);
			const response = await fetch(url);
			const data = await response.json();

			if (Array.isArray(data) && data.length > 0) {
				const course = data[0];
				courseDescription =
					course.description || "No description available";
				courseTitle = course.name || className;

				// Get sections for this course
				const sectionsUrl = new URL(
					`https://api.umd.io/v1/courses/${className}/sections`,
				);
				const sectionsResponse = await fetch(sectionsUrl);
				const sectionsData = await sectionsResponse.json();

				// Extract instructors from sections
				const instructorSet = new Set<string>();
				sections = sectionsData || [];

				sections.forEach((section: any) => {
					if (Array.isArray(section.instructors)) {
						section.instructors.forEach((instructor: string) => {
							if (
								instructor &&
								instructor !== "Instructor: TBA"
							) {
								instructorSet.add(instructor);
							}
						});
					}
				});

				instructors = Array.from(instructorSet);
			}
		} catch (error) {
			console.error("Error fetching course data:", error);
			courseDescription = "Failed to load course details";
		} finally {
			isLoading = false;
		}
	}

	// This is a completely new approach that doesn't prohibit professors
	function viewProfessorDetails(profName: string) {
		// Tell the parent we want to view this professor
		dispatch("viewProfessor", { professorName: profName });

		// Close this modal
		dialog.close();
	}

	// Separate function to handle prohibit/allow toggle
	function toggleProhibition(profName: string) {
		if (prohibitedProfessors.includes(profName)) {
			reAddProfessor(profName);
		} else {
			prohibitProf(profName);
		}
	}
</script>

<dialog
	bind:this={dialog}
	on:close={() => (showModal = false)}
	on:click|self={() => closeModal(index)}
	class="modal"
>
	<div class="modal-content" on:click|stopPropagation>
		{#if isLoading}
			<div class="loading">
				<div class="spinner"></div>
				<p>Loading course information...</p>
			</div>
		{:else}
			<div class="modal-header">
				<div>
					<h1>{className}</h1>
					<h2>{courseTitle}</h2>
				</div>
				<div class="button-group">
					<button
						class="action-btn danger"
						on:click={() => {
							removeClasses(className);
							dialog.close();
						}}
					>
						Remove Class
					</button>
					<button
						class="close-btn"
						on:click={() => closeModal(index)}
					>
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
			</div>

			<div class="course-description">
				<h3>Description</h3>
				<p>{courseDescription}</p>
			</div>

			<div class="instructors-section">
				<h3>Instructors</h3>
				<div class="instructors-list">
					{#if instructors.length > 0}
						{#each instructors as instructor}
							<div class="instructor-item">
								<!-- Left side: Name and Details button -->
								<div class="instructor-info">
									<div class="instructor-name">
										{instructor}
									</div>
									<button
										class="view-details-btn"
										on:click|stopPropagation={() =>
											viewProfessorDetails(instructor)}
									>
										View Details
									</button>
								</div>

								<!-- Right side: Prohibit/Allow button -->
								<button
									class="instructor-action {prohibitedProfessors.includes(
										instructor,
									)
										? 'prohibited'
										: ''}"
									on:click|stopPropagation={() =>
										toggleProhibition(instructor)}
								>
									{#if prohibitedProfessors.includes(instructor)}
										Allow
									{:else}
										Prohibit
									{/if}
								</button>
							</div>
						{/each}
					{:else}
						<p>No instructors available for this course.</p>
					{/if}
				</div>
			</div>
		{/if}
	</div>
</dialog>

<style>
	/* Remove specific font imports - now handled by global fonts.css */

	/* Apply font to all elements */
	:global(*) {
		font-family: "Gotham", "Helvetica Neue", Arial, sans-serif;
	}

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
		max-height: 85vh;
		overflow-y: auto;
	}

	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 24px;
		border-bottom: 1px solid #eee;
		padding-bottom: 16px;
	}

	.modal-header h1 {
		margin: 0;
		font-size: 1.8rem;
		color: #e21833;
	}

	.modal-header h2 {
		margin: 4px 0 0 0;
		font-size: 1.2rem;
		color: #333;
	}

	.button-group {
		display: flex;
		gap: 8px;
		align-items: center;
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

	.action-btn {
		background-color: #e21833;
		border: none;
		color: white;
		padding: 8px 16px;
		border-radius: 6px;
		font-weight: 500;
		cursor: pointer;
		transition: background-color 0.2s;
	}

	.action-btn:hover {
		background-color: #c91528;
	}

	.action-btn.danger {
		background-color: #e21833; /* UMD red for danger */
	}

	h3 {
		margin: 0 0 12px 0;
		font-size: 1.1rem;
		color: #333;
	}

	.course-description {
		margin-bottom: 24px;
	}

	.course-description p {
		line-height: 1.5;
		color: #444;
	}

	.instructors-section {
		margin-top: 24px;
	}

	.instructors-list {
		display: flex;
		flex-direction: column;
		gap: 10px;
	}

	/* Updated instructor item style for better separation */
	.instructor-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 12px 16px;
		border: 1px solid #eee;
		border-radius: 8px;
		background-color: white;
		gap: 12px; /* Add gap between elements */
		position: static; /* Ensure it doesn't create a positioning context */
		cursor: default; /* Explicitly non-interactive */
	}

	.instructor-info {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		flex: 1;
	}

	.instructor-name {
		font-weight: 500;
		font-size: 0.9rem;
		margin-bottom: 8px; /* Increase space between name and button */
		pointer-events: none; /* Completely non-interactive */
	}

	/* Make view details button more distinct */
	.view-details-btn {
		background-color: transparent;
		border: 1px solid #e21833;
		color: #e21833;
		font-size: 0.8rem;
		padding: 4px 8px;
		border-radius: 4px;
		cursor: pointer;
		display: inline-block; /* Make it a block element */
		width: auto;
		text-decoration: none; /* Remove underline */
		margin: 0;
	}

	.view-details-btn:hover {
		background-color: rgba(226, 24, 51, 0.05);
	}

	/* Make prohibit/allow button very distinct */
	.instructor-action {
		background: #f0f0f0;
		border: 1px solid #ddd; /* Add border for clarity */
		padding: 8px 12px;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.8rem;
		white-space: nowrap;
		font-weight: 500;
		min-width: 90px;
		width: 90px; /* Fixed width rather than percentage */
		text-align: center;
		position: relative; /* Create its own stacking context */
		z-index: 2; /* Ensure it's above other elements */
		flex-shrink: 0; /* Prevent shrinking */
	}

	.instructor-action:hover {
		background-color: #e0e0e0;
	}

	.instructor-action.prohibited {
		background-color: #e8f4e8; /* Light green background */
		color: #2a602a; /* Dark green text */
		cursor: pointer; /* Keep the pointer cursor */
		border: 1px solid #c8e6c9; /* Light green border */
	}

	.instructor-action.prohibited:hover {
		background-color: #d5ebd5; /* Slightly darker green on hover */
	}

	/* Loading indicator */
	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 40px 0;
	}

	.spinner {
		width: 40px;
		height: 40px;
		border: 4px solid #f3f3f3;
		border-top: 4px solid #e21833;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin-bottom: 16px;
	}

	@keyframes spin {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
	}

	/* Modal animations */
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
