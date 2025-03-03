<script lang="ts">
	import { createEventDispatcher } from "svelte";

	export let showTimeSelectionModal = false;
	// Changed to const export with proper type since it's not being used inside the component
	export const prohibitedTimes: Array<any> = [];

	let dialog: HTMLDialogElement;
	let selectedDay = "Monday";
	let startHour = "8";
	let startMinute = "00";
	let startAMPM = "AM";
	let endHour = "9";
	let endMinute = "00";
	let endAMPM = "AM";

	const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
	const hours = Array.from({ length: 12 }, (_, i) => String(i + 1));
	const minutes = ["00", "15", "30", "45"];
	const ampm = ["AM", "PM"];

	const dispatch = createEventDispatcher();

	$: if (dialog && showTimeSelectionModal) dialog.showModal();

	function closeModal() {
		dispatch("close");
		dialog.close();
	}

	function handleSubmit() {
		// Convert day to abbreviated form as needed by the backend
		let dayCode;
		switch (selectedDay) {
			case "Monday":
				dayCode = "M";
				break;
			case "Tuesday":
				dayCode = "Tu";
				break;
			case "Wednesday":
				dayCode = "W";
				break;
			case "Thursday":
				dayCode = "Th";
				break;
			case "Friday":
				dayCode = "F";
				break;
		}

		// Convert times to standardized format
		const startTime = formatTime(startHour, startMinute, startAMPM);
		const endTime = formatTime(endHour, endMinute, endAMPM);

		// Create the time restriction as a Map
		const timeRestriction = new Map();
		timeRestriction.set("days", dayCode);
		timeRestriction.set("start_time", startTime);
		timeRestriction.set("end_time", endTime);

		dispatch("add", timeRestriction);
	}

	function formatTime(hour: string, minute: string, ampm: string) {
		let hourNum = parseInt(hour);

		// Convert to 24-hour format
		if (ampm === "PM" && hourNum < 12) {
			hourNum += 12;
		} else if (ampm === "AM" && hourNum === 12) {
			hourNum = 0;
		}

		// Format as a string
		return `${hourNum.toString().padStart(2, "0")}:${minute}${ampm.toLowerCase()}`;
	}
</script>

<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
<!-- svelte-ignore a11y-click-events-have-key-events -->
<dialog
	bind:this={dialog}
	on:close={() => (showTimeSelectionModal = false)}
	on:click|self={closeModal}
	class="time-modal"
>
	<div class="modal-content" on:click|stopPropagation role="dialog">
		<div class="modal-header">
			<h2>Add Time Restriction</h2>
			<button class="close-btn" on:click={closeModal}>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="24"
					height="24"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
				>
					<line x1="18" y1="6" x2="6" y2="18"></line>
					<line x1="6" y1="6" x2="18" y2="18"></line>
				</svg>
			</button>
		</div>

		<form on:submit|preventDefault={handleSubmit}>
			<div class="form-group">
				<label for="day">Day:</label>
				<select id="day" bind:value={selectedDay}>
					{#each days as day}
						<option value={day}>{day}</option>
					{/each}
				</select>
			</div>

			<div class="time-section">
				<h3>Start Time:</h3>
				<div class="time-inputs">
					<select bind:value={startHour}>
						{#each hours as hour}
							<option value={hour}>{hour}</option>
						{/each}
					</select>
					<span>:</span>
					<select bind:value={startMinute}>
						{#each minutes as minute}
							<option value={minute}>{minute}</option>
						{/each}
					</select>
					<select bind:value={startAMPM}>
						{#each ampm as period}
							<option value={period}>{period}</option>
						{/each}
					</select>
				</div>
			</div>

			<div class="time-section">
				<h3>End Time:</h3>
				<div class="time-inputs">
					<select bind:value={endHour}>
						{#each hours as hour}
							<option value={hour}>{hour}</option>
						{/each}
					</select>
					<span>:</span>
					<select bind:value={endMinute}>
						{#each minutes as minute}
							<option value={minute}>{minute}</option>
						{/each}
					</select>
					<select bind:value={endAMPM}>
						{#each ampm as period}
							<option value={period}>{period}</option>
						{/each}
					</select>
				</div>
			</div>

			<div class="button-container">
				<button type="button" class="cancel-btn" on:click={closeModal}
					>Cancel</button
				>
				<button type="submit" class="add-btn">Add Restriction</button>
			</div>
		</form>
	</div>
</dialog>

<style>
	.time-modal {
		max-width: 450px;
		width: 90%;
		border-radius: 12px;
		border: none;
		padding: 0;
		box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
		overflow: hidden;
	}

	.modal-content {
		padding: 24px;
	}

	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;
	}

	.modal-header h2 {
		margin: 0;
		color: #222;
	}

	.close-btn {
		background: transparent;
		border: none;
		cursor: pointer;
		padding: 4px;
		display: flex;
		color: #666;
		transition: color 0.2s;
	}

	.close-btn:hover {
		color: #222;
	}

	.form-group {
		margin-bottom: 20px;
	}

	.form-group label {
		display: block;
		margin-bottom: 8px;
		font-weight: 500;
	}

	select {
		width: 100%;
		padding: 10px 12px;
		border: 1px solid #ddd;
		border-radius: 6px;
		font-size: 16px;
		appearance: auto;
	}

	.time-section {
		margin-bottom: 20px;
	}

	.time-section h3 {
		margin: 0 0 8px 0;
		font-size: 16px;
		font-weight: 500;
	}

	.time-inputs {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.time-inputs select {
		width: auto;
	}

	.time-inputs span {
		font-weight: bold;
	}

	.button-container {
		display: flex;
		gap: 12px;
		justify-content: flex-end;
		margin-top: 24px;
	}

	.cancel-btn {
		background-color: #f0f0f0;
		border: none;
		padding: 10px 16px;
		border-radius: 6px;
		cursor: pointer;
		font-weight: 500;
	}

	.add-btn {
		background-color: #e21833;
		border: none;
		color: white;
		padding: 10px 16px;
		border-radius: 6px;
		cursor: pointer;
		font-weight: 500;
	}

	.add-btn:hover {
		background-color: #c91528;
	}

	dialog::backdrop {
		background: rgba(0, 0, 0, 0.5);
		backdrop-filter: blur(2px);
	}

	dialog[open] {
		animation: zoom 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
	}

	@keyframes zoom {
		from {
			transform: scale(0.95);
			opacity: 0;
		}
		to {
			transform: scale(1);
			opacity: 1;
		}
	}

	dialog[open]::backdrop {
		animation: fade 0.2s ease-out;
	}

	@keyframes fade {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}
</style>
