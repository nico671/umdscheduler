<script>
	import { onMount, onDestroy } from 'svelte';
	import ScheduleView from './ScheduleView.svelte';
	export let generatedSchedules = [];
	export let addedClasses = [];
	export let colorMap;
</script>

<div class="schedules-container"></div>

<style lang="scss">
	.schedules-container {
		display: flex;
		flex-direction: column;
		width: 95%;
		height: 100%;
		margin: 0px;
		padding: 0px;
		// max-width: 95%;
	}
	#schedules-scroll {
		margin: 0px;
		padding: 0px;
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

	h4 {
		margin: 0;
		padding: 0;
	}
	h3 {
		margin: 0;
		padding: 0;
	}
	h2 {
		margin-top: 0;
		padding-top: 0;
	}
</style>
