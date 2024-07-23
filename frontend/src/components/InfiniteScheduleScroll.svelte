<script>
	import { onMount, onDestroy } from 'svelte';
	import ScheduleView from './ScheduleView.svelte';
	export let generatedSchedules = [];
	export let addedClasses = [];
	export let colorMap;
	let currentAmountLoaded = 0;
	let schedules = [];
	let element;

	const addNewSchedules = () => {
		if (currentAmountLoaded >= generatedSchedules.length) return;
		const newSchedules = generatedSchedules.slice(currentAmountLoaded, currentAmountLoaded + 10);
		currentAmountLoaded += 10;
		schedules = [...schedules, ...newSchedules];
	};

	const checkScroll = () => {
		if (element.scrollHeight - element.scrollTop <= element.clientHeight + 10) {
			addNewSchedules();
		}
	};

	onMount(() => {
		console.log('mounted');
		addNewSchedules();
		element = document.getElementById('schedules-scroll');
		if (element) {
			console.log('element found');
			element.addEventListener('scroll', checkScroll);
		} else {
			console.error('Element not found');
		}
	});

	onDestroy(() => {
		if (element) {
			element.removeEventListener('scroll', checkScroll);
		}
	});

	$: {
		if (generatedSchedules.length === 0) {
			console.log('schedules reset');
			currentAmountLoaded = 0;
			schedules = [];
		}
	}
</script>

<div class="schedules-container">
	<ul id="schedules-scroll" bind:this={element}>
		{#if generatedSchedules.length}
			<p>{generatedSchedules.length} schedules generated!</p>
		{/if}
		{#each schedules as item, i}
			<h3>Schedule #{i + 1}</h3>
			<ScheduleView bind:scheduleData={item} {addedClasses} {colorMap}></ScheduleView>
		{/each}
	</ul>
</div>

<style lang="scss">

	.schedules-container{
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		width: 100%;
		// max-width: 95%;
		
	}
	#schedules-scroll {
		margin:0;
		padding:1vw;
		box-sizing: border-box;
		overflow-y: scroll;
		height: 80vh;
		width: 100%;
		&::-webkit-scrollbar {
			display: none;

			/* Hide scrollbar for IE, Edge and Firefox */
			scrollbar-width: none; /* Firefox */
			-ms-overflow-style: none;
		}
	}
</style>
