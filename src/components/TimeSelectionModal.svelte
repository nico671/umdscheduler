<script lang="ts">
	import { createEventDispatcher } from "svelte";

	export let showTimeSelectionModal = false;
	export const prohibitedTimes: Array<any> = [];

	let dialog: HTMLDialogElement;
	// Convert single day selection to array of selected days
	let selectedDays = {
		Monday: false,
		Tuesday: false,
		Wednesday: false,
		Thursday: false,
		Friday: false,
	};
	let startHour = "8";
	let startMinute = "00";
	let startAMPM = "AM";
	let endHour = "9";
	let endMinute = "00";
	let endAMPM = "AM";

	type DayKey = "Monday" | "Tuesday" | "Wednesday" | "Thursday" | "Friday";

	// Ensure dayNames are of this type
	const dayNames: DayKey[] = [
		"Monday",
		"Tuesday",
		"Wednesday",
		"Thursday",
		"Friday",
	];

	const dayCodes = {
		Monday: "M",
		Tuesday: "Tu",
		Wednesday: "W",
		Thursday: "Th",
		Friday: "F",
	};
	const hours = Array.from({ length: 12 }, (_, i) => String(i + 1));
	const minutes = ["00", "15", "30", "45"];
	const ampm = ["AM", "PM"];

	const dispatch = createEventDispatcher();

	$: if (dialog && showTimeSelectionModal) dialog.showModal();

	// Computed property to check if at least one day is selected
	$: hasDaySelected = Object.values(selectedDays).some(
		(selected) => selected,
	);

	function closeModal() {
		dispatch("close");
		dialog.close();
	}

	function handleSubmit() {
		// Create a time restriction for each selected day
		const selectedDayEntries = Object.entries(selectedDays)
			.filter(([_, selected]) => selected)
			.map(([dayName, _]) => dayName);

		// Convert times to standardized format
		const startTime = formatTime(startHour, startMinute, startAMPM);
		const endTime = formatTime(endHour, endMinute, endAMPM);

		// Create a restriction for each selected day
		const restrictions = selectedDayEntries.map((dayName) => {
			const timeRestriction = new Map();
			timeRestriction.set(
				"days",
				dayCodes[dayName as keyof typeof dayCodes],
			);
			timeRestriction.set("start_time", startTime);
			timeRestriction.set("end_time", endTime);
			return timeRestriction;
		});

		// Dispatch all restrictions
		dispatch("addMultiple", restrictions);
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

	function toggleAllDays(select: boolean) {
		for (const day of dayNames) {
			selectedDays[day as keyof typeof selectedDays] = select;
		}
		// Force UI update
		selectedDays = { ...selectedDays };
	}
</script>

<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
<!-- svelte-ignore a11y-click-events-have-key-events -->
<dialog
	bind:this={dialog}
	on:close={() => (showTimeSelectionModal = false)}
	on:click|self={closeModal}
	class="modal"
>
	<div class="modal-content" on:click|stopPropagation role="dialog">
		<div class="modal-header">
			<h1>Add Time Restriction</h1>
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
				<!-- svelte-ignore a11y-label-has-associated-control -->
				<label class="form-label">Select Days</label>
				<div class="days-grid">
					{#each dayNames as day}
						<label class="day-checkbox">
							<input
								type="checkbox"
								bind:checked={selectedDays[day]}
							/>
							<span class="checkbox-display"
								>{day.substring(0, 3)}</span
							>
						</label>
					{/each}
				</div>
				<div class="day-actions">
					<button
						type="button"
						class="btn-link"
						on:click={() => toggleAllDays(true)}>Select All</button
					>
					<button
						type="button"
						class="btn-link"
						on:click={() => toggleAllDays(false)}>Clear All</button
					>
				</div>
			</div>

			<div class="time-container">
				<div class="time-section">
					<!-- svelte-ignore a11y-label-has-associated-control -->
					<label class="form-label">Start Time</label>
					<div class="time-inputs">
						<select bind:value={startHour} class="time-select">
							{#each hours as hour}
								<option value={hour}>{hour}</option>
							{/each}
						</select>
						<span class="time-separator">:</span>
						<select bind:value={startMinute} class="time-select">
							{#each minutes as minute}
								<option value={minute}>{minute}</option>
							{/each}
						</select>
						<select bind:value={startAMPM} class="ampm-select">
							{#each ampm as period}
								<option value={period}>{period}</option>
							{/each}
						</select>
					</div>
				</div>

				<div class="time-section">
					<!-- svelte-ignore a11y-label-has-associated-control -->
					<label class="form-label">End Time</label>
					<div class="time-inputs">
						<select bind:value={endHour} class="time-select">
							{#each hours as hour}
								<option value={hour}>{hour}</option>
							{/each}
						</select>
						<span class="time-separator">:</span>
						<select bind:value={endMinute} class="time-select">
							{#each minutes as minute}
								<option value={minute}>{minute}</option>
							{/each}
						</select>
						<select bind:value={endAMPM} class="ampm-select">
							{#each ampm as period}
								<option value={period}>{period}</option>
							{/each}
						</select>
					</div>
				</div>
			</div>

			<div class="form-footer">
				<button
					type="button"
					class="btn btn-outline"
					on:click={closeModal}>Cancel</button
				>
				<button
					type="submit"
					class="btn btn-primary"
					disabled={!hasDaySelected}
				>
					Add Restriction{selectedDays &&
					Object.values(selectedDays).filter(Boolean).length > 1
						? "s"
						: ""}
				</button>
			</div>
		</form>
	</div>
</dialog>

<style>
	.modal {
		max-width: 450px;
		width: 95%;
		border-radius: var(--radius-lg);
		border: none;
		padding: 0;
		box-shadow: var(--shadow-lg);
		overflow: hidden;
	}

	.modal-content {
		padding: var(--space-5);
		max-height: 85vh;
		overflow-y: auto;
	}

	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--space-5);
		border-bottom: 1px solid var(--neutral-200);
		padding-bottom: var(--space-4);
	}

	.modal-header h1 {
		margin: 0;
		font-size: 1.5rem;
		color: var(--primary);
	}

	.close-btn {
		background: transparent;
		border: none;
		cursor: pointer;
		padding: var(--space-1);
		color: var(--neutral-600);
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 50%;
		transition: background-color var(--transition-fast);
	}

	.close-btn:hover {
		background-color: var(--neutral-100);
	}

	.form-group {
		margin-bottom: var(--space-5);
	}

	.form-label {
		display: block;
		margin-bottom: var(--space-3);
		font-weight: 500;
		color: var(--neutral-800);
	}

	/* Days grid with improved styling */
	.days-grid {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: var(--space-2);
		margin-bottom: var(--space-3);
	}

	.day-checkbox {
		position: relative;
		display: block;
	}

	.day-checkbox input {
		position: absolute;
		opacity: 0;
		cursor: pointer;
		height: 0;
		width: 0;
	}

	.checkbox-display {
		display: flex;
		align-items: center;
		justify-content: center;
		background-color: var(--neutral-100);
		color: var(--neutral-700);
		border: 1px solid var(--neutral-300);
		height: 40px;
		border-radius: var(--radius-md);
		font-weight: 500;
		cursor: pointer;
		transition: all var(--transition-fast);
		user-select: none;
	}

	.day-checkbox input:checked + .checkbox-display {
		background-color: var(--primary-light);
		color: var(--primary);
		border-color: var(--primary);
	}

	.day-checkbox:hover .checkbox-display {
		background-color: var(--neutral-200);
	}

	.day-checkbox input:checked:hover + .checkbox-display {
		background-color: var(--primary-light);
		opacity: 0.9;
	}

	.day-actions {
		display: flex;
		justify-content: flex-end;
		gap: var(--space-3);
		margin-top: var(--space-2);
	}

	.btn-link {
		background: none;
		border: none;
		color: var(--primary);
		font-size: 0.875rem;
		font-weight: 500;
		padding: var(--space-1) 0;
		cursor: pointer;
		text-decoration: none;
		transition: opacity var(--transition-fast);
	}

	.btn-link:hover {
		text-decoration: underline;
		opacity: 0.9;
	}

	/* Time inputs with improved styling - now stacked vertically */
	.time-container {
		display: flex;
		flex-direction: column;
		gap: var(--space-4);
		margin-bottom: var(--space-5);
	}

	.time-section {
		width: 100%;
	}

	.time-inputs {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		width: 100%;
	}

	select {
		height: 40px;
		border: 1px solid var(--neutral-300);
		border-radius: var(--radius-md);
		background-color: white;
		padding: 0 var(--space-2);
		font-size: 1rem;
		color: var(--neutral-800);
		transition: border-color var(--transition-fast);
		-webkit-appearance: none;
		-moz-appearance: none;
		appearance: none;
		background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23757575' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
		background-repeat: no-repeat;
		background-position: right 8px center;
		background-size: 16px;
		padding-right: 28px;
	}

	select:focus {
		outline: none;
		border-color: var(--primary);
		box-shadow: 0 0 0 2px rgba(226, 24, 51, 0.1);
	}

	/* Make time selects more prominent with vertical layout */
	.time-select {
		width: 70px;
		flex-grow: 1;
	}

	.ampm-select {
		width: 80px;
	}

	.time-separator {
		font-weight: bold;
		font-size: 1.2rem;
		color: var(--neutral-600);
	}

	/* Form footer */
	.form-footer {
		display: flex;
		justify-content: flex-end;
		gap: var(--space-3);
		padding-top: var(--space-4);
		border-top: 1px solid var(--neutral-200);
	}

	.btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: var(--space-2) var(--space-4);
		border-radius: var(--radius-md);
		font-weight: 500;
		border: none;
		cursor: pointer;
		transition:
			background-color var(--transition-fast),
			transform var(--transition-fast),
			box-shadow var(--transition-fast);
	}

	.btn-primary {
		background-color: var(--primary);
		color: white;
	}

	.btn-primary:hover:not(:disabled) {
		background-color: var(--primary-dark);
		box-shadow: var(--shadow-md);
	}

	.btn-primary:disabled {
		background-color: var(--neutral-400);
		cursor: not-allowed;
	}

	.btn-outline {
		background-color: transparent;
		border: 1px solid var(--neutral-300);
	}

	.btn-outline:hover {
		background-color: var(--neutral-100);
	}

	/* Dialog animations */
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

	/* Media queries for better responsiveness */
	@media (max-width: 500px) {
		.days-grid {
			grid-template-columns: repeat(3, 1fr);
		}
	}
</style>
