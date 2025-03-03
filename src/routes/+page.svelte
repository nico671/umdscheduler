<script lang="ts">
	// Call the function after the component has been mounted
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import ClassModal from '../components/ClassModal.svelte';
	import AddClassModal from '../components/AddClassModal.svelte';
	import TimeSelectionModal from '../components/TimeSelectionModal.svelte';
	import ProfessorModal from '../components/ProfessorModal.svelte';
	import ScheduleView from '../components/ScheduleView.svelte';

	let availableClasses = [] as string[];
	var addedClasses = [] as string[];

	let prohibitedTimes = [] as Map<string, string>[];
	let prohibitedProfessors: string[] = [];
	let generatedSchedules: any[] = [];
	let colorMap = new Map();
	let showTimeSelectionModal = false;
	let showAddClassModal = false;
	let generatingSchedules = false;

	let currentAmountLoaded = 0;

	let showClassModals = new Array(addedClasses.length).fill(false); // Initialize all modals as closed
	let showProfessorModals = new Array(prohibitedProfessors.length).fill(false);

	async function generateSchedules() {
		generatedSchedules = [];
		// schedules = [];

		currentAmountLoaded = 0;
		generatingSchedules = true;

		const url = new URL('http://127.0.0.1:5000/schedule');
		console.log(prohibitedTimes.map((map) => Object.fromEntries(map)));
		console.log(Array.from(prohibitedProfessors.values()).flatMap((profs) => profs));
		fetch(url, {
			method: 'POST',
			body: JSON.stringify({
				wanted_classes: addedClasses,
				restrictions: {
					minSeats: 1,
					prohibitedInstructors: Array.from(prohibitedProfessors.values()).flatMap(
						(profs) => profs
					),
					prohibitedTimes: prohibitedTimes.map((map) => Object.fromEntries(map)),
					required_classes: addedClasses
				}
			}),
			headers: {
				'Content-Type': 'application/json'
			}
		})
			.then((response) => response.json())
			.then((data) => {
				console.log(data[0]);
				console.log(data.length);
				// shuffle(data);
				generatedSchedules = data;
				schedules = [];
				addNewSchedules();
				// console.log(generatedSchedules);
			})
			.catch((error) => {
				console.log(error);
				return [];
			});
	}

	function removeProhibitedTime(time: number) {
		prohibitedTimes.splice(time, 1);
		prohibitedTimes = [...prohibitedTimes];
	}

	function prohibitProf(prof: string) {
		if (prohibitedProfessors.includes(prof)) {
			return;
		}
		prohibitedProfessors.push(prof);
		prohibitedProfessors = [...prohibitedProfessors];
		let idx = prohibitedProfessors.indexOf(prof);
		showProfessorModals[idx] = false;
		showProfessorModals = [...showProfessorModals];
	}

	function reAddProfessor(prof: string) {
		if (!prohibitedProfessors.includes(prof)) {
			return;
		}
		const index = prohibitedProfessors.indexOf(prof);
		prohibitedProfessors.splice(index, 1);
		prohibitedProfessors = [...prohibitedProfessors];
	}

	function closeClassModal(index: number) {
		showClassModals[index] = false;
		showClassModals = [...showClassModals];
	}

	function closeProfModal(index: number) {
		showProfessorModals[index] = false;
		showProfessorModals = [...showProfessorModals];
	}

	// function showProfModal(index: number) {
	// 	showProfessorModals[index] = true;
	// 	showProfessorModals = [...showProfessorModals];
	// }

	function removeClasses(value: string) {
		const index = addedClasses.indexOf(value);
		if (index !== -1) {
			addedClasses.splice(index, 1);
			addedClasses = [...addedClasses];
			showClassModals.splice(index, 1);
			availableClasses.push(value);
		}
	}

	onMount(async () => {
		const url = new URL('https://api.umd.io/v1/courses/list');
		url.searchParams.append('sort', 'sort=course_id,-credits');
		url.searchParams.append('semester', '202501');

		fetch(url)
			.then((response) => response.json())
			.then((data) => {
				availableClasses = data.map((item: any) => item.course_id);
				// console.log(availableClasses);
			})
			.catch((error) => {
				console.log(error);
				return [];
			});
		addNewSchedules();
		element = document.getElementById('schedules-scroll');
		if (element) {
			console.log('element found');
			element.addEventListener('scroll', checkScroll);
		} else {
			console.error('Element not found');
		}
	});
	let schedules: any[] = [];
	let element: HTMLElement | null;

	const addNewSchedules = () => {
		if (!Array.isArray(generatedSchedules)) {
			console.log(generatedSchedules);
			console.error('generatedSchedules is not an array');
			return;
		}
		if (currentAmountLoaded >= generatedSchedules.length) return;
		const newSchedules = generatedSchedules.slice(currentAmountLoaded, currentAmountLoaded + 10);
		currentAmountLoaded += 10;
		schedules = [...schedules, ...newSchedules];
	};

	const checkScroll = () => {
		if (element && element.scrollHeight - element.scrollTop <= element.clientHeight + 10) {
			addNewSchedules();
		}
	};

	onDestroy(() => {
		if (element) {
			element.removeEventListener('scroll', checkScroll);
		}
	});
</script>

<header>
	<div id="header-row">
		<h1 id="header-text">TerpScheduler</h1>
		<div id="header-button-rows">
			{#if addedClasses.length > 1}
				<button class="header-button" on:click={() => generateSchedules()}>Generate!</button>
			{/if}

			<button class="header-button" on:click={() => (showAddClassModal = true)}>Add Class</button>
			<AddClassModal
				bind:colorMap
				bind:showModals={showClassModals}
				bind:showAddClassModal
				bind:addedClasses
				bind:availableClasses
			></AddClassModal>
			<button class="header-button" on:click={() => (showTimeSelectionModal = true)}
				>Prohibit Time</button
			>
			<TimeSelectionModal bind:prohibitedTimes bind:showTimeSelectionModal></TimeSelectionModal>
		</div>
	</div>

	<div id="im-bad-at-css-holder-div">
		<div id="restrictions-container">
			<div class="restriction-box">
				<h2>Added Classes</h2>
				<div class="restriction-items">
					{#each addedClasses as className, index}
						<button
							style="background-color: {colorMap.get(className) ||
								'#64646443'}; border-color: {colorMap.get(className) || '#646464b2'}"
							class="restriction-button"
							on:click={() => (showClassModals[index] = true)}
						>
							{className}
						</button>
						<ClassModal
							bind:showModal={showClassModals[index]}
							{className}
							{removeClasses}
							{index}
							closeModal={closeClassModal}
							{prohibitProf}
							{prohibitedProfessors}
						></ClassModal>
					{/each}
				</div>
			</div>

			<div class="restriction-box">
				<h2>Prohibited Professors</h2>
				{#if prohibitedProfessors.length > 0}
					<div class="restriction-items">
						{#each prohibitedProfessors as prof, index}
							<button
								class="restriction-button"
								on:click={() => {
									console.log(prof);
									showProfessorModals[index] = true;
									showProfessorModals = [...showProfessorModals];
								}}>{prof}</button
							>
							<ProfessorModal
								bind:showModal={showProfessorModals[index]}
								{addedClasses}
								closeModal={closeProfModal}
								profName={prof}
								{reAddProfessor}
								{index}
							></ProfessorModal>
						{/each}
					</div>
				{/if}
			</div>

			<div class="restriction-box">
				<h2>Prohibited Times</h2>
				<div class="restriction-items">
					{#if prohibitedTimes.length > 0}
						{#each prohibitedTimes.entries() as [time, day]}
							<button
								class="restriction-button"
								on:click={() => {
									if (
										confirm(
											`Allow classes ${day.get('day')}: ${day.get('start')}-${day.get('end')}?`
										)
									) {
										removeProhibitedTime(time);
									}
								}}>{day.get('day')}: {day.get('start')}-{day.get('end')}</button
							>
						{/each}
					{/if}
				</div>
			</div>
		</div>
	</div>
</header>
<body bind:this={element}>
	{#if generatedSchedules.length > 0}
		<h2>{generatedSchedules.length} schedules generated!</h2>
	{/if}
	{#if generatedSchedules.length === 0}
		<div id="no-sched-div">
			{#if !generatingSchedules}
				<h1>
					Add at least 2 class and click the "Generate Schedules" button to generate schedules
				</h1>
			{:else}
				<div class="lds-dual-ring"></div>
			{/if}
			<!-- <h1>No schedules generated</h1> -->
		</div>
	{/if}
	{#each schedules.sort((a, b) => a['prof_weight'] - b['prof_weight']) as item, i}
		<h3>Schedule #{i + 1}</h3>
		<h4>Average Professor Rating - {item['prof_weight']}</h4>
		<ScheduleView {colorMap} scheduleData={item}></ScheduleView>
	{/each}
</body>

<style>
	header {
		font-family: 'Haas Grot Text R Web', 'Helvetica Neue', Helvetica, Arial, sans-serif;
		padding: 1vh;
		margin: 0px;
		width: 100vw;
		max-width: 98vw;
		height: 100%;
		position: sticky;
	}

	body {
		font-family: 'Haas Grot Text R Web', 'Helvetica Neue', Helvetica, Arial, sans-serif;
		padding: 1vh;
		margin: 0px;
		width: 100vw;
		max-width: 99vw;
		height: 100%;
		display: flex;
		flex-direction: column;
		height: fit-content;
		box-sizing: border-box;
		overflow-y: scroll;
		/* background-color: lightblue; */
	}

	h2 {
		padding-left: 0vh;
		padding-top: 1vh;
		margin: 0px;
	}

	#im-bad-at-css-holder-div {
		display: flex;
		flex-direction: column;
		justify-content: start;
		align-items: start;
		padding: 0px;
		margin: 0px;

		border-radius: 0px 0px 15px 15px;
	}

	.restriction-box {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		justify-content: flex-start;
		height: 15vh;
		max-height: 15vh;
		width: 30%;
		max-width: 30%;
		padding: 0px;
		margin: 0px;
		/* border: solid 3px #94727254; */
		border-radius: 15px;
		background-color: #f0f0f0;
	}

	#no-sched-div {
		display: flex;
		flex-direction: column;
		/* flex-basis: auto; */
		justify-content: center;
		align-items: center;
	}

	.lds-dual-ring,
	.lds-dual-ring:after {
		box-sizing: border-box;
	}
	.lds-dual-ring {
		display: inline-block;
		width: 80px;
		height: 80px;
	}
	.lds-dual-ring:after {
		content: ' ';
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
	}

	.restriction-button {
		background-color: #64646443;
		border: 2px solid #646464b2;
		border-radius: 25px;
		text-align: center;
		font-size: small;
		padding-left: 0.3vw;
		width: fit-content;
		height: 4vh;
		margin-right: 1vh;
	}

	.header-button {
		background-color: #f0f0f0;
		border-radius: 8px;
		border-width: 0;
		color: black;
		cursor: pointer;
		display: inline-block;
		font-family: 'Haas Grot Text R Web', 'Helvetica Neue', Helvetica, Arial, sans-serif;
		font-size: 1.5vw;
		font-weight: 500;
		line-height: 20px;
		list-style: none;
		padding: 1vw;
		/* margin: 1vw; */
		text-align: center;
		transition: all 200ms;
		vertical-align: baseline;
		white-space: nowrap;
		user-select: none;
		-webkit-user-select: none;
		touch-action: manipulation;
	}

	#restrictions-container {
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
	}

	:host {
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		/* padding: 1em; */
	}

	.restriction-items {
		width: fit-content;
		display: flex;
		flex-wrap: wrap;
		padding: 1vh;
		margin-bottom: 1vh;
		/* background-color: #64646443; */
		justify-content: flex-start;
	}
</style>
