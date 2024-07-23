<script lang="ts">
	export let prohibitedTimes = [] as Map<string, string>[];
	let dialog: HTMLDialogElement;
	export let showTimeSelectionModal: boolean;
	function appendAMPM(value: string) {
		// console.log(value)//;
		var timeSplit = value.split(':');
		var hours = parseInt(timeSplit[0]);
		var minutes = timeSplit[1];
		var meridian = '';
		if (hours > 12) {
			meridian = 'pm';
			hours -= 12;
		} else if (hours < 12) {
			meridian = 'am';
			if (hours == 0) {
				hours = 12;
			}
		} else {
			meridian = 'pm';
		}
		return hours + ':' + minutes + meridian;
	}

	function addTime() {
		let startElement = document.getElementById('start-time') as HTMLInputElement;
		let endElement = document.getElementById('end-time') as HTMLInputElement;
		let start = startElement ? startElement.value : '';
		let end = endElement ? endElement.value : '';
		start = appendAMPM(start);
		end = appendAMPM(end);
		let days = [];
		if ((document.getElementById('monday') as HTMLInputElement)?.checked) {
			days.push('M');
		}
		if ((document.getElementById('tuesday') as HTMLInputElement)?.checked) {
			days.push('Tu');
		}
		if ((document.getElementById('wednesday') as HTMLInputElement)?.checked) {
			days.push('W');
		}
		if ((document.getElementById('thursday') as HTMLInputElement)?.checked) {
			days.push('Th');
		}
		if ((document.getElementById('friday') as HTMLInputElement)?.checked) {
			days.push('F');
		}
		for (let i = 0; i < days.length; i++) {
			var tempMap = new Map<string, string>();
			tempMap.set('start', start);
			tempMap.set('end', end);
			tempMap.set('day', days[i]);
			// console.log(tempMap);
			if (prohibitedTimes == undefined) {
				prohibitedTimes = [];
			}

			let tempMapStr = JSON.stringify(Array.from(tempMap.entries()));
			let prohibitedTimesStr = prohibitedTimes.map((timeBlock) =>
				JSON.stringify(Array.from(timeBlock.entries()))
			);

			if (!prohibitedTimesStr.includes(tempMapStr)) {
				// prohibitedTimes.push(tempMap);
				prohibitedTimes = [...prohibitedTimes, tempMap];
			}

			// force reset prohibitedTimes
			prohibitedTimes = [...prohibitedTimes];
			console.log(prohibitedTimes);
		}

		// reset values of all inputs
		startElement.value = '08:00';
		endElement.value = '08:01';
		(document.getElementById('monday') as HTMLInputElement).checked = false;
		(document.getElementById('tuesday') as HTMLInputElement).checked = false;
		(document.getElementById('wednesday') as HTMLInputElement).checked = false;
		(document.getElementById('thursday') as HTMLInputElement).checked = false;
		(document.getElementById('friday') as HTMLInputElement).checked = false;
		showTimeSelectionModal = false;
		dialog.close();
	}

	$: if (dialog && showTimeSelectionModal) dialog.showModal();
</script>

<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
<dialog
	bind:this={dialog}
	on:click|self={(event) => {
		if (event.target === dialog) {
			dialog.close();
			showTimeSelectionModal = false;
		}
	}}
	on:keydown|self={(event) => {
		if (event.key === 'Escape')
			() => {
				showTimeSelectionModal = false;
				dialog.close();
			};
	}}
>
	<div>
		<h1>Add Time Block</h1>
		<p>Enter the start and end times for the block and select the days it should be prohibited.</p>
		<form>
			<label for="start-time">Start Time</label>
			<input
				type="time"
				id="start-time"
				name="appt"
				value="08:00"
				min="08:00"
				max="19:59"
				required
			/>
			<label for="end-time">End Time</label>
			<input type="time" id="end-time" name="appt" value="08:01" min="08:01" max="20:00" required />
			<br />
			<input type="checkbox" id="monday" name="Monday" value="M" class="checkbox-input" />
			<label for="monday" class="checkbox-label">Monday</label><br />
			<input type="checkbox" id="tuesday" name="Tuesday" value="Tu" class="checkbox-input" />
			<label for="tuesday" class="checkbox-label">Tuesday</label><br />
			<input type="checkbox" id="wednesday" name="Wednesday" value="W" class="checkbox-input" />
			<label for="wednesday" class="checkbox-label">Wednesday</label><br />
			<input type="checkbox" id="thursday" name="Thursday" value="Th" class="checkbox-input" />
			<label for="thursday" class="checkbox-label">Thursday</label><br />
			<input type="checkbox" id="friday" name="Friday" value="F" class="checkbox-input" />
			<label for="friday" class="checkbox-label">Friday</label><br />
		</form>
		<button on:click|stopPropagation={addTime}>Submit</button>
	</div>
</dialog>

<style>
	dialog:not([open]) {
		display: none;
	}

	dialog {
		width: 75vh;
		height: 75vh;
		padding: 10px;
		box-sizing: border-box;
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		overflow: hidden;
	}

	form {
		display: flex;
		flex-direction: column;
		width: 30%;
	}

	#start-time,
	#end-time {
		/* Styles for the start and end time inputs */
		padding: 10px;
		margin-bottom: 10px;
	}

	#monday,
	#tuesday,
	#wednesday,
	#thursday,
	#friday {
		/* Styles for the weekday checkboxes */
		margin: 5px;
	}

	.checkbox-input {
		position: absolute;
		opacity: 0;
		height: 0;
		width: 0;
	}

	/* Style the label */
	.checkbox-label {
		position: relative;
		padding-left: 25px;
		cursor: pointer;
	}

	/* Add a custom box */
	.checkbox-label::before {
		content: '';
		position: absolute;
		left: 0;
		top: 0;
		height: 20px;
		width: 20px;
		border: 1px solid #000;
	}

	/* Add a custom checkmark */
	.checkbox-input:checked + .checkbox-label::after {
		content: '';
		position: absolute;
		left: 5px;
		top: 5px;
		height: 10px;
		width: 10px;
		background-color: #000;
	}

	button {
		align-self: center;
		padding: 10px 20px;
		background-color: #4caf50; /* Green */
		border: none;
		color: white;
		text-align: center;
		text-decoration: none;
		display: inline-block;
		font-size: 16px;
		margin: 4px 2px;
		cursor: pointer;
	}

	p {
		margin: 0;
	}

	h1 {
		font-size: 1.5em;
		font-weight: bold;
		margin-bottom: 0;
	}
</style>
