<script lang="ts">
	import { onMount, onDestroy } from "svelte";
	import ClassModal from "../components/ClassModal.svelte";
	import AddClassModal from "../components/AddClassModal.svelte";
	import TimeSelectionModal from "../components/TimeSelectionModal.svelte";
	import ProfessorModal from "../components/ProfessorModal.svelte";
	import ScheduleView from "../components/ScheduleView.svelte";
	import SemesterSelector from "../components/SemesterSelector.svelte";
	import "../styles/page.css";
	import "./styles/page-styles.css";
	import "../styles/global.css"; // Import global styles

	// Import all logic from the separate file
	import * as logic from "./page-logic";
	import {
		availableClasses,
		addedClasses,
		prohibitedTimes,
		prohibitedProfessors,
		colorMap,
		showTimeSelectionModal,
		showAddClassModal,
		generatingSchedules,
		currentAmountLoaded,
		showClassModals,
		showProfessorModals,
		schedules,
		sortOption,
		error,
		viewProfessorInfo,
		generatedSchedules,
		addTimeRestriction,
		addMultipleTimeRestrictions,
		availableSemesters,
		currentSemester,
		fetchSemesters,
	} from "./page-logic";

	// Reactive statements to manage state
	$: sortedSchedules = logic.sortSchedules($schedules);

	// Assign colors to added classes when they change
	$: {
		$addedClasses.forEach((className, index) => {
			if (!$colorMap.has(className)) {
				$colorMap.set(className, logic.generateColor(index));
			}
		});
	}

	// Handle semester change to reload classes
	function handleSemesterChange() {
		// Clear current schedules and classes when semester changes
		$schedules = [];
		$generatedSchedules = [];
		$error = null;

		// Clear added classes when semester changes to prevent conflicts
		$addedClasses = [];
		$showClassModals = [];

		// Refresh available classes for the new semester
		fetchAvailableClasses($currentSemester);
	}

	// Function to fetch available classes with semester parameter
	async function fetchAvailableClasses(semester: string) {
		try {
			const url = new URL("https://api.umd.io/v1/courses/list");
			url.searchParams.set("sort", "course_id,-credits");
			url.searchParams.set("semester", semester);

			console.log(
				`Fetching available classes for semester: ${semester} (${logic.formatSemester(semester)})`,
			);

			const response = await fetch(url);
			const data = await response.json();
			$availableClasses = data.map(
				(item: { course_id: string }) => item.course_id,
			);
		} catch (err) {
			$error =
				err instanceof Error ? err.message : "Failed to fetch classes";
			console.error("Error fetching classes:", err);
		}
	}

	onMount(async () => {
		// Fetch list of available semesters
		await fetchSemesters();

		// Initial fetch of available classes using current semester
		if ($currentSemester) {
			fetchAvailableClasses($currentSemester);
		}

		// Initialize class-professor tracking
		$addedClasses.forEach((className) => {
			logic.fetchClassDetails(className, $currentSemester);
		});
	});
</script>

<div class="app-container">
	<header class="app-header">
		<div class="header-content">
			<div class="header-left">
				<h1 class="app-title">UMD Scheduler</h1>
				<SemesterSelector onChange={handleSemesterChange} />
			</div>
			<div class="header-actions">
				<button
					class="btn btn-outline"
					on:click={() => ($showTimeSelectionModal = true)}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="16"
						height="16"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
					>
						<circle cx="12" cy="12" r="10"></circle>
						<polyline points="12 6 12 12 16 14"></polyline>
					</svg>
					Add Time Restriction
				</button>
				<button
					class="btn btn-outline"
					on:click={() => ($showAddClassModal = true)}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="16"
						height="16"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
					>
						<path d="M12 5v14M5 12h14"></path>
					</svg>
					Add Class
				</button>
				<button
					class="btn btn-primary"
					on:click={logic.generateSchedules}
					disabled={$generatingSchedules}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="16"
						height="16"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
					>
						<path d="M3 6l9 6 9-6M3 12l9 6 9-6"></path>
					</svg>
					{$generatingSchedules
						? "Generating..."
						: "Generate Schedules"}
				</button>
			</div>
		</div>
	</header>

	<main class="app-main">
		<div class="restrictions-container">
			<!-- Class Selection -->
			<div class="restriction-box">
				<h2 class="restriction-title">Selected Classes</h2>
				<div class="restriction-items">
					{#each $addedClasses as className, i}
						<button
							class="restriction-button"
							on:click={() => {
								$showClassModals[i] = true;
								$showClassModals = [...$showClassModals];
							}}
							style="background-color: {$colorMap.get(
								className,
							) || '#f5f5f5'}; 
								   color: {$colorMap.get(className) ? '#333' : '#666'};
								   border-color: {$colorMap.get(className)
								? logic.shade(
										$colorMap.get(className) ?? '#646464',
										20,
									)
								: '#e0e0e0'};"
						>
							{className}
						</button>
					{/each}
				</div>
			</div>

			<!-- Professor Restrictions -->
			<div class="restriction-box">
				<h2 class="restriction-title">Professor Restrictions</h2>
				<div class="restriction-items">
					{#each $prohibitedProfessors as prof, i}
						<button
							class="restriction-button professor-restriction"
							on:click={() => {
								$showProfessorModals[i] = true;
								$showProfessorModals = [
									...$showProfessorModals,
								];
							}}
						>
							{prof}
						</button>
					{/each}
				</div>
			</div>

			<!-- Time Restrictions -->
			<div class="restriction-box">
				<h2 class="restriction-title">Time Restrictions</h2>
				<div class="restriction-items">
					{#each $prohibitedTimes as time, i}
						<div class="restriction-button time-restriction">
							<span class="restriction-text"
								>{logic.formatTimeRestriction(time)}</span
							>
							<button
								class="remove-btn"
								on:click|stopPropagation={() =>
									logic.removeProhibitedTime(i)}
								aria-label="Remove time restriction"
							>
								<svg
									class="remove-icon"
									xmlns="http://www.w3.org/2000/svg"
									width="14"
									height="14"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
								>
									<line x1="18" y1="6" x2="6" y2="18"></line>
									<line x1="6" y1="6" x2="18" y2="18"></line>
								</svg>
							</button>
						</div>
					{/each}
				</div>
			</div>
		</div>

		<!-- Display error message if present -->
		{#if $error}
			<div class="error-message" role="alert">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="20"
					height="20"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
				>
					<circle cx="12" cy="12" r="10"></circle>
					<line x1="12" y1="8" x2="12" y2="12"></line>
					<line x1="12" y1="16" x2="12.01" y2="16"></line>
				</svg>
				{$error}
			</div>
		{/if}

		<!-- Loading, empty state, or schedules -->
		{#if $generatingSchedules}
			<div class="loading-container">
				<div class="spinner"></div>
				<p>Generating schedules, please wait...</p>
			</div>
		{:else if sortedSchedules.length === 0}
			<div class="empty-state">
				<div class="empty-state-icon">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="64"
						height="64"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="1"
					>
						<rect x="3" y="4" width="18" height="18" rx="2" ry="2"
						></rect>
						<line x1="16" y1="2" x2="16" y2="6"></line>
						<line x1="8" y1="2" x2="8" y2="6"></line>
						<line x1="3" y1="10" x2="21" y2="10"></line>
					</svg>
				</div>
				<h2>No schedules generated yet</h2>
				<p>
					Add some classes and click "Generate Schedules" to get
					started
				</p>
			</div>
		{:else}
			<div class="schedules-header">
				<h2>Generated Schedules</h2>
				<div class="schedules-count">
					<span class="badge">{$generatedSchedules.length}</span> possible
					schedules found
				</div>
			</div>
			<div class="schedules-container">
				{#each sortedSchedules as schedule, i (i)}
					<ScheduleView
						scheduleData={schedule}
						colorMap={$colorMap}
						scheduleIndex={i}
					/>
				{/each}
			</div>
		{/if}
	</main>
</div>

<!-- Modals -->
{#if $showTimeSelectionModal}
	<TimeSelectionModal
		prohibitedTimes={$prohibitedTimes}
		showTimeSelectionModal={$showTimeSelectionModal}
		on:close={() => ($showTimeSelectionModal = false)}
		on:add={(event) => {
			// Use the new function to prevent duplicates
			const result = addTimeRestriction(event.detail, $prohibitedTimes);
			$prohibitedTimes = result.map((item) =>
				item instanceof Map ? item : new Map(Object.entries(item)),
			);
			$showTimeSelectionModal = false;
		}}
		on:addMultiple={(event) => {
			// Use the new function to prevent duplicates for multiple restrictions
			$prohibitedTimes = addMultipleTimeRestrictions(
				event.detail,
				$prohibitedTimes,
			).map((item) =>
				item instanceof Map ? item : new Map(Object.entries(item)),
			);
			$showTimeSelectionModal = false;
		}}
	/>
{/if}

{#if $showAddClassModal}
	<AddClassModal
		availableClasses={$availableClasses}
		addedClasses={$addedClasses}
		showAddClassModal={$showAddClassModal}
		colorMap={$colorMap}
		showModals={$showClassModals}
		on:close={() => ($showAddClassModal = false)}
		on:add={(event) => {
			const data = event.detail;
			const className = typeof data === "string" ? data : data.className;

			if (!$addedClasses.includes(className)) {
				// Add the class
				$addedClasses = [...$addedClasses, className];

				// Fetch professor information for this class
				logic.fetchClassDetails(className);

				// Generate a color for the class
				if (!$colorMap.has(className)) {
					$colorMap.set(
						className,
						logic.generateColor($addedClasses.length - 1),
					);
				}

				// Remove from available classes
				$availableClasses = $availableClasses.filter(
					(c) => c !== className,
				);

				// Update showClassModals array
				$showClassModals = new Array($addedClasses.length).fill(false);

				// If event.detail is an object with showModal set to true, show the modal
				if (typeof data === "object" && data.showModal) {
					// Set the modal flag for the newly added class to true
					$showClassModals[$addedClasses.length - 1] = true;
				}

				$showAddClassModal = false;
			}
		}}
	/>
{/if}

{#each $addedClasses as _, i}
	{#if $showClassModals[i]}
		<ClassModal
			className={$addedClasses[i]}
			showModal={$showClassModals[i]}
			prohibitedProfessors={$prohibitedProfessors}
			index={i}
			showProfessorModals={$showProfessorModals}
			closeModal={logic.closeClassModal}
			removeClasses={logic.removeClasses}
			prohibitProf={logic.prohibitProf}
			reAddProfessor={logic.reAddProfessor}
			on:viewProfessor={logic.viewProfessorDetails}
		/>
	{/if}
{/each}

{#each $viewProfessorInfo as profInfo, i}
	{#if profInfo.showModal}
		<ProfessorModal
			profName={profInfo.name}
			addedClasses={$addedClasses}
			showModal={profInfo.showModal}
			index={i}
			closeModal={logic.closeViewProfessorModal}
			reAddProfessor={logic.reAddProfessor}
			isViewOnly={true}
			returnTo={profInfo.returnTo}
		/>
	{/if}
{/each}

{#each $prohibitedProfessors as prof, i}
	{#if $showProfessorModals[i]}
		<ProfessorModal
			profName={prof}
			addedClasses={$addedClasses}
			showModal={$showProfessorModals[i]}
			index={i}
			closeModal={logic.closeProfModal}
			reAddProfessor={logic.reAddProfessor}
		/>
	{/if}
{/each}

<style>
	.app-container {
		display: flex;
		flex-direction: column;
		min-height: 100vh;
		width: 100%; /* Full width */
		margin: 0;
		padding: 0;
		overflow-x: hidden; /* Prevent horizontal scroll */
	}

	.app-header {
		background-color: white;
		padding: var(--space-4) 0;
		box-shadow: var(--shadow-sm);
		border-bottom: 1px solid var(--neutral-200);
		position: sticky;
		top: 0;
		z-index: 10;
		width: 100%; /* Full width */
	}

	.header-content {
		width: 100%;
		max-width: 100%; /* Use full width */
		margin: 0 auto;
		padding: 0 var(--space-4); /* Padding on the content */
		display: flex;
		justify-content: space-between;
		align-items: center;
		box-sizing: border-box; /* Include padding in width calculation */
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: var(--space-4);
		flex: 1; /* Take up available space */
	}

	.app-title {
		font-size: 1.5rem;
		font-weight: 700;
		margin: 0;
		color: var(--primary);
	}

	.header-actions {
		display: flex;
		gap: var(--space-3);
		flex: 1; /* Take up available space */
		justify-content: flex-end; /* Align buttons to the right */
	}

	.app-main {
		padding: var(--space-5) var(--space-4);
		flex: 1;
		width: 100%; /* Full width */
		box-sizing: border-box;
		overflow-x: hidden; /* Ensure content doesn't overflow */
	}

	/* Restrictions styling */
	.restrictions-container {
		display: grid;
		grid-template-columns: repeat(3, 1fr); /* Three equal columns */
		gap: var(--space-5);
		margin-bottom: var(--space-6);
		width: 100%;
	}

	.restriction-box {
		background-color: white;
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-sm);
		overflow: hidden;
		transition: var(--transition-normal);
		display: flex; /* Use flexbox for layout */
		flex-direction: column; /* Stack children vertically */
		width: 100%; /* Ensure full width within grid cell */
		height: 100%; /* Fill the grid cell height */
	}

	.restriction-box:hover {
		box-shadow: var(--shadow-md);
	}

	.restriction-title {
		padding: var(--space-3) var(--space-4);
		font-size: 1rem;
		font-weight: 600;
		color: var(--neutral-800);
		background-color: var(--neutral-50);
		border-bottom: 1px solid var(--neutral-200);
		margin: 0;
		text-align: center; /* Center the title text */
		width: 100%; /* Ensure full width */
		box-sizing: border-box; /* Include padding in width calculation */
	}

	.restriction-items {
		padding: var(--space-3) var(--space-4);
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-2);
		min-height: 80px;
		flex-grow: 1; /* Allow items area to grow */
		width: 100%; /* Full width */
	}

	.restriction-button {
		border-radius: var(--radius-full);
		font-size: 0.875rem;
		padding: var(--space-1) var(--space-3);
		border: 1px solid var(--neutral-300);
		background-color: var(--neutral-100);
		color: var(--neutral-800);
		display: inline-flex;
		align-items: center;
		gap: var(--space-2);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.restriction-button:hover {
		transform: translateY(-1px);
		box-shadow: var(--shadow-sm);
	}

	.professor-restriction {
		background-color: var(--neutral-100);
		border-color: var(--neutral-300);
	}

	.time-restriction {
		background-color: var(--primary-light);
		border-color: #f8d7dc;
		cursor: default; /* Change cursor to default since it's not clickable */
		padding: var(--space-1) var (--space-2); /* Reduced padding */
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--space-1); /* Reduced gap */
		font-size: 0.75rem; /* Smaller font size */
		height: 1.75rem; /* Explicit height to make it smaller */
		min-height: auto; /* Override any min-height */
		line-height: 1; /* Tighter line height */
	}

	.restriction-text {
		font-size: 0.75rem; /* Smaller font size */
		white-space: nowrap; /* Prevent text wrapping */
	}

	.remove-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		background: none;
		border: none;
		padding: 1px; /* Smaller padding */
		border-radius: 50%;
		margin-left: var(--space-1);
		cursor: pointer;
		transition: background-color var(--transition-fast);
		width: 16px; /* Explicit width */
		height: 16px; /* Explicit height */
		min-width: 16px; /* Ensure it doesn't grow */
	}

	.remove-icon {
		color: var (--neutral-500);
		width: 12px; /* Smaller icon */
		height: 12px; /* Smaller icon */
		min-width: 12px; /* Force size */
		min-height: 12px; /* Force size */
	}

	/* Empty state */
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--space-7);
		text-align: center;
		color: var (--neutral-600);
		background-color: white;
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-sm);
	}

	.empty-state-icon {
		color: var(--neutral-400);
		margin-bottom: var (--space-4);
	}

	.empty-state h2 {
		font-size: 1.25rem;
		font-weight: 600;
		margin-bottom: var(--space-2);
		color: var(--neutral-800);
	}

	.empty-state p {
		max-width: 400px;
		color: var(--neutral-600);
	}

	/* Loading spinner */
	.loading-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--space-6);
	}

	.spinner {
		width: 40px;
		height: 40px;
		border: 4px solid rgba(226, 24, 51, 0.1);
		border-top: 4px solid var(--primary);
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin-bottom: var(--space-4);
	}

	@keyframes spin {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
	}

	/* Schedules */
	.schedules-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--space-4);
	}

	.schedules-header h2 {
		margin: 0;
		font-size: 1.25rem;
		color: var(--neutral-900);
	}

	.schedules-count {
		color: var(--neutral-600);
		font-size: 0.875rem;
		display: flex;
		align-items: center;
	}

	.badge {
		background-color: var(--primary);
		color: white;
		border-radius: var(--radius-full);
		padding: 2px 8px;
		font-weight: 600;
		margin-right: var(--space-2);
		font-size: 0.75rem;
	}

	.schedules-container {
		display: flex;
		flex-direction: column;
		gap: var(--space-5);
		width: 100%; /* Full width */
		overflow-x: hidden;
	}

	/* Error message */
	.error-message {
		background-color: rgba(244, 67, 54, 0.1);
		border-left: 4px solid var(--error);
		padding: var(--space-3) var(--space-4);
		margin: var(--space-4) 0;
		border-radius: var(--radius-md);
		color: var(--neutral-800);
		display: flex;
		align-items: center;
		gap: var(--space-3);
	}

	/* Empty state indicators */
	.restriction-items:empty::before {
		content: "None added";
		color: var (--neutral-500);
		font-style: italic;
		font-size: 0.875rem;
		width: 100%;
		text-align: center;
		padding: var(--space-3) 0;
	}

	/* Responsive styles */
	@media (max-width: 1200px) {
		.restrictions-container {
			grid-template-columns: repeat(
				2,
				1fr
			); /* Two equal columns on medium screens */
		}
	}

	@media (max-width: 768px) {
		.header-content {
			flex-direction: column;
			align-items: flex-start;
			gap: var(--space-3);
		}

		.header-left {
			width: 100%;
			flex-wrap: wrap;
			margin-bottom: var(--space-2);
		}

		.header-actions {
			width: 100%;
			flex-wrap: wrap;
			gap: var(--space-2);
			justify-content: flex-start; /* Left align on mobile */
		}

		.btn {
			flex: 1;
			min-width: 0; /* Allow buttons to shrink */
			font-size: 0.85rem; /* Smaller text on mobile */
		}

		.restrictions-container {
			grid-template-columns: 1fr; /* Single column on mobile */
		}

		/* Fix potential overflow in the schedule view */
		.schedules-container {
			width: 100%;
			overflow-x: auto; /* Allow horizontal scroll if needed */
		}

		.app-main {
			padding: var(--space-3) var(--space-3);
		}

		/* Make buttons stack vertically on very small screens */
		@media (max-width: 480px) {
			.header-actions {
				flex-direction: column;
				width: 100%;
			}
		}
	}
</style>
