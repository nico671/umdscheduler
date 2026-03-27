<script>
    import ModalShell from "./ModalShell.svelte";

    let {
        isOpen = false,
        onClose = () => {},
        activeCourseSummary = null,
        isLoadingCourseDetail = false,
        courseDetailError = "",
        activeCourseDetail = null,
        activeCourseAverageGpa = null,
        isLoadingActiveCourseAverageGpa = false,
        activeCourseGenedCodes = [],
        activeCourseProfessors = [],
        professorRatingsByName = {},
        isLoadingProfessorRatings = false,
        prohibitedProfessors = [],
        isSectionsExpanded = false,
        sortedActiveCourseSections = [],
        isActiveCourseOptional = false,
        isActiveCourseRequired = false,
        formatAverageGpa = (value) => String(value ?? "Unavailable"),
        formatProfessorRating = (value) => String(value ?? "No rating yet"),
        getProfessorReviewUrl = () => null,
        onAddOptional = () => {},
        onAddRequired = () => {},
        onAllowProfessor = () => {},
        onProhibitProfessor = () => {},
        onToggleSectionsExpanded = () => {},
    } = $props();
</script>

{#if isOpen}
    <ModalShell
        backdropClass="course-modal-backdrop"
        modalClass="course-modal"
        ariaLabel="Course details"
        closeLabel="Close class details"
        {onClose}
    >
        <header class="course-modal-header">
            <div>
                <p class="course-id">{activeCourseSummary?.id ?? "Course"}</p>
                <h2>{activeCourseSummary?.title ?? "Class details"}</h2>
            </div>
            <div class="course-modal-actions">
                <button
                    class="restriction-button"
                    type="button"
                    onclick={() => onAddOptional()}
                    disabled={isActiveCourseOptional || isActiveCourseRequired}
                >
                    {isActiveCourseOptional
                        ? "Already optional"
                        : "Add as optional"}
                </button>
                <button
                    class="add-button"
                    type="button"
                    onclick={() => onAddRequired()}
                    disabled={isActiveCourseRequired}
                >
                    {isActiveCourseRequired ? "Already added" : "Add class"}
                </button>
                <button
                    class="modal-close"
                    type="button"
                    aria-label="Close class details"
                    onclick={() => onClose()}
                >
                    ×
                </button>
            </div>
        </header>

        {#if isLoadingCourseDetail}
            <div class="modal-state">Loading class information…</div>
        {:else if courseDetailError}
            <div class="modal-state">{courseDetailError}</div>
        {:else if activeCourseDetail}
            <div class="course-modal-body">
                <p class="card-copy">
                    {activeCourseDetail.description ||
                        "No description available."}
                </p>

                <div class="modal-metadata">
                    <span class="modal-metadata-chip"
                        >Credits: {activeCourseDetail.credits || "N/A"}</span
                    >
                    <span class="modal-metadata-chip gpa-chip">
                        <span>
                            Average GPA: {isLoadingActiveCourseAverageGpa
                                ? "Loading..."
                                : formatAverageGpa(activeCourseAverageGpa)}
                        </span>
                        <span class="info-tooltip">
                            <button
                                type="button"
                                class="info-tooltip-trigger"
                                aria-label="How class average GPA is calculated"
                                >i</button
                            >
                            <span class="info-tooltip-content" role="tooltip">
                                Class average GPA is pulled from PlanetTerp's
                                <code>/api/v1/course</code> average_gpa field for
                                this course, based on historical grade distributions.
                            </span>
                        </span>
                    </span>
                    <span class="modal-metadata-chip">
                        GenEd: {activeCourseGenedCodes.length
                            ? activeCourseGenedCodes.join(", ")
                            : "None"}
                    </span>
                </div>
                <section class="modal-section">
                    <h3>Professors</h3>
                    {#if activeCourseProfessors.length === 0}
                        <p class="modal-item-copy">
                            No instructor names are currently listed.
                        </p>
                    {:else}
                        <ul
                            class="modal-list"
                            aria-label="Professors and ratings"
                        >
                            {#each activeCourseProfessors as professor (professor)}
                                <li class="modal-item professor-item">
                                    <div>
                                        <p class="modal-item-title">
                                            {professor}
                                        </p>
                                        <p class="modal-item-copy">
                                            {#if isLoadingProfessorRatings && !(professor in professorRatingsByName)}
                                                Loading PlanetTerp rating…
                                            {:else}
                                                Rating: {formatProfessorRating(
                                                    professorRatingsByName[
                                                        professor
                                                    ]?.rating,
                                                )}
                                            {/if}
                                        </p>
                                    </div>
                                    <div class="professor-actions">
                                        {#if getProfessorReviewUrl(professor)}
                                            <a
                                                class="remove-button professor-link"
                                                href={getProfessorReviewUrl(
                                                    professor,
                                                )}
                                                target="_blank"
                                                rel="noreferrer"
                                            >
                                                View reviews
                                            </a>
                                        {/if}
                                        {#if prohibitedProfessors.includes(professor)}
                                            <button
                                                class="remove-button"
                                                type="button"
                                                onclick={() =>
                                                    onAllowProfessor(professor)}
                                            >
                                                Undo prohibit
                                            </button>
                                        {:else}
                                            <button
                                                class="remove-button"
                                                type="button"
                                                onclick={() =>
                                                    onProhibitProfessor(
                                                        professor,
                                                    )}
                                            >
                                                Prohibit professor
                                            </button>
                                        {/if}
                                    </div>
                                </li>
                            {/each}
                        </ul>
                    {/if}
                </section>

                <section class="modal-section">
                    <div class="modal-section-header">
                        <h3>Sections</h3>
                        <button
                            class="restriction-button section-toggle"
                            type="button"
                            onclick={() => onToggleSectionsExpanded()}
                            aria-expanded={isSectionsExpanded}
                        >
                            {isSectionsExpanded
                                ? "Hide sections"
                                : "View sections"}
                        </button>
                    </div>
                    {#if isSectionsExpanded}
                        {#if sortedActiveCourseSections.length}
                            <ul
                                class="modal-list"
                                aria-label="Available sections"
                            >
                                {#each sortedActiveCourseSections as section (section.section_code)}
                                    <li class="modal-item">
                                        <p class="modal-item-title">
                                            Section {section.section_code}
                                        </p>
                                        <p class="modal-item-copy">
                                            Instructors: {section.instructors
                                                ?.length
                                                ? section.instructors.join(", ")
                                                : "TBA"}
                                        </p>
                                        <p class="modal-item-copy">
                                            Seats: {section.open_seats} open /
                                            {section.total_seats} total
                                        </p>
                                        <p class="modal-item-copy">
                                            Waitlist: {section.waitlist ?? 0}
                                        </p>
                                    </li>
                                {/each}
                            </ul>
                        {:else}
                            <p class="modal-item-copy">
                                No section data available for this semester.
                            </p>
                        {/if}
                    {/if}
                </section>
            </div>
        {/if}
    </ModalShell>
{/if}
