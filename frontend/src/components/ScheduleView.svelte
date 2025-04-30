<script lang="ts">
	import { onMount } from "svelte";
	import SectionDetailModal from "./SectionDetailModal.svelte";
	import "../components/styles/schedule-view-styles.css";
	let dayLabels: any[][] = [[], [], [], [], []];
	let daysCodes = ["M", "Tu", "W", "Th", "F"];
	let dayNames = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

	export let colorMap: Map<string, string> = new Map<string, string>();
	export let scheduleData: any;
	export let scheduleIndex: number = 0;

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

<div class="schedule-wrapper">
	<div class="schedule-header">
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
							style="top: {i *
								hourHeight}px; height: {hourHeight}px;"
						></div>
					{/each}
				</div>

				<!-- Day columns with events -->
				<div class="day-columns">
					{#each daysCodes as day, i}
						<div class="schedule-column">
							{#each formatSlots(dayLabels[i] || []) as slot}
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
										<!-- Consistent layout for all slots -->
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
									</div>

									<!-- Show tooltip on hover for all slots, regardless of size -->
									<div
										class="slot-tooltip"
										style="
											background: {colorMap.get(slot.class) || '#f0f0f0'};
											border-color: {colorMap.get(slot.class)
											? 'rgba(0, 0, 0, 0.1)'
											: 'rgba(0, 0, 0, 0.1)'};
										"
									>
										<div class="tooltip-professor">
											{slot.professor}
											{#if slot.prof_rating}
												<span class="tooltip-rating"
													>({Number(
														slot.prof_rating,
													).toFixed(1)} ⭐)</span
												>
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

<!-- <style>
	
</style> -->
