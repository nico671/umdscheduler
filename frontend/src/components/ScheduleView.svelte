<script lang="ts">
	import { onMount } from 'svelte';
	let dayLabels: any[][] = [[], [], [], [], []];
	let daysCodes = ['M', 'Tu', 'W', 'Th', 'F'];

	export let colorMap: Map<string, string> = new Map<string, string>();
	export let scheduleData: any;

	let earliestStart = 480; // 8:00 AM in minutes
	let latestEnd = 1200; // 8:00 PM in minutes
	let totalLength = latestEnd - earliestStart;
	let offsetDate = new Date();
	offsetDate.setHours(8, 0, 0, 0); // Set offsetDate to 8:00 AM

	onMount(() => {
		// Process schedule data
		Object.keys(scheduleData).forEach((element) => {
			const meetings = scheduleData[element]?.meetings;
			if (meetings) {
				meetings.forEach((classTime: any) => {
					const days = classTime.days.toString();
					const startDate = createDate(classTime.start_time);
					const endDate = createDate(classTime.end_time);

					const { startSlot, length } = calculateSlotTimes(startDate, endDate);

					daysCodes.forEach((dayCode, k) => {
						if (days.includes(dayCode)) {
							const slot = {
								sectionCode: scheduleData[element]['number'],
								days: dayCode,
								start: startSlot, // percentage
								startTime: getFormattedTime(startDate),
								endTime: getFormattedTime(endDate),
								class: element,
								professor: scheduleData[element]['instructors'].toString(),
								location: `${classTime.building} ${classTime.room}`,
								prof_rating: scheduleData[element]['prof_weight'],
								length: length // percentage
							};
							dayLabels[k].push(slot);
						}
					});
				});
			}
		});

		console.log('Final dayLabels:', dayLabels);

		// Trigger reactivity by reassigning dayLabels
		dayLabels = [...dayLabels];
	});

	const createDate = (dateStr: string) => {
		let parts = dateStr.split(':');
		let date = new Date();
		let hours = parseInt(parts[0]);
		if (dateStr.includes('pm') && hours !== 12) {
			hours += 12;
		}
		date.setHours(hours);
		date.setMinutes(parseInt(parts[1]));
		date.setSeconds(0);
		return date;
	};

	const getFormattedTime = (date: Date) => {
		return Intl.DateTimeFormat('en-US', { timeStyle: 'short' }).format(date);
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
</script>

<div class="grid-container">
	{#each daysCodes as day, i}
		<div class="schedule-column">
			<div class="day-label">{day}</div>
			{#each formatSlots(dayLabels[i] || []) as slot}
				<div
					class="schedule-slot"
					style="top: {slot.start}%; height: {slot.length}%; background: {colorMap.get(
						slot.class
					) || '#ccc'};"
				>
					<b>{slot.class}</b> - Section {slot.sectionCode} - {slot.location}
					<br />
					{slot.professor} - {slot.prof_rating} ✪
					<br />
					{slot.startTime} - {slot.endTime}
				</div>
			{/each}
		</div>
	{/each}
</div>

<style>
	.grid-container {
		display: grid;
		grid-template-columns: repeat(5, 1fr); /* Make all day columns equal size */
		width: 100%;
		height: 100vh;
		border: 4px solid #000000;
	}

	.schedule-column {
		position: relative;
		border: 1px solid #ccc;
		height: 100%; /* Ensure it fills the grid container */
	}

	.day-label {
		text-align: center;
		font-weight: bold;
		padding: 5px 0;
	}

	.schedule-slot {
		height: 100%;
		position: absolute;
		left: 1%;
		width: 98%;
		/* border: 1px solid #000; */
		color: #000;
		padding: 2px;
		box-sizing: border-box;
		overflow: hidden;
		border-radius: 4px;
		font-size: 0.8em;
	}
</style>
