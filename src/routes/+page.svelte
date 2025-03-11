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
		// Add the imported functions:
		fetchAvailableClasses,
		handleSemesterChange,
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
