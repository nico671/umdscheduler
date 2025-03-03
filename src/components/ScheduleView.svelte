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
	let earliestStart = 480; // 8:00 AM in minutes from midnight
	let latestEnd = 1200; // 8:00 PM in minutes from midnight
	let totalLength = latestEnd - earliestStart;
	let scheduleHeight = 800; // Overall height of the schedule container

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

					const { startSlot, length } = calculateSlotTimes(
						startDate,
						endDate,
					);

					daysCodes.forEach((dayCode, k) => {
						if (days.includes(dayCode)) {
							const slot = {
								sectionCode: scheduleData[element]["number"],
								days: dayCode,
								start: startSlot, // percentage
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
								length: length, // percentage
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

		// Calculate percentage values with respect to grid dimensions
		const startSlot = ((startMinutes - earliestStart) / totalLength) * 100;
		const length = ((endMinutes - startMinutes) / totalLength) * 100;

		return { startSlot, length };
	};

	function formatSlots(day: any[]) {
		return day.sort((a, b) => a.start - b.start);
	}

	// Update the detail levels to always include time and location
	function shouldShowDetails(length: number) {
		// For very small slots (less than 30 minutes)
		if (length < 4) return 0;
		// For small slots (30-45 minutes)
		if (length < 8) return 1;
		// For medium slots (45-75 minutes)
		if (length < 12) return 2;
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

<!-- Add a header above the schedule container -->
<div class="schedule-header">
	<div class="schedule-info">
		<h3 class="schedule-number">Schedule #{scheduleIndex + 1}</h3>
		<div class="rating-badge">
			<span class="rating-label">Avg. Professor Rating:</span>
			<span class="rating-value">{avgProfRating} ⭐</span>
		</div>
	</div>
</div>

<div class="schedule-container" style="height: {scheduleHeight}px;">
	<!-- Time labels column - ensure exact height matching grid lines -->
	<div class="time-labels">
		{#each timeLabels as time, i}
			<div class="time-label" style="height: {hourHeight}px;">
				{time}
			</div>
		{/each}
	</div>

	<!-- Grid container -->
	<div class="grid-container">
		<!-- Day headers -->
		<div class="day-headers">
			{#each dayNames as day, i}
				<div class="day-header">{day}</div>
			{/each}
		</div>

		<!-- Schedule grid with column grid lines -->
		<div class="schedule-grid">
			<!-- Time grid lines - explicit height matching time labels -->
			<div class="grid-lines">
				{#each timeLabels as time, i}
					<div
						class="grid-line"
						style="height: {hourHeight}px;"
					></div>
				{/each}
			</div>

			<!-- Day columns -->
			{#each daysCodes as day, i}
				<div class="schedule-column">
					<!-- svelte-ignore a11y-no-static-element-interactions -->
					{#each formatSlots(dayLabels[i] || []) as slot}
						{@const detailLevel = shouldShowDetails(slot.length)}
						<!-- svelte-ignore a11y-click-events-have-key-events -->
						<div
							class="schedule-slot"
							style="
								top: {slot.start}%; 
								height: {slot.length}%; 
								background: {colorMap.get(slot.class) || '#f0f0f0'};
								{slot.horizontalPosition !== undefined
								? `left: ${slot.horizontalPosition * (100 / slot.totalOverlap)}%; 
									 width: ${100 / slot.totalOverlap}%;`
								: 'left: 2px; right: 2px;'}
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
											>{slot.location.split(" ")[0]}</span
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
									<strong>{slot.class}</strong> Section {slot.sectionCode}
								</div>
								<div>{slot.startTime} - {slot.endTime}</div>
								<div>{slot.location}</div>
								<div>
									{slot.professor}
									{#if slot.prof_rating}
										({Number(slot.prof_rating).toFixed(1)} ⭐)
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

{#if showSectionModal}
	<SectionDetailModal
		showModal={showSectionModal}
		sectionId={selectedSectionId}
		courseId={selectedCourseId}
		on:close={closeSectionModal}
	/>
{/if}

<style>
	.schedule-container {
		display: flex;
		width: 100%;
		max-width: 100%;
		/* Height is now controlled by the scheduleHeight variable */
		margin-bottom: 40px;
		border-radius: 8px;
		overflow: hidden;
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
		box-sizing: border-box;
		border-top-left-radius: 0;
		border-top-right-radius: 0;
		position: relative; /* Add this for better positioning context */
	}

	.time-labels {
		width: 80px;
		display: flex;
		flex-direction: column;
		padding-top: 50px; /* Match the day-headers height exactly */
		background-color: #f9f9f9;
		border-right: 1px solid #eaeaea;
		z-index: 2; /* Keep time labels above grid for visual clarity */
	}

	.time-label {
		/* height: 60px; - Now set via inline style for exact matching */
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.8rem;
		color: #666;
		border-bottom: 1px dashed #eaeaea;
		box-sizing: border-box; /* Ensure border is included in height calculation */
	}

	.grid-container {
		flex: 1;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		min-width: 0; /* Allow shrinking below content size if needed */
	}

	.day-headers {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		height: 50px; /* Fixed height to match padding-top of time-labels */
		background-color: #e21833;
		color: white;
		z-index: 2; /* Keep headers above grid */
	}

	.day-header {
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: bold;
		border-right: 1px solid rgba(255, 255, 255, 0.2);
	}

	.day-header:last-child {
		border-right: none;
	}

	.schedule-grid {
		position: relative;
		flex: 1;
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		overflow: hidden;
	}

	.grid-lines {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		z-index: 0;
		pointer-events: none;
	}

	.grid-line {
		position: relative;
		/* height: 60px; - Now set via inline style for exact matching */
		border-bottom: 1px dashed #eaeaea;
		box-sizing: border-box; /* Ensure border is included in height calculation */
	}

	.schedule-column {
		position: relative;
		border-right: 1px solid #eaeaea;
		height: 100%;
	}

	.schedule-column:last-child {
		border-right: none;
	}

	.schedule-slot {
		position: absolute;
		left: 2px;
		right: 2px;
		border-radius: 6px;
		color: #333;
		padding: 4px;
		box-sizing: border-box;
		overflow: hidden;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
		transition: all 0.25s ease;
		z-index: 1;
		/* No need for any additional margins that might throw off alignment */
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
		gap: 2px;
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
		padding: 12px 16px;
		background-color: #f8f8f8;
		border-top-left-radius: 8px;
		border-top-right-radius: 8px;
		border-bottom: 2px solid #e21833;
		margin-bottom: -1px; /* Connect with schedule container */
	}

	.schedule-info {
		display: flex;
		justify-content: space-between;
		width: 100%;
		align-items: center;
	}

	.schedule-number {
		margin: 0;
		color: #333;
		font-size: 1.2rem;
		font-weight: 600;
	}

	.rating-badge {
		display: flex;
		align-items: center;
		gap: 8px;
		background-color: white;
		padding: 6px 12px;
		border-radius: 20px;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}

	.rating-label {
		color: #666;
		font-size: 0.9rem;
	}

	.rating-value {
		color: #e21833;
		font-weight: bold;
		font-size: 1rem;
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
</style>
