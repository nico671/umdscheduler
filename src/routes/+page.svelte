<script lang="ts">
	import { onMount, onDestroy } from "svelte";
	import ClassModal from "../components/ClassModal.svelte";
	import AddClassModal from "../components/AddClassModal.svelte";
	import TimeSelectionModal from "../components/TimeSelectionModal.svelte";
	import ProfessorModal from "../components/ProfessorModal.svelte";
	import ScheduleView from "../components/ScheduleView.svelte";
	import "../styles/page.css";
	import { fetchWithProxy } from "../lib/proxy";

	interface Schedule {
		prof_weight: number;
		[key: string]: any; // Allow for other properties
	}

	let availableClasses: string[] = [];
	let addedClasses: string[] = [];
	let prohibitedTimes: Map<string, string>[] = [];
	let prohibitedProfessors: string[] = [];
	let generatedSchedules: any[] = [];
	let colorMap = new Map();
	let showTimeSelectionModal = false;
	let showAddClassModal = false;
	let generatingSchedules = false;
	let currentAmountLoaded = 0;
	let showClassModals: boolean[] = [];
	let showProfessorModals: boolean[] = [];
	let scrollContainer: HTMLElement | null = null;
	let schedules: any[] = [];
	let sortOption = "rating"; // Default sort option
	let error: string | null = null;
	let viewProfessorInfo: { name: string; showModal: boolean }[] = [];

	// Theme colors
	const umdRed = "#e21833";
	const umdGold = "#FFD200";

	// Color generator for classes
	function generateColor(index: number) {
		const hues = [210, 180, 120, 330, 270, 30, 150, 300, 60, 240];
		const hue = hues[index % hues.length];
		return `hsl(${hue}, 70%, 85%)`;
	}

	const generateSchedules = async () => {
		if (addedClasses.length === 0) {
			error = "Please add at least one class before generating schedules";
			return;
		}

		generatedSchedules = [];
		schedules = [];
		currentAmountLoaded = 0;
		generatingSchedules = true;
		error = null;

		try {
			// Fix the data structure for prohibited times
			const formattedProhibitedTimes = prohibitedTimes.map((timeMap) => {
				// Handle both Map objects and plain objects
				if (timeMap instanceof Map) {
					return Object.fromEntries(timeMap);
				}
				return timeMap;
			});

			const requestData = {
				wanted_classes: addedClasses,
				restrictions: {
					minSeats: 1,
					prohibitedInstructors: prohibitedProfessors,
					prohibitedTimes: formattedProhibitedTimes,
					required_classes: addedClasses,
				},
			};

			console.log(
				"Sending request to generate schedules:",
				JSON.stringify(requestData),
			);

			try {
				// Direct fetch to backend - no proxy
				const response = await fetch("http://127.0.0.1:5000/schedule", {
					method: "POST",
					headers: {
						"Content-Type": "application/json",
						Accept: "application/json",
						Origin: "http://localhost:5173",
					},
					body: JSON.stringify(requestData),
					mode: "cors",
					credentials: "omit",
				});

				if (!response.ok) {
					const errorText = await response.text();
					throw new Error(
						`HTTP error! Status: ${response.status}, Details: ${errorText}`,
					);
				}

				const data = await response.json();
				processScheduleData(data);
			} catch (fetchError) {
				console.error("Direct fetch failed:", fetchError);
				error = `Failed to connect to the backend server. Make sure it's running at http://127.0.0.1:5000 and reload the page.`;
			}
		} catch (err) {
			console.error("Error generating schedules:", err);
			error =
				err instanceof Error
					? `Error: ${err.message}`
					: "An error occurred while generating schedules";
		} finally {
			generatingSchedules = false;
		}
	};

	function processScheduleData(data: any) {
		console.log(`Received ${data?.length || 0} schedules`);

		if (!Array.isArray(data) || data.length === 0) {
			error = "No possible schedules found with your constraints";
		} else {
			generatedSchedules = data;
			addNewSchedules();
		}
	}

	const addNewSchedules = () => {
		if (
			!Array.isArray(generatedSchedules) ||
			generatedSchedules.length === 0
		) {
			return;
		}

		const remainingCount = generatedSchedules.length - currentAmountLoaded;
		if (remainingCount <= 0) {
			return;
		}

		const batchSize = 10;
		const count = Math.min(batchSize, remainingCount);

		const newSchedules = generatedSchedules.slice(
			currentAmountLoaded,
			currentAmountLoaded + count,
		);

		currentAmountLoaded += count;
		console.log(
			`Adding ${count} schedules, total now ${currentAmountLoaded}/${generatedSchedules.length}`,
		);

		schedules = [...schedules, ...newSchedules];
	};

	function removeProhibitedTime(index: number) {
		prohibitedTimes.splice(index, 1);
		prohibitedTimes = [...prohibitedTimes];
	}

	// Format time restriction for display
	function formatTimeRestriction(
		timeMap: Map<string, string> | Record<string, string>,
	): string {
		// Ensure we're working with a Map
		const map =
			timeMap instanceof Map ? timeMap : new Map(Object.entries(timeMap));

		const days = (map.get("days") || "") as string;
		const start = formatTimeForDisplay(
			(map.get("start_time") || "") as string,
		);
		const end = formatTimeForDisplay((map.get("end_time") || "") as string);

		// Convert day code to display format
		let dayDisplay = "";
		switch (days) {
			case "M":
				dayDisplay = "Monday";
				break;
			case "Tu":
				dayDisplay = "Tuesday";
				break;
			case "W":
				dayDisplay = "Wednesday";
				break;
			case "Th":
				dayDisplay = "Thursday";
				break;
			case "F":
				dayDisplay = "Friday";
				break;
			default:
				dayDisplay = days;
		}

		return `${dayDisplay}: ${start} - ${end}`;
	}

	// Format time string for display
	function formatTimeForDisplay(timeString: string): string {
		// Extract hour and minute from format like "08:00am"
		const match = timeString.match(/^(\d{1,2}):(\d{2})(am|pm)$/i);
		if (!match) return timeString;

		const [_, hour, minute, period] = match;
		return `${hour}:${minute} ${period.toUpperCase()}`;
	}

	// Add a structure to track which professors belong to which classes
	let classProfessors: Record<string, string[]> = {};

	// Enhanced function to fetch class details and update professor associations
	async function fetchClassDetails(className: string) {
		try {
			const url = new URL(`https://api.umd.io/v1/courses/${className}`);
			const response = await fetch(url);
			const data = await response.json();

			if (Array.isArray(data) && data.length > 0) {
				// Extract professors from sections
				const professors: string[] = [];
				if (data[0].sections) {
					data[0].sections.forEach((section: any) => {
						if (section.instructors) {
							section.instructors.forEach(
								(instructor: string) => {
									if (
										instructor &&
										instructor !== "Instructor: TBA" &&
										!professors.includes(instructor)
									) {
										professors.push(instructor);
									}
								},
							);
						}
					});
				}

				// Store the professors for this class
				classProfessors[className] = professors;
			}
		} catch (error) {
			console.error(`Error fetching details for ${className}:`, error);
		}
	}

	// Enhanced function to remove classes
	function removeClasses(value: string) {
		const index = addedClasses.indexOf(value);
		if (index !== -1) {
			// Remove the class
			addedClasses.splice(index, 1);
			addedClasses = [...addedClasses];

			// Remove the color from the map
			colorMap.delete(value);

			// Update modal array
			showClassModals = new Array(addedClasses.length).fill(false);

			// Add back to available classes
			if (!availableClasses.includes(value)) {
				availableClasses.push(value);
				availableClasses.sort();
			}

			// Remove professors that were only associated with this class
			const profsToKeep = new Set<string>();

			// Collect all professors from remaining classes
			Object.entries(classProfessors).forEach(([className, profs]) => {
				if (className !== value && addedClasses.includes(className)) {
					profs.forEach((prof) => profsToKeep.add(prof));
				}
			});

			// Filter out professors that are no longer needed
			prohibitedProfessors = prohibitedProfessors.filter((prof) =>
				profsToKeep.has(prof),
			);

			// Update professor modals
			showProfessorModals = new Array(prohibitedProfessors.length).fill(
				false,
			);

			// Remove the class from the classProfessors map
			delete classProfessors[value];
		}
	}

	// Update the professor prohibition function to track which classes have which professors
	async function prohibitProf(prof: string) {
		if (prohibitedProfessors.includes(prof)) {
			return;
		}
		prohibitedProfessors.push(prof);
		prohibitedProfessors = [...prohibitedProfessors];

		// Update modal array
		showProfessorModals = new Array(prohibitedProfessors.length).fill(
			false,
		);
	}

	function reAddProfessor(prof: string) {
		if (!prohibitedProfessors.includes(prof)) {
			return;
		}
		const index = prohibitedProfessors.indexOf(prof);
		prohibitedProfessors.splice(index, 1);
		prohibitedProfessors = [...prohibitedProfessors];

		// Update modal array
		showProfessorModals = new Array(prohibitedProfessors.length).fill(
			false,
		);
	}

	function closeClassModal(index: number) {
		showClassModals[index] = false;
		showClassModals = [...showClassModals];
	}

	function closeProfModal(index: number) {
		showProfessorModals[index] = false;
		showProfessorModals = [...showProfessorModals];
	}

	function viewProfessorDetails(profName: string) {
		// Check if we're already tracking this professor
		const existingIndex = viewProfessorInfo.findIndex(
			(p) => p.name === profName,
		);

		if (existingIndex >= 0) {
			// Update existing entry
			viewProfessorInfo[existingIndex].showModal = true;
			viewProfessorInfo = [...viewProfessorInfo];
		} else {
			// Add new entry
			viewProfessorInfo = [
				...viewProfessorInfo,
				{
					name: profName,
					showModal: true,
				},
			];
		}
	}

	function closeViewProfessorModal(index: number) {
		if (viewProfessorInfo[index]) {
			viewProfessorInfo[index].showModal = false;
			viewProfessorInfo = [...viewProfessorInfo];
		}
	}

	onMount(async () => {
		// Fetch available classes
		try {
			const url = new URL("https://api.umd.io/v1/courses/list");
			url.searchParams.set("sort", "course_id,-credits");
			url.searchParams.set("semester", "202501");

			const response = await fetch(url);
			const data = await response.json();
			availableClasses = data.map(
				(item: { course_id: string }) => item.course_id,
			);
		} catch (err) {
			error =
				err instanceof Error ? err.message : "Failed to fetch classes";
			console.error("Error fetching classes:", err);
		}

		// Initialize class-professor tracking
		addedClasses.forEach((className) => {
			fetchClassDetails(className);
		});

		const cleanup = initializeScrollListener();
		if (cleanup) {
			onDestroy(cleanup);
		}
	});

	function sortSchedules(schedules: any[]) {
		if (sortOption === "rating") {
			return [...schedules].sort(
				(a, b) => b["prof_weight"] - a["prof_weight"],
			);
		} else {
			// Add more sorting options as needed
			return schedules;
		}
	}

	// Assign colors to added classes
	$: {
		addedClasses.forEach((className, index) => {
			if (!colorMap.has(className)) {
				colorMap.set(className, generateColor(index));
			}
		});
	}

	$: sortedSchedules = sortSchedules(schedules);

	// Listen for changes to addedClasses to update classProfessors
	$: {
		if (addedClasses.length > 0) {
			// Check for any new classes that need professor information
			addedClasses.forEach((className) => {
				if (!classProfessors[className]) {
					fetchClassDetails(className);
				}
			});
		}
	}

	function initializeScrollListener() {
		if (!scrollContainer) return undefined;

		const handleScroll = () => {
			if (scrollContainer) {
				const { scrollTop, scrollHeight, clientHeight } =
					scrollContainer;
				if (
					scrollTop + clientHeight >= scrollHeight - 100 &&
					!generatingSchedules
				) {
					addNewSchedules();
				}
			}
		};

		if (scrollContainer) {
			scrollContainer.addEventListener("scroll", handleScroll);
			return () =>
				scrollContainer?.removeEventListener("scroll", handleScroll);
		}

		return undefined;
	}

	// Helper function to darken colors for borders
	function shade(color: string, percent: number): string {
		// Parse the HSL color
		const match = color.match(/hsl\((\d+),\s*(\d+)%,\s*(\d+)%\)/);
		if (!match) return color;

		const h = parseInt(match[1], 10);
		const s = parseInt(match[2], 10);
		// Darken the lightness by the given percentage
		const l = Math.max(parseInt(match[3], 10) - percent, 0);

		return `hsl(${h}, ${s}%, ${l}%)`;
	}
</script>

<div class="container">
	<header class="header">
		<div class="header-row">
			<h1 class="header-title">UMDScheduler</h1>
			<div class="header-actions">
				<button
					class="header-button"
					on:click={() => (showTimeSelectionModal = true)}
				>
					Add Time Restriction
				</button>
				<button
					class="header-button"
					on:click={() => (showAddClassModal = true)}
				>
					Add Class
				</button>
				<button
					class="header-button"
					on:click={generateSchedules}
					disabled={generatingSchedules}
				>
					Generate Schedules
				</button>
			</div>
		</div>
	</header>

	<main>
		<div class="restrictions-container">
			<!-- Class Selection (moved to first position) -->
			<div class="restriction-box">
				<h2 class="restriction-title">Selected Classes</h2>
				<div class="restriction-items">
					{#each addedClasses as className, i}
						<button
							class="restriction-button"
							on:click={() => (showClassModals[i] = true)}
							style="background-color: {colorMap.get(className) ||
								'#64646443'}; border-color: {colorMap.get(
								className,
							)
								? shade(colorMap.get(className), 20)
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
					{#each prohibitedProfessors as prof, i}
						<button
							class="restriction-button"
							on:click={() => (showProfessorModals[i] = true)}
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
					{#each prohibitedTimes as time, i}
						<button
							class="restriction-button"
							on:click={() => removeProhibitedTime(i)}
						>
							{formatTimeRestriction(time)} ×
						</button>
					{/each}
				</div>
			</div>
		</div>

		{#if error}
			<div class="error-message">
				{error}
			</div>
		{/if}

		{#if generatingSchedules}
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
					Showing {Math.min(
						currentAmountLoaded,
						generatedSchedules.length,
					)} of {generatedSchedules.length} possible schedules
				</p>
			</div>
			<div bind:this={scrollContainer} class="schedules-container">
				{#each sortedSchedules as schedule, i (i)}
					<ScheduleView
						scheduleData={schedule}
						{colorMap}
						scheduleIndex={i}
					/>
				{/each}
			</div>
		{/if}
	</main>
</div>

{#if showTimeSelectionModal}
	<TimeSelectionModal
		{prohibitedTimes}
		{showTimeSelectionModal}
		on:close={() => (showTimeSelectionModal = false)}
		on:add={(event) => {
			prohibitedTimes = [...prohibitedTimes, event.detail];
			showTimeSelectionModal = false;
		}}
	/>
{/if}

{#if showAddClassModal}
	<AddClassModal
		{availableClasses}
		{addedClasses}
		{showAddClassModal}
		{colorMap}
		showModals={showClassModals}
		on:close={() => (showAddClassModal = false)}
		on:add={(event) => {
			const data = event.detail;
			const className = typeof data === "string" ? data : data.className;

			if (!addedClasses.includes(className)) {
				// Add the class
				addedClasses = [...addedClasses, className];

				// Fetch professor information for this class
				fetchClassDetails(className);

				// Generate a color for the class
				if (!colorMap.has(className)) {
					colorMap.set(
						className,
						generateColor(addedClasses.length - 1),
					);
				}

				// Remove from available classes
				availableClasses = availableClasses.filter(
					(c) => c !== className,
				);

				// Update showClassModals array
				showClassModals = new Array(addedClasses.length).fill(false);

				// If event.detail is an object with showModal set to true, show the modal
				if (typeof data === "object" && data.showModal) {
					// Set the modal flag for the newly added class to true
					showClassModals[addedClasses.length - 1] = true;
				}

				showAddClassModal = false;
			}
		}}
	/>
{/if}

{#each addedClasses as _, i}
	{#if showClassModals[i]}
		<ClassModal
			className={addedClasses[i]}
			showModal={showClassModals[i]}
			{prohibitedProfessors}
			index={i}
			{showProfessorModals}
			closeModal={closeClassModal}
			{removeClasses}
			{prohibitProf}
			{reAddProfessor}
			on:viewProfessor={(event) =>
				viewProfessorDetails(event.detail.professorName)}
		/>
	{/if}
{/each}

{#each prohibitedProfessors as prof, i}
	{#if showProfessorModals[i]}
		<ProfessorModal
			profName={prof}
			{addedClasses}
			showModal={showProfessorModals[i]}
			index={i}
			closeModal={closeProfModal}
			{reAddProfessor}
		/>
	{/if}
{/each}

{#each viewProfessorInfo as profInfo, i}
	{#if profInfo.showModal}
		<ProfessorModal
			profName={profInfo.name}
			{addedClasses}
			showModal={profInfo.showModal}
			index={i}
			closeModal={() => closeViewProfessorModal(i)}
			{reAddProfessor}
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
		max-width: 100%;
		display: flex;
		flex-direction: column;
		gap: 20px;
		padding: 20px 0;
		overflow-x: hidden;
		box-sizing: border-box;
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

	.restriction-items {
		width: fit-content;
		display: flex;
		flex-wrap: wrap;
		padding: 1vh;
		margin-bottom: 1vh;
		justify-content: flex-start;
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
</style>
