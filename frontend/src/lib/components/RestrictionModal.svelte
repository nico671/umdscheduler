<script>
    import ModalShell from "./ModalShell.svelte";

    let {
        isOpen = false,
        onClose = () => {},
        weekdays = [],
        startHours = [],
        selectedRestrictedDays = [],
        selectedRestrictedStartHours = [],
        selectedRestrictionLabel = "",
        selectedRestrictionCount = 0,
        formatHour = (hour) => String(hour),
        onToggleRestrictedDay = () => {},
        onToggleRestrictedStartHour = () => {},
        onActivateRestriction = () => {},
    } = $props();
</script>

{#if isOpen}
    <ModalShell
        backdropClass="restriction-modal-backdrop"
        modalClass="restriction-modal"
        ariaLabel="Create time restrictions"
        closeLabel="Close time restriction modal"
        {onClose}
    >
        <header class="course-modal-header">
            <div>
                <p class="course-id">Schedule Constraints</p>
                <h2>Create Time Restrictions</h2>
            </div>
            <button
                class="modal-close"
                type="button"
                aria-label="Close time restriction modal"
                onclick={() => onClose()}
            >
                ×
            </button>
        </header>

        <div class="restriction-modal-body">
            <p class="card-copy">
                Pick one or more days and time slots, then activate to add every
                combination.
            </p>

            <div class="restriction-controls restriction-controls-modal">
                <fieldset class="restriction-multiselect">
                    <legend class="sr-only">Restricted days</legend>
                    <p class="restriction-group-label">Days</p>
                    <div class="restriction-options-grid">
                        {#each weekdays as day (day)}
                            <button
                                type="button"
                                class="restriction-option"
                                class:restriction-option-selected={selectedRestrictedDays.includes(
                                    day,
                                )}
                                aria-pressed={selectedRestrictedDays.includes(
                                    day,
                                )}
                                onclick={() => onToggleRestrictedDay(day)}
                            >
                                {day.slice(0, 3)}
                            </button>
                        {/each}
                    </div>
                </fieldset>

                <fieldset class="restriction-multiselect">
                    <legend class="sr-only">Restricted time slots</legend>
                    <p class="restriction-group-label">Time slots</p>
                    <div
                        class="restriction-options-grid restriction-options-grid-hours"
                    >
                        {#each startHours as hour (hour)}
                            <button
                                type="button"
                                class="restriction-option"
                                class:restriction-option-selected={selectedRestrictedStartHours.includes(
                                    hour,
                                )}
                                aria-pressed={selectedRestrictedStartHours.includes(
                                    hour,
                                )}
                                onclick={() =>
                                    onToggleRestrictedStartHour(hour)}
                            >
                                {formatHour(hour)}
                            </button>
                        {/each}
                    </div>
                </fieldset>
            </div>

            <p class="search-hint">Selected: {selectedRestrictionLabel}</p>

            <div class="restriction-modal-actions">
                <button
                    class="restriction-button"
                    type="button"
                    onclick={() => onClose()}
                >
                    Done
                </button>
                <button
                    class="add-button"
                    type="button"
                    onclick={() => onActivateRestriction()}
                    disabled={selectedRestrictionCount === 0}
                >
                    Activate restrictions
                </button>
            </div>
        </div>
    </ModalShell>
{/if}
