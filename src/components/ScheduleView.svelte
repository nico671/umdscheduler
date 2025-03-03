<script lang="ts">
	import { onMount } from "svelte";
	let dayLabels: any[][] = [[], [], [], [], []];
	let daysCodes = ["M", "Tu", "W", "Th", "F"];
	let dayNames = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

	export let colorMap: Map<string, string> = new Map<string, string>();
	export let scheduleData: any;

	let earliestStart = 480; // 8:00 AM in minutes
	let latestEnd = 1200; // 8:00 PM in minutes
	let totalLength = latestEnd - earliestStart;

	// Generate time labels for the schedule
	let timeLabels: string[] = [];
	for (let i = earliestStart; i <= latestEnd; i += 60) {
		const hour = Math.floor(i / 60);
		const meridiem = hour >= 12 ? "PM" : "AM";
		const displayHour = hour > 12 ? hour - 12 : hour === 0 ? 12 : hour;
		timeLabels.push(`${displayHour}:00 ${meridiem}`);
	}

	let scheduleHeight = 800; // Increased from 700px

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

	const calculateSlotTimes = (startDate: Date, endDate: Date) => {
		const startMinutes = startDate.getHours() * 60 + startDate.getMinutes();
		const endMinutes = endDate.getHours() * 60 + endDate.getMinutes();
		const startSlot = ((startMinutes - earliestStart) / totalLength) * 100;
		const length = ((endMinutes - startMinutes) / totalLength) * 100;
		return { startSlot, length };
	};

	function formatSlots(day: any[]) {
		return day.sort((a, b) => a.start - b.start);
	}

	function shouldShowDetails(length: number) {
		// For very small slots, we'll only show class name (less than 30 minutes)
		if (length < 4) return 0;
		// For small slots (30-45 minutes), show compact info
		if (length < 8) return 1;
		// For medium slots (45-75 minutes), show more info
		if (length < 12) return 2;
		// For large slots (75+ minutes), show all details
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
</script>

<div class="schedule-container" style="height: {scheduleHeight}px;">
	<!-- Time labels column -->
	<div class="time-labels">
		{#each timeLabels as time}
			<div class="time-label">{time}</div>
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
			<!-- Time grid lines -->
			<div class="grid-lines">
				{#each timeLabels as time}
					<div class="grid-line"></div>
				{/each}
			</div>

			<!-- Day columns -->
			{#each daysCodes as day, i}
				<div class="schedule-column">
					{#each formatSlots(dayLabels[i] || []) as slot}
						{@const detailLevel = shouldShowDetails(slot.length)}
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
						>
							<div class="slot-content">
								<!-- Detail level 0: Very small slots -->
								{#if detailLevel === 0}
									<div class="slot-header slot-header-mini">
										{slot.class}
									</div>
									<!-- Detail level 1: Small slots (compact horizontal layout) -->
								{:else if detailLevel === 1}
									<div class="slot-header compact">
										<span class="class-name"
											>{slot.class}</span
										>
									</div>
									<div class="compact-info">
										<span class="time-compact"
											>{slot.startTime.replace(
												":00",
												"",
											)}-{slot.endTime.replace(
												":00",
												"",
											)}</span
										>
										<span class="section-compact"
											>§{slot.sectionCode}</span
										>
									</div>
									<!-- Detail level 2: Medium slots -->
								{:else if detailLevel === 2}
									<div class="slot-header">
										<span class="class-name"
											>{slot.class}</span
										>
										<span class="section-number"
											>§{slot.sectionCode}</span
										>
									</div>
									<!-- Combined time and location in one row -->
									<div class="combined-row">
										<span>{slot.location}</span>
										<span
											>{slot.startTime.replace(
												":00",
												"",
											)}-{slot.endTime.replace(
												":00",
												"",
											)}</span
										>
									</div>
									<!-- Professor name only (no rating) -->
									<div class="slot-professor">
										{formatProfName(slot.professor)}
									</div>
									<!-- Detail level 3: Full details for large slots -->
								{:else}
									<div class="slot-header">
										<span class="class-name"
											>{slot.class}</span
										>
										<span class="section-number"
											>§{slot.sectionCode}</span
										>
									</div>

									<div class="slot-time">
										{slot.startTime} - {slot.endTime}
									</div>

									<div class="slot-location">
										{slot.location}
									</div>

									<div class="slot-professor">
										<span class="prof-name"
											>{slot.professor}</span
										>
										{#if slot.prof_rating}
											<span class="slot-rating">
												{Number(
													slot.prof_rating,
												).toFixed(1)} ⭐
											</span>
										{/if}
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
	}

	.time-labels {
		width: 80px;
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		padding-top: 50px; /* Match the day-headers height */
		background-color: #f9f9f9;
		border-right: 1px solid #eaeaea;
	}

	.time-label {
		height: 60px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.8rem;
		color: #666;
		border-bottom: 1px dashed #eaeaea;
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
		height: 50px;
		background-color: #e21833;
		color: white;
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
		height: 60px;
		border-bottom: 1px dashed #eaeaea;
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
		padding: 1px;
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
		justify-content: space-between;
		font-size: 0.8rem;
		overflow: hidden;
	}

	.slot-header {
		font-weight: bold;
		font-size: 0.9rem;
		margin-bottom: 2px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		overflow: hidden;
	}

	.slot-header-mini {
		justify-content: center;
		text-align: center;
		font-size: 0.65rem;
		font-weight: bold;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		padding: 1px;
		line-height: 1.1;
		height: 100%;
		display: flex;
		align-items: center;
	}

	.class-name {
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		flex: 1;
	}

	.section-number {
		font-size: 0.7rem;
		opacity: 0.9;
		font-weight: normal;
		padding-left: 4px;
		white-space: nowrap;
	}

	.slot-location,
	.slot-professor,
	.slot-time {
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		font-size: 0.75rem;
		line-height: 1.3;
	}

	.slot-time {
		font-weight: 500;
	}

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
		.slot-content {
			font-size: 0.85rem;
			padding: 10px;
		}

		.slot-header {
			font-size: 1rem;
		}
	}

	@media (max-width: 768px) {
		.schedule-container {
			height: 650px;
		}

		.time-labels {
			width: 50px;
		}

		.time-label {
			font-size: 0.65rem;
		}

		.slot-content {
			padding: 3px;
			font-size: 0.65rem;
		}

		.slot-header {
			font-size: 0.75rem;
			margin-bottom: 1px;
		}
	}

	/* For compact displays */
	.compact {
		margin-bottom: 0;
	}

	.compact-info {
		display: flex;
		justify-content: space-between;
		font-size: 0.65rem;
		white-space: nowrap;
		overflow: hidden;
	}

	.time-compact {
		font-weight: 500;
	}

	.section-compact {
		opacity: 0.8;
	}

	/* Combined row for medium slots */
	.combined-row {
		display: flex;
		justify-content: space-between;
		font-size: 0.7rem;
		white-space: nowrap;
		overflow: hidden;
	}

	.combined-row span {
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.combined-row span:first-child {
		max-width: 60%;
		text-align: left;
	}

	.combined-row span:last-child {
		text-align: right;
	}
</style>
