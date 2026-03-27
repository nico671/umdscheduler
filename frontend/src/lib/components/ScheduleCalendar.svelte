<script>
    let {
        schedule = null,
        weekdays = [],
        formatHour = (hour) => String(hour),
        onEntrySelect = () => {},
    } = $props();
</script>

{#if schedule?.calendar}
    <div class="week-calendar-shell">
        <div class="week-calendar-header-row">
            <div class="time-column-spacer" aria-hidden="true"></div>
            {#each weekdays as day (day)}
                <p class="calendar-day-heading">{day.slice(0, 3)}</p>
            {/each}
        </div>

        <div class="week-calendar-body">
            <div class="calendar-time-column" aria-hidden="true">
                {#each schedule.calendar.hourMarkers as hour (hour)}
                    {@const topPercent =
                        ((hour * 60 - schedule.calendar.startMinutes) /
                            (schedule.calendar.endMinutes -
                                schedule.calendar.startMinutes)) *
                        100}
                    <span
                        class="calendar-time-label"
                        style={`top: ${topPercent}%`}
                    >
                        {formatHour(hour)}
                    </span>
                {/each}
            </div>

            <div class="calendar-days-grid">
                {#each schedule.calendar.dayColumns as dayColumn (dayColumn.day)}
                    <div class="calendar-day-column">
                        {#each schedule.calendar.hourMarkers as hour (hour)}
                            {@const lineTopPercent =
                                ((hour * 60 - schedule.calendar.startMinutes) /
                                    (schedule.calendar.endMinutes -
                                        schedule.calendar.startMinutes)) *
                                100}
                            <span
                                class="calendar-hour-line"
                                style={`top: ${lineTopPercent}%`}
                            ></span>
                        {/each}

                        {#each dayColumn.entries as entry (`${entry.courseCode}-${entry.sectionCode}-${entry.startMinutes}-${entry.laneIndex}`)}
                            <button
                                type="button"
                                class="calendar-entry calendar-entry-button"
                                aria-label={`View details for ${entry.courseCode} section ${entry.sectionCode}`}
                                onclick={() => onEntrySelect(entry)}
                                style={`top: ${entry.topPercent}%; height: ${entry.heightPercent}%; left: calc(${entry.leftPercent}% + 0.2rem); width: calc(${entry.widthPercent}% - 0.35rem); --entry-color: ${entry.color};`}
                            >
                                <p class="calendar-entry-title">
                                    {entry.courseCode} · {entry.sectionCode}
                                </p>
                                <p class="calendar-entry-copy">{entry.label}</p>
                            </button>
                        {/each}
                    </div>
                {/each}
            </div>
        </div>
    </div>
{/if}
