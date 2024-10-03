<script lang="ts">
	import { onMount } from 'svelte';
	let dayLabels = new Map<number, any[]>();
	dayLabels.set(0, []);
	dayLabels.set(1, []);
	dayLabels.set(2, []);
	dayLabels.set(3, []);
	dayLabels.set(4, []);
	let daysCodes = ['M', 'Tu', 'W', 'Th', 'F'];

	export let colorMap: Map<string, string> = new Map<string, string>();
	export let scheduleData: any;
	let classes: Map<string, any> = new Map<string, any>();
	export let addedClasses: string[] = [];
	var offsetDate = new Date();
	offsetDate.setHours(8);
	offsetDate.setMinutes(0);
	offsetDate.setDate(26);
	offsetDate.setFullYear(2018);
	offsetDate.setMonth(11);
	offsetDate.setSeconds(0);
	let totalLength = 0; // The height of the schedule view in vh
	let latestEnd = 0; // The end time of the latest slot in minutes (12 hours * 60 minutes)
	let earliestStart = 100000;
	onMount(async () => {
		// console.log(scheduleData);
		// Utility functions
		const createDate = (dateStr: string) => {
			// console.log(dateStr)
			let parts = dateStr.split(':');
			let date = new Date();
			date.setDate(26);
			date.setFullYear(2018);
			date.setMonth(11);
			let hours = parseInt(parts[0]);
			if (dateStr.includes('pm') && hours !== 12) {
				hours += 12;
			}
			date.setHours(hours);
			date.setMinutes(parseInt(parts[1]));
			date.setSeconds(0);
			return date;
		};

		const getFormattedTime = (date: number | Date | undefined) => {
			// console.log(date);
			return Intl.DateTimeFormat('en-US', { timeStyle: 'short' }).format(date);
		};

		const calculateSlotTimes = (startDate: Date, endDate: Date) => {
			const startSlot = Math.round((startDate.getTime() - offsetDate.getTime()) / 60000);
			const endSlot = Math.round((endDate.getTime() - offsetDate.getTime()) / 60000);
			// console.log(startSlot, startDate);
			if (startSlot < earliestStart) {
				earliestStart = startSlot;
			}
			if (endSlot > latestEnd) {
				latestEnd = endSlot;
			}
			return { startSlot, length: endSlot - startSlot };
		};

		// Main processing
		addedClasses.forEach((element) => {
			scheduleData[element]['meetings'].forEach(
				(classTime: {
					days: { toString: () => any };
					start_time: any;
					end_time: any;
					building: any;
					room: any;
				}) => {
					const days = classTime.days.toString();
					const startDate = createDate(classTime.start_time);
					const endDate = createDate(classTime.end_time);

					const { startSlot, length } = calculateSlotTimes(startDate, endDate);

					daysCodes.forEach((dayCode, k) => {
						if (days.toLowerCase().includes(dayCode.toLowerCase())) {
							const slot = {
								sectionCode: scheduleData[element]['number'],
								days: dayCode,
								start: startSlot,
								startTime: getFormattedTime(startDate),
								endTime: getFormattedTime(endDate),
								class: element,
								professor: scheduleData[element]['instructors'].toString(),
								location: `${classTime.building} ${classTime.room}`,
								prof_rating: scheduleData[element]['prof_weight'],
								// time: getTime(startSlot),
								length: length
							};

							if (!dayLabels.has(k)) {
								dayLabels.set(k, []);
							}
							dayLabels.get(k)!.push(slot);
						}
					});
				}
			);
		});
		totalLength = latestEnd - earliestStart;
		dayLabels = new Map([...dayLabels.entries()].sort());
	});

	function formatSlots(day: any[]) {
		day = day.sort((a, b) => a.start - b.start);
		return day;
	}
</script>

<!-- TODO: need to fix schedule generation frontend -->
<div class="grid-container">
	{#each new Map([...dayLabels.entries()].sort()).values() as day, i}
		<div class="schedule-column">
			{#each formatSlots(day) as slot, j}
				<div
					class="schedule-slot"
					style="top: {slot.start - earliestStart}px; height: {slot.length /
						totalLength}px; background:{colorMap.get(slot.class)};"
				>
					{slot.class} ({slot.sectionCode}) - {slot.location}
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
		grid-template-columns: repeat(5, 1fr);
		width: 100%;
		height: 65vh;
		/* height: fit-content; */
		border: 4px solid #000000;
		align-items: stretch;
	}

	.schedule-column {
		flex: 1;
		position: relative;
		justify-content: center;
		/* align-items: stretch; */
		height: 100%;
		margin-left: 0.5vh;
		margin-right: 0.5vh;
	}

	.schedule-slot {
		/* font-size: smaller; */
		float: none;
		position: absolute;
		text-align: center;
		/* margin: 1vh; */
		width: 100%;
		/* padding: 1vh; */
		border-radius: 3%;
		/* padding: 1%; */
		/* font-size: 1.5vh; */
	}
</style>
