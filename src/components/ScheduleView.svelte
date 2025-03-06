<script lang="ts">
	import { onMount } from "svelte";
	import SectionDetailModal from "./SectionDetailModal.svelte";
	let dayLabels: any[][] = [[], [], [], [], []];
	let daysCodes = ["M", "Tu", "W", "Th", "F"];
	let dayNames = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

	export let colorMap: Map<string, string> = new Map<string, string>();
	export let scheduleData: any;
	export let scheduleIndex: number = 0;

	// Define more precise time constants for better alignment
	const hourHeight = 60; // Height in pixels for one hour
	const dayHeaderHeight = 50; // Height of day header
	let earliestStart = 480; // 8:00 AM in minutes from midnight
	let latestEnd = 1200; // 8:00 PM in minutes from midnight
	const totalHours = (latestEnd - earliestStart) / 60;
	const scheduleHeight = totalHours * hourHeight;

	// Generate time labels for the schedule with more precision
	let timeLabels: string[] = [];
	for (let i = earliestStart; i <= latestEnd; i += 60) {
		const hour = Math.floor(i / 60);
		const meridiem = hour >= 12 ? "PM" : "AM";
		const displayHour = hour > 12 ? hour - 12 : hour === 0 ? 12 : hour;
		timeLabels.push(`${displayHour}:00 ${meridiem}`);
	}

	let showSectionModal = false;
	let selectedSectionId = "";
	let selectedCourseId = "";

	// Function to open section details
	function openSectionDetails(courseId: string, sectionId: string) {
		selectedCourseId = courseId;
		selectedSectionId = sectionId;
		showSectionModal = true;
	}

	// Function to close section modal
	function closeSectionModal() {
		showSectionModal = false;
		// Don't reset the IDs until after animation completes
		setTimeout(() => {
			selectedSectionId = "";
			selectedCourseId = "";
		}, 300);
	}

	onMount(() => {
		// Process schedule data
		Object.keys(scheduleData).forEach((element) => {
			const meetings = scheduleData[element]?.meetings;
			if (meetings) {
				meetings.forEach((classTime: any) => {
					const days = classTime.days.toString();
					const startDate = createDate(classTime.start_time);
					const endDate = createDate(classTime.end_time);

					const { startPixels, heightPixels } = calculateSlotTimes(
						startDate,
						endDate,
					);

					daysCodes.forEach((dayCode, k) => {
						if (days.includes(dayCode)) {
							const slot = {
								sectionCode: scheduleData[element]["number"],
								days: dayCode,
								startPixels, // pixels
								startTime: getFormattedTime(startDate),
								endTime: getFormattedTime(endDate),
								class: element,
								professor:
									scheduleData[element][
										"instructors"
									].toString(),
								location: `${classTime.building} ${classTime.room}`,
								prof_rating:
									scheduleData[element]["prof_weight"],
								heightPixels, // pixels
								// Add raw time values for overlap detection
								rawStartTime:
									startDate.getHours() * 60 +
									startDate.getMinutes(),
								rawEndTime:
									endDate.getHours() * 60 +
									endDate.getMinutes(),
							};
							dayLabels[k].push(slot);
						}
					});
				});
			}
		});

		// Find overlapping slots and adjust their horizontal position
		for (let dayIndex = 0; dayIndex < dayLabels.length; dayIndex++) {
			const dayClasses = dayLabels[dayIndex];

			if (dayClasses.length > 1) {
				// Sort by start time
				dayClasses.sort((a, b) => a.rawStartTime - b.rawStartTime);

				// Track overlapping groups
				const overlapGroups: any[][] = [];
				let currentGroup: any[] = [];

				// Group overlapping classes
				for (let i = 0; i < dayClasses.length; i++) {
					const current = dayClasses[i];

					if (i === 0) {
						// Start the first group with the first class
						currentGroup = [current];
					} else {
						// Check if this class overlaps with any in the current group
						const overlaps = currentGroup.some(
							(prev) =>
								current.rawStartTime < prev.rawEndTime &&
								current.rawEndTime > prev.rawStartTime,
						);

						if (overlaps) {
							// Add to current group if overlapping
							currentGroup.push(current);
						} else {
							// Start a new group if no overlap
							if (currentGroup.length > 0) {
								overlapGroups.push([...currentGroup]);
							}
							currentGroup = [current];
						}
					}
				}

				// Add the last group if not empty
				if (currentGroup.length > 0) {
					overlapGroups.push(currentGroup);
				}

				// Assign horizontal position for overlapping classes
				overlapGroups.forEach((group) => {
					if (group.length > 1) {
						for (let i = 0; i < group.length; i++) {
							group[i].horizontalPosition = i;
							group[i].totalOverlap = group.length;
						}
					}
				});
			}
		}

		// Trigger reactivity by reassigning dayLabels
		dayLabels = [...dayLabels];
	});

	const createDate = (dateStr: string) => {
		// Fix time parsing to be more robust
		const trimmedStr = dateStr.trim().toLowerCase();
		const isPM = trimmedStr.includes("pm");

		// Remove am/pm and extract hours and minutes
		const timeOnly = trimmedStr.replace(/am|pm/i, "").trim();
		const [hoursStr, minutesStr] = timeOnly.split(":");

		let hours = parseInt(hoursStr);
		const minutes = parseInt(minutesStr);

		// Proper 12-hour to 24-hour conversion
		if (isPM && hours < 12) {
			hours += 12;
		} else if (!isPM && hours === 12) {
			hours = 0;
		}

		const date = new Date();
		date.setHours(hours);
		date.setMinutes(minutes);
		date.setSeconds(0);
		return date;
	};

	const getFormattedTime = (date: Date) => {
		return new Intl.DateTimeFormat("en-US", {
			hour: "numeric",
			minute: "2-digit",
			hour12: true,
		}).format(date);
	};

	// Improved slot time calculation for precise alignment with the grid
	const calculateSlotTimes = (startDate: Date, endDate: Date) => {
		const startMinutes = startDate.getHours() * 60 + startDate.getMinutes();
		const endMinutes = endDate.getHours() * 60 + endDate.getMinutes();

		// Calculate position in pixels directly (no percentages)
		const pixelsPerMinute = hourHeight / 60;
		const startPixels = (startMinutes - earliestStart) * pixelsPerMinute;
		const heightPixels = (endMinutes - startMinutes) * pixelsPerMinute;

		return { startPixels, heightPixels };
	};

	function formatSlots(day: any[]) {
		// Change sort from "a.start" to "a.startPixels"
		return day.sort((a, b) => a.startPixels - b.startPixels);
	}

	// Fix the shouldShowDetails implementation
	function shouldShowDetails(heightPixels: number) {
		// For very small slots (less than 30 minutes)
		if (heightPixels < 30) return 0;
		// For small slots (30-45 minutes)
		if (heightPixels < 45) return 1;
		// For medium slots (45-75 minutes)
		if (heightPixels < 75) return 2;
		// For large slots (75+ minutes)
		return 3;
	}

	// Format professor name to be shorter
	function formatProfName(fullName: string): string {
		if (!fullName) return "TBA";

		// If there's a comma, assume it's "Last, First" format
		if (fullName.includes(",")) {
			const parts = fullName.split(",");
			return parts[0]; // Just return the last name
		}

		// Otherwise split by spaces and use first + last initial
		const names = fullName.trim().split(" ");
		if (names.length <= 1) return fullName;

		return names[0]; // Just return the first name
	}

	// Function to calculate average professor rating
	function calculateAverageRating(): string {
		if (!scheduleData) return "N/A";

		let totalRating = 0;
		let countRated = 0;

		Object.keys(scheduleData).forEach((className) => {
			if (
				scheduleData[className] &&
				scheduleData[className]["prof_weight"]
			) {
				totalRating += parseFloat(
					scheduleData[className]["prof_weight"],
				);
				countRated++;
			}
		});

		if (countRated === 0) return "N/A";
		return (totalRating / countRated).toFixed(2);
	}

	// Calculate the average rating when the component initializes
	const avgProfRating = calculateAverageRating();
</script>

<!-- Updated to ensure full width -->
<div class="schedule-wrapper">
	<div class="schedule-header">
		<!-- Updated schedule header -->
		<div class="schedule-info">
			<div class="schedule-number">
				<span class="schedule-badge">#{scheduleIndex + 1}</span>
				<h3>Schedule</h3>
			</div>
			<div class="rating-badge">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="16"
					height="16"
					viewBox="0 0 24 24"
					fill="currentColor"
					stroke="none"
				>
					<polygon
						points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"
					></polygon>
				</svg>
				<span class="rating-value">{avgProfRating}</span>
				<span class="rating-label">Avg. Professor Rating</span>
			</div>
		</div>
	</div>

	<!-- Redesigned container with CSS Grid for perfect alignment -->
	<div class="schedule-container">
		<!-- Time labels column with fixed dimensions -->
		<div class="time-labels" style="padding-top: {dayHeaderHeight}px;">
			{#each timeLabels as time, i}
				<div class="time-label" style="height: {hourHeight}px;">
					{time}
				</div>
			{/each}
		</div>

		<!-- Content area with days and schedule -->
		<div class="schedule-content">
			<!-- Day headers with fixed height -->
			<div class="day-headers" style="height: {dayHeaderHeight}px;">
				{#each dayNames as day, i}
					<div class="day-header">{day}</div>
				{/each}
			</div>

			<!-- Scrollable grid area with fixed height -->
			<div class="grid-area" style="height: {scheduleHeight}px;">
				<!-- Background grid lines -->
				<div class="grid-lines">
					{#each timeLabels as _, i}
						<div
							class="grid-line"
							style="height: {hourHeight}px;"
						></div>
					{/each}
				</div>

				<!-- Day columns with events -->
				<div class="day-columns">
					{#each daysCodes as day, i}
						<div class="schedule-column">
							{#each formatSlots(dayLabels[i] || []) as slot}
								<!-- Fix: Calculate detail level for each slot -->
								{@const detailLevel = shouldShowDetails(
									slot.heightPixels,
								)}
								<!-- Schedule slot with absolute positioning -->
								<!-- svelte-ignore a11y-click-events-have-key-events -->
								<!-- svelte-ignore a11y-no-static-element-interactions -->
								<div
									class="schedule-slot"
									style="
										top: {slot.startPixels}px; 
										height: {slot.heightPixels}px; 
										background: {colorMap.get(slot.class) || '#f0f0f0'};
										{slot.horizontalPosition !== undefined
										? `left: calc(${slot.horizontalPosition * (100 / slot.totalOverlap)}%); 
												width: calc(${100 / slot.totalOverlap}%);`
										: 'left: 0; right: 0;'}
									"
									on:click={() =>
										openSectionDetails(
											slot.class,
											`${slot.class}-${slot.sectionCode}`,
										)}
								>
									<div class="slot-content">
										<!-- Detail level 0: Very small slots - stack class and time -->
										{#if detailLevel === 0}
											<div class="horizontal-info">
												<span class="class-name"
													>{slot.class}</span
												>
												<span class="mini-time"
													>{slot.startTime.replace(
														":00",
														"",
													)}</span
												>
											</div>

											<!-- Detail level 1: Small slots - stack horizontally -->
										{:else if detailLevel === 1}
											<div class="class-row">
												<span class="class-name"
													>{slot.class}</span
												>
												<span class="section-number"
													>§{slot.sectionCode}</span
												>
											</div>
											<div class="info-row">
												<span class="slot-location"
													>{slot.location.split(
														" ",
													)[0]}</span
												>
												<span class="slot-time"
													>{slot.startTime.replace(
														":00",
														"",
													)}-{slot.endTime.replace(
														":00",
														"",
													)}</span
												>
											</div>

											<!-- Detail level 2: Medium slots - more horizontal stacking -->
										{:else if detailLevel === 2}
											<div class="class-row">
												<span class="class-name"
													>{slot.class}</span
												>
												<span class="section-number"
													>§{slot.sectionCode}</span
												>
											</div>
											<div class="info-row">
												<span class="slot-location"
													>{slot.location}</span
												>
											</div>
											<div class="info-row">
												<span class="slot-time"
													>{slot.startTime.replace(
														":00",
														"",
													)}-{slot.endTime.replace(
														":00",
														"",
													)}</span
												>
											</div>

											<!-- Detail level 3: Large slots - optimal layout with horizontal elements -->
										{:else}
											<div class="class-row">
												<span class="class-name"
													>{slot.class}</span
												>
												<span class="section-number"
													>§{slot.sectionCode}</span
												>
											</div>
											<div class="info-row">
												<span class="slot-location"
													>{slot.location}</span
												>
											</div>
											<div class="info-row">
												<span class="slot-time"
													>{slot.startTime}-{slot.endTime}</span
												>
											</div>
										{/if}
									</div>

									<!-- Show tooltip on hover for all slots, regardless of size -->
									<div class="slot-tooltip">
										<div>
											<strong>{slot.class}</strong>
											Section {slot.sectionCode}
										</div>
										<div>
											{slot.startTime} - {slot.endTime}
										</div>
										<div>{slot.location}</div>
										<div>
											{slot.professor}
											{#if slot.prof_rating}
												({Number(
													slot.prof_rating,
												).toFixed(1)} ⭐)
											{/if}
										</div>
									</div>
								</div>
							{/each}
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>
</div>

{#if showSectionModal}
	<SectionDetailModal
		showModal={showSectionModal}
		sectionId={selectedSectionId}
		courseId={selectedCourseId}
		on:close={closeSectionModal}
	/>
{/if}

<style>
	.schedule-wrapper {
		width: 100%;
		margin: 0 0 2rem 0;
		overflow-x: auto; /* Allow horizontal scroll only within this component if needed */
	}

	/* Container uses CSS Grid for precise alignment */
	.schedule-container {
		display: grid;
		grid-template-columns: 80px 1fr;
		grid-template-rows: auto;
		width: 100%;
		min-width: 600px; /* Minimum width to prevent squishing */
		max-width: 100%;
		margin: 0 0 40px 0;
		border-radius: 8px;
		overflow: hidden;
		box-shadow: var(--shadow-sm);
		box-sizing: border-box;
		border-top-left-radius: 0;
		border-top-right-radius: 0;
	}

	/* Time labels column with exact alignment */
	.time-labels {
		position: relative;
		display: flex;
		flex-direction: column;
		background-color: #f9f9f9;
		border-right: 1px solid #eaeaea;
		z-index: 2;
		box-sizing: border-box;
		padding: 0; /* Remove padding */
	}

	.time-label {
		display: flex;
		align-items: flex-start; /* Align to top */
		justify-content: center;
		font-size: 0.8rem;
		color: #666;
		border-bottom: 1px solid #eaeaea;
		box-sizing: border-box;
		position: relative;
		text-align: center;
		padding-top: 4px; /* Small top padding */
	}

	/* Schedule content area containing days and grid */
	.schedule-content {
		display: flex;
		flex-direction: column;
		position: relative;
		width: 100%;
	}

	/* Day headers with fixed height */
	.day-headers {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		background-color: #e21833;
		color: white;
		z-index: 2;
	}

	.day-header {
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: bold;
		border-right: 1px solid rgba(255, 255, 255, 0.2);
	}

	/* Grid area containing both lines and events */
	.grid-area {
		position: relative; /* Ensure content is laid out properly */
		width: 100%;
	}

	/* Grid lines with exact height matching time labels */
	.grid-lines {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		z-index: 0; /* Send these behind day-columns */
		pointer-events: none;
		display: flex;
		flex-direction: column;
	}

	.grid-line {
		width: 100%;
		border-bottom: 1px solid #eaeaea;
		box-sizing: border-box;
	}

	/* Day columns container uses CSS Grid for equal column widths */
	.day-columns {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		position: absolute; /* Position absolutely to align with grid lines */
		top: 0;
		width: 100%;
		height: 100%;
	}

	.schedule-column {
		position: relative;
		border-right: 1px solid #eaeaea;
		height: 100%;
	}

	/* Ensure slots are positioned precisely */
	.schedule-slot {
		position: absolute;
		border-radius: 6px;
		color: #333;
		padding: 4px;
		box-sizing: border-box;
		overflow: hidden;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
		transition: all 0.25s ease;
		z-index: 1;
	}

	.schedule-slot:hover {
		transform: scale(1.02);
		box-shadow: 0 5px 10px rgba(0, 0, 0, 0.15);
		z-index: 10;
	}

	.schedule-slot:hover .slot-tooltip {
		display: block;
	}

	.slot-content {
		height: 100%;
		width: 100%;
		padding: 4px;
		display: flex;
		flex-direction: column;
		/* gap: 2px; */
		overflow: hidden;
	}

	/* Class name is the only bold element */
	.class-name {
		font-weight: bold;
		font-size: 0.8rem;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	/* All other text is consistent weight and size */
	.section-number,
	.slot-location,
	.slot-time {
		font-weight: normal;
		font-size: 0.75rem;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		color: #333;
	}

	/* Remove any specific styling for different detail levels */

	.slot-tooltip {
		display: none;
		position: absolute;
		background: rgba(255, 255, 255, 0.95);
		border: 1px solid #ddd;
		border-radius: 6px;
		padding: 8px 12px;
		min-width: 200px;
		box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
		z-index: 1000;
		top: 0;
		left: 100%;
		font-size: 0.8rem;
		line-height: 1.5;
		color: #333;
	}

	/* Ensure tooltip stays visible and doesn't get cut off */
	.schedule-slot:hover .slot-tooltip {
		display: block;
	}

	/* For slots too far right, show tooltip on the left */
	.schedule-column:nth-child(4) .slot-tooltip,
	.schedule-column:nth-child(5) .slot-tooltip {
		left: auto;
		right: 100%;
	}

	/* Making the schedule more responsive */
	@media (min-width: 1200px) {
		.class-name {
			font-size: 0.95rem;
		}

		.section-number,
		.slot-location,
		.slot-time {
			font-size: 0.85rem;
		}
	}

	@media (max-width: 768px) {
		.class-name {
			font-size: 0.75rem;
		}

		.section-number,
		.slot-location,
		.slot-time {
			font-size: 0.7rem;
		}
	}

	/* Schedule header styling */
	.schedule-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--space-3) var(--space-4);
		background-color: white;
		border-top-left-radius: var(--radius-lg);
		border-top-right-radius: var(--radius-lg);
		border-bottom: 2px solid var(--primary);
		margin-bottom: -1px; /* Connect with schedule container */
	}

	.schedule-info {
		display: flex;
		justify-content: space-between;
		width: 100%;
		align-items: center;
	}

	.schedule-number {
		display: flex;
		align-items: center;
		gap: var(--space-2);
	}

	.schedule-number h3 {
		margin: 0;
		font-size: 1.125rem;
		font-weight: 600;
		color: var(--neutral-800);
	}

	.schedule-badge {
		background-color: var(--primary);
		color: white;
		border-radius: var(--radius-full);
		padding: var(--space-1) var(--space-2);
		font-size: 0.875rem;
		font-weight: 600;
		min-width: 24px;
		text-align: center;
	}

	.rating-badge {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		background-color: white;
		padding: var(--space-2) var(--space-3);
		border-radius: var(--radius-full);
		box-shadow: var(--shadow-sm);
		color: var(--neutral-600);
	}

	.rating-badge svg {
		color: #ffc107;
	}

	.rating-value {
		color: var(--neutral-900);
		font-weight: 600;
		font-size: 0.875rem;
	}

	.rating-label {
		color: var(--neutral-600);
		font-size: 0.75rem;
	}

	/* Improved slot content layout */
	.slot-content {
		height: 100%;
		width: 100%;
		padding: 4px;
		display: flex;
		flex-direction: column;
		gap: 2px;
		overflow: hidden;
	}

	/* Horizontal information layout */
	.horizontal-info {
		display: flex;
		justify-content: space-between;
		align-items: center;
		width: 100%;
		overflow: hidden;
	}

	.class-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		width: 100%;
		overflow: hidden;
	}

	.info-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		width: 100%;
		overflow: hidden;
		font-size: 0.75rem;
	}

	/* Class name is the only bold element */
	.class-name {
		font-weight: bold;
		font-size: 0.8rem;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		flex: 1;
	}

	.mini-time {
		font-size: 0.7rem;
		white-space: nowrap;
		margin-left: 4px;
	}

	/* Section number now positioned inline */
	.section-number {
		font-size: 0.7rem;
		opacity: 0.9;
		font-weight: normal;
		white-space: nowrap;
		padding-left: 4px;
		flex-shrink: 0;
	}

	/* All other text is consistent weight and size */
	.slot-location,
	.slot-time {
		font-weight: normal;
		font-size: 0.75rem;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.slot-location {
		flex: 1;
		text-align: left;
	}

	.slot-time {
		text-align: right;
		flex-shrink: 0;
		margin-left: 4px;
	}

	/* Make the schedule more responsive */
	@media (max-width: 768px) {
		.schedule-container {
			display: flex;
			flex-direction: column;
			width: 100%;
			overflow-x: auto; /* Allow horizontal scroll on narrow screens */
		}

		.time-labels {
			display: none; /* Hide on small screens to save space */
		}

		.schedule-content {
			min-width: 600px; /* Minimum width to ensure readability */
		}

		.schedule-wrapper {
			margin: 0 -16px; /* Negative margin to allow schedule to break out of container */
			padding: 0 16px; /* Add padding to compensate and maintain visual alignment */
			width: calc(100% + 32px); /* Compensate for negative margins */
		}

		/* ...other mobile styles... */
	}
</style>
