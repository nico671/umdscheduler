<script lang="ts">
	import { onMount } from "svelte";
	export let addedClasses: string[];
	export let showModal: boolean; // boolean
	let dialog: HTMLDialogElement; // HTMLDialogElement
	export let profName: string;
	let instructorType: string = "Instructor";
	let courses: string[] = [];
	let reviews: any[] = [];
	let averageRating: number | string = "N/A";
	export let index: number;
	export let closeModal: (index: number) => void;
	export let reAddProfessor: (className: string) => void;
	let isLoading: boolean = true;

	// Check if all data is loaded
	$: loaded = instructorType && courses && !isLoading;

	$: if (dialog && showModal) dialog.showModal();

	onMount(async () => {
		console.log(showModal);
		const url = new URL("https://planetterp.com/api/v1/professor");
		url.searchParams.append("name", profName);
		url.searchParams.append("reviews", "true");

		try {
			const response = await fetch(url);
			const data = await response.json();
			console.log(data);

			reviews = data.reviews || [];
			averageRating = data.average_rating || "N/A";

			// Simplified instructor type handling
			instructorType = data.type || "Instructor";
			courses = data.courses || [];

			isLoading = false;
		} catch (error) {
			console.error("Error fetching professor data:", error);
			isLoading = false;
			if (dialog) dialog.close();
		}
	});
</script>

<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
<!-- svelte-ignore a11y-click-events-have-key-events -->
<dialog
	bind:this={dialog}
	on:close={() => (showModal = false)}
	on:click|self={() => dialog.close()}
	class="prof-modal"
>
	<div class="modal-content">
		{#if isLoading}
			<div class="loader-container">
				<div class="loader"></div>
			</div>
		{:else}
			<div class="modal-header">
				<h1>{profName}</h1>
				<div class="button-group">
					<button
						class="allow-btn"
						on:click={() => {
							reAddProfessor(profName);
							dialog.close();
						}}
					>
						Allow {instructorType}
					</button>
					<button
						class="close-btn"
						on:click={() => {
							closeModal(index);
							dialog.close();
						}}
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

			<div class="rating-section">
				<div class="rating-badge">
					<span class="rating-value">{averageRating}</span>
					<span class="rating-label">Average Rating</span>
				</div>
			</div>

			<h2>Courses</h2>
			<div class="courses-list">
				{#if courses.length > 0}
					{#each courses as course}
						<span class="course-chip">{course}</span>
					{/each}
				{:else}
					<p>No courses available</p>
				{/if}
			</div>

			<h2>Reviews</h2>
			{#if reviews.length > 0}
				<div class="reviews-container">
					{#each reviews as review}
						{#if addedClasses.includes(review.course)}
							<div class="review-card">
								<div class="review-header">
									<span class="review-course"
										>{review.course}</span
									>
									<span class="review-date"
										>{review.created}</span
									>
								</div>
								<div class="review-grades">
									<span class="grade-badge"
										>Grade: {review.expected_grade ||
											"N/A"}</span
									>
									<span class="rating-badge-small"
										>Rating: {review.rating || "N/A"}</span
									>
								</div>
								<p class="review-text">{review.review}</p>
							</div>
						{/if}
					{/each}
				</div>
			{:else}
				<p>No reviews available for your selected courses.</p>
			{/if}
		{/if}
	</div>
</dialog>

<style>
	.prof-modal {
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
		color: #333;
		flex-grow: 1;
	}

	.button-group {
		display: flex;
		gap: 8px;
	}

	.close-btn {
		background: transparent;
		border: none;
		color: #666;
		cursor: pointer;
		padding: 6px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 50%;
		transition:
			background-color 0.2s,
			color 0.2s;
	}

	.close-btn:hover {
		background-color: rgba(0, 0, 0, 0.05);
		color: #333;
	}

	.allow-btn {
		background-color: #e21833;
		border: none;
		color: white;
		padding: 8px 16px;
		border-radius: 6px;
		font-weight: 500;
		cursor: pointer;
		transition: background-color 0.2s;
	}

	.allow-btn:hover {
		background-color: #c91528;
	}

	.rating-section {
		display: flex;
		justify-content: center;
		margin: 20px 0;
	}

	.rating-badge {
		display: flex;
		flex-direction: column;
		align-items: center;
		background-color: #f8f8f8;
		border-radius: 12px;
		padding: 16px 30px;
		box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
	}

	.rating-value {
		font-size: 2.5rem;
		font-weight: bold;
		color: #e21833;
	}

	.rating-label {
		font-size: 0.9rem;
		color: #666;
		margin-top: 4px;
	}

	.reviews-container {
		display: flex;
		flex-direction: column;
		gap: 16px;
		margin-top: 16px;
	}

	.review-card {
		border: 1px solid #eee;
		border-radius: 8px;
		padding: 16px;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
		transition:
			transform 0.2s,
			box-shadow 0.2s;
	}

	.review-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 3px 6px rgba(0, 0, 0, 0.1);
	}

	.review-header {
		display: flex;
		justify-content: space-between;
		margin-bottom: 12px;
		align-items: center;
	}

	.review-course {
		font-weight: bold;
		color: #333;
	}

	.review-date {
		color: #888;
		font-size: 0.85rem;
	}

	.review-grades {
		display: flex;
		gap: 10px;
		margin-bottom: 12px;
		flex-wrap: wrap;
	}

	.grade-badge,
	.rating-badge-small {
		background-color: #f0f0f0;
		padding: 4px 8px;
		border-radius: 4px;
		font-size: 0.85rem;
	}

	.review-text {
		color: #333;
		line-height: 1.5;
		margin: 0;
	}

	.courses-list {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		margin-bottom: 24px;
	}

	.course-chip {
		background-color: #f0f0f0;
		padding: 6px 12px;
		border-radius: 16px;
		font-size: 0.9rem;
	}

	h2 {
		color: #333;
		margin-top: 24px;
		margin-bottom: 16px;
		font-size: 1.3rem;
	}

	/* Loader styling */
	.loader-container {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 200px;
	}

	.loader {
		width: 48px;
		height: 48px;
		border: 5px solid #f3f3f3;
		border-top: 5px solid #e21833;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
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
</style>
