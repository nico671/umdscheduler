<script lang="ts">
	import { onMount, onDestroy } from "svelte";
	import ClassModal from "../components/ClassModal.svelte";
	import AddClassModal from "../components/AddClassModal.svelte";
	import TimeSelectionModal from "../components/TimeSelectionModal.svelte";
	import ProfessorModal from "../components/ProfessorModal.svelte";
	import ScheduleView from "../components/ScheduleView.svelte";
	import "../styles/page.css";
	import "./styles/page-styles.css";

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
	} from "./page-logic";

	let scrollContainer: HTMLElement | null = null;

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
		// Fetch available classes
		try {
			const url = new URL("https://api.umd.io/v1/courses/list");
			url.searchParams.set("sort", "course_id,-credits");
			url.searchParams.set("semester", "202501");

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

		// Initialize class-professor tracking
		$addedClasses.forEach((className) => {
			logic.fetchClassDetails(className);
		});
	});
</script>

<div class="container">
	<header class="header">
		<div class="header-row">
			<h1 class="header-title">UMDScheduler</h1>
			<div class="header-actions">
				<button
					class="header-button"
					on:click={() => ($showTimeSelectionModal = true)}
				>
					Add Time Restriction
				</button>
				<button
					class="header-button"
					on:click={() => ($showAddClassModal = true)}
				>
					Add Class
				</button>
				<button
					class="header-button"
					on:click={logic.generateSchedules}
					disabled={$generatingSchedules}
				>
					Generate Schedules
				</button>
			</div>
		</div>
	</header>

	<main>
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
							) || '#64646443'}; 
									   border-color: {$colorMap.get(className)
								? logic.shade(
										$colorMap.get(className) ?? '#646464',
										20,
									)
								: '#646464b2'};"
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
							class="restriction-button"
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
						<button
							class="restriction-button"
							on:click={() => logic.removeProhibitedTime(i)}
						>
							{logic.formatTimeRestriction(time)} ×
						</button>
					{/each}
				</div>
			</div>
		</div>

		{#if $error}
			<div class="error-message">
				{$error}
			</div>
		{/if}

		{#if $generatingSchedules}
			<div class="loading-spinner">
				<div class="spinner"></div>
				<p>Generating schedules, please wait...</p>
			</div>
		{:else if sortedSchedules.length === 0}
			<div id="no-sched-div">
				<h2>No schedules generated yet</h2>
				<p>
					Add some classes and click "Generate Schedules" to get
					started
				</p>
			</div>
		{:else}
			<div class="schedules-info">
				<h2>Generated Schedules</h2>
				<p>
					Showing {$generatedSchedules.length} schedules
				</p>
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
			$prohibitedTimes = [...$prohibitedTimes, event.detail];
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
	/* Override any inline styles that might be causing overflow */
	header {
		font-family: "Haas Grot Text R Web", "Helvetica Neue", Helvetica, Arial,
			sans-serif;
		padding: 1vh;
		margin: 0;
		width: 100%;
		max-width: 100%;
		height: 100%;
		position: sticky;
		box-sizing: border-box;
	}

	/* body {
		font-family: "Haas Grot Text R Web", "Helvetica Neue", Helvetica, Arial,
			sans-serif;
		padding: 1vh;
		margin: 0;
		width: 100%;
		max-width: 100%;
		height: 100%;
		display: flex;
		flex-direction: column;
		height: fit-content;
		box-sizing: border-box;
		overflow-x: hidden;
	} */

	main {
		width: 100%;
		max-width: 100%;
		padding: 0;
		margin: 0;
		box-sizing: border-box;
	}

	/* ...rest of existing styles... */

	.schedules-container {
		width: 100%;
		display: flex;
		flex-direction: column;
		gap: 20px;
		padding: 20px 0;
		overflow-y: visible; /* Allow content to expand */
		overflow-x: hidden;
		height: auto; /* Auto height instead of fixed */
		min-height: auto; /* No minimum height */
		max-height: none; /* No max height restriction */
	}

	/* ...rest of existing styles... */

	h2 {
		padding-left: 0vh;
		padding-top: 1vh;
		margin: 0px;
	}

	/* #im-bad-at-css-holder-div {
		display: flex;
		flex-direction: column;
		justify-content: start;
		align-items: start;
		padding: 0px;
		margin: 0px;
		border-radius: 0px 0px 15px 15px;
	} */

	.restriction-box {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		justify-content: flex-start;
		min-height: 15vh;
		padding: 0;
		margin: 0;
		border-radius: 15px;
		background-color: #f0f0f0;
	}

	.restriction-title {
		padding: 12px 16px;
		margin: 0;
		/* color: var(--umd-red); */
		font-size: 1.2rem;
		font-weight: 600;
	}

	.restriction-items {
		width: 100%;
		display: flex;
		flex-wrap: wrap;
		padding: 0 16px 16px;
		margin-bottom: 1vh;
		justify-content: flex-start;
		box-sizing: border-box;
	}

	#no-sched-div {
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
	}

	/* .lds-dual-ring,
	.lds-dual-ring:after {
		box-sizing: border-box;
	}
	.lds-dual-ring {
		display: inline-block;
		width: 80px;
		height: 80px;
	}
	.lds-dual-ring:after {
		content: " ";
		display: block;
		width: 64px;
		height: 64px;
		margin: 8px;
		border-radius: 50%;
		border: 6.4px solid currentColor;
		border-color: currentColor transparent currentColor transparent;
		animation: lds-dual-ring 1.2s linear infinite;
	}
	@keyframes lds-dual-ring {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
	} */

	.restriction-button {
		/* Base styling */
		border-radius: 25px;
		text-align: center;
		font-size: 0.9rem;
		font-weight: 500;
		padding: 8px 12px;
		padding-left: 12px;
		width: fit-content;
		height: auto;
		margin: 4px;
		transition: all 0.2s ease;
		color: #333;
		cursor: pointer;
	}

	.restriction-button:hover {
		transform: translateY(-1px);
		box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
	}

	.header-button {
		background-color: #f0f0f0;
		border-radius: 8px;
		border-width: 0;
		color: black;
		cursor: pointer;
		display: inline-block;
		font-family: "Haas Grot Text R Web", "Helvetica Neue", Helvetica, Arial,
			sans-serif;
		font-size: 1.5vw;
		font-weight: 500;
		line-height: 20px;
		list-style: none;
		padding: 1vw;
		text-align: center;
		transition: all 200ms;
		vertical-align: baseline;
		white-space: nowrap;
		user-select: none;
		-webkit-user-select: none;
		touch-action: manipulation;
	}

	/* #restrictions-container {
		display: flex;
		flex-direction: row;
		justify-content: space-between;
		align-items: center;
		width: 100%;
	}

	#header-text {
		margin: 0px;
		font-size: 3vw;
		color: #e21833;
	}

	#header-row {
		display: flex;
		flex-direction: row;
		justify-content: space-between;
		width: 100%;
		padding-bottom: 2vh;
		margin: 0px;
	} */

	:host {
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
	}

	.schedules-container {
		width: 100%;
		display: flex;
		flex-direction: column;
		gap: 20px;
		padding: 20px 0;
	}

	.error-message {
		color: var(--umd-red);
		padding: 15px;
		background-color: rgba(226, 24, 51, 0.1);
		border-radius: 8px;
		margin: 20px 0;
		text-align: center;
	}

	.loading-spinner {
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		min-height: 200px;
	}

	.loading-spinner p {
		margin-top: 20px;
		color: #666;
	}

	/* .generate-button {
		margin-top: 20px;
	} */

	.schedules-info {
		margin: 20px 0;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.schedules-info h2 {
		margin: 0;
		color: var(--umd-red);
	}

	.schedules-info p {
		color: #666;
	}

	.loading-more {
		display: flex;
		flex-direction: row;
		align-items: center;
		justify-content: center;
		padding: 20px 0;
		gap: 10px;
	}

	.spinner-small {
		width: 20px;
		height: 20px;
		border: 3px solid #f3f3f3;
		border-top: 3px solid #e21833;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	.loading-more p {
		margin: 0;
		color: #666;
		font-size: 0.9rem;
	}
</style>
