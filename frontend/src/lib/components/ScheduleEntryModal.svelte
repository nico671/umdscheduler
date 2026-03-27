<script>
    import ModalShell from "./ModalShell.svelte";

    let {
        isOpen = false,
        onClose = () => {},
        activeScheduleEntrySummary = null,
        isLoadingScheduleEntryDetail = false,
        scheduleEntryDetailError = "",
        activeScheduleEntry = null,
        activeScheduleEntrySection = null,
        activeScheduleEntryCourseDetail = null,
        activeScheduleEntrySectionGpa = null,
        isLoadingActiveScheduleEntrySectionGpa = false,
        activeScheduleEntryProfessors = [],
        isLoadingScheduleEntryRatings = false,
        scheduleEntryProfessorRatingsByName = {},
        formatAverageGpa = (value) => String(value ?? "Unavailable"),
        formatProfessorRating = (value) => String(value ?? "No rating yet"),
        getScheduleEntryProfessorReviewUrl = () => null,
        getMeetingLocation = () => "",
    } = $props();
</script>

{#if isOpen}
    <ModalShell
        backdropClass="course-modal-backdrop"
        modalClass="course-modal"
        ariaLabel="Scheduled class details"
        closeLabel="Close scheduled class details"
        {onClose}
    >
        <header class="course-modal-header">
            <div>
                <p class="course-id">
                    {activeScheduleEntrySummary?.id ?? "Course"}
                </p>
                <h2>
                    {activeScheduleEntrySummary?.title ??
                        "Scheduled class details"}
                </h2>
            </div>
            <button
                class="modal-close"
                type="button"
                aria-label="Close scheduled class details"
                onclick={() => onClose()}
            >
                ×
            </button>
        </header>

        {#if isLoadingScheduleEntryDetail}
            <div class="modal-state">
                Loading class and section information…
            </div>
        {:else if scheduleEntryDetailError}
            <div class="modal-state">{scheduleEntryDetailError}</div>
        {:else if activeScheduleEntry && activeScheduleEntrySection}
            <div class="course-modal-body">
                <div class="modal-metadata">
                    <span class="modal-metadata-chip"
                        >Section: {activeScheduleEntry.sectionCode}</span
                    >
                    <span class="modal-metadata-chip"
                        >Selected meeting: {activeScheduleEntry.day},
                        {activeScheduleEntry.label}</span
                    >
                    {#if activeScheduleEntry.location}
                        <span class="modal-metadata-chip"
                            >Location: {activeScheduleEntry.location}</span
                        >
                    {/if}
                    <span class="modal-metadata-chip"
                        >Credits: {activeScheduleEntryCourseDetail?.credits ??
                            "N/A"}</span
                    >
                    <span class="modal-metadata-chip gpa-chip">
                        <span>
                            Section GPA: {isLoadingActiveScheduleEntrySectionGpa
                                ? "Loading..."
                                : formatAverageGpa(
                                      activeScheduleEntrySectionGpa,
                                  )}
                        </span>
                        <span class="info-tooltip">
                            <button
                                type="button"
                                class="info-tooltip-trigger"
                                aria-label="How section GPA is calculated"
                                >i</button
                            >
                            <span class="info-tooltip-content" role="tooltip">
                                Section GPA is a weighted average over A–F
                                grades from PlanetTerp
                                <code>/api/v1/grades</code> for the section's listed
                                instructors in this course. Grade counts are used
                                as weights.
                            </span>
                        </span>
                    </span>
                </div>

                <p class="card-copy">
                    {activeScheduleEntryCourseDetail?.description ||
                        "No description available."}
                </p>

                <section class="modal-section">
                    <h3>Professors (PlanetTerp ratings)</h3>
                    {#if activeScheduleEntryProfessors.length === 0}
                        <p class="modal-item-copy">
                            No instructor names are currently listed.
                        </p>
                    {:else}
                        <ul
                            class="modal-list"
                            aria-label="Section professors and ratings"
                        >
                            {#each activeScheduleEntryProfessors as professor (professor)}
                                <li class="modal-item professor-item">
                                    <div>
                                        <p class="modal-item-title">
                                            {professor}
                                        </p>
                                        <p class="modal-item-copy">
                                            {#if isLoadingScheduleEntryRatings && !(professor in scheduleEntryProfessorRatingsByName)}
                                                Loading PlanetTerp rating…
                                            {:else}
                                                Rating: {formatProfessorRating(
                                                    scheduleEntryProfessorRatingsByName[
                                                        professor
                                                    ]?.rating,
                                                )}
                                            {/if}
                                        </p>
                                    </div>
                                    {#if getScheduleEntryProfessorReviewUrl(professor)}
                                        <a
                                            class="remove-button professor-link"
                                            href={getScheduleEntryProfessorReviewUrl(
                                                professor,
                                            )}
                                            target="_blank"
                                            rel="noreferrer"
                                        >
                                            View reviews
                                        </a>
                                    {/if}
                                </li>
                            {/each}
                        </ul>
                    {/if}
                </section>

                <section class="modal-section">
                    <h3>Section Meetings</h3>
                    {#if activeScheduleEntrySection.meetings?.length}
                        <ul class="modal-list" aria-label="Section meetings">
                            {#each activeScheduleEntrySection.meetings as meeting, index (`${meeting.days ?? "NA"}-${meeting.start_time ?? "NA"}-${meeting.end_time ?? "NA"}-${index}`)}
                                <li class="modal-item">
                                    <p class="modal-item-title">
                                        {meeting.class_type || "Class"}
                                    </p>
                                    <p class="modal-item-copy">
                                        {meeting.days || "TBA"} ·
                                        {meeting.start_time || "TBA"} -
                                        {meeting.end_time || "TBA"}
                                    </p>
                                    <p class="modal-item-copy">
                                        {getMeetingLocation(meeting) ||
                                            "Location TBD"}
                                    </p>
                                </li>
                            {/each}
                        </ul>
                    {:else}
                        <p class="modal-item-copy">
                            No meeting details are available.
                        </p>
                    {/if}
                </section>
            </div>
        {/if}
    </ModalShell>
{/if}
