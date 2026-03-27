<script>
    let {
        appName = "UMDScheduler",
        query = $bindable(""),
        normalizedQuery = "",
        isLoadingCourses = false,
        coursesLoadError = "",
        searchDropdownCourses = [],
        canGenerateSchedules = false,
        isLoadingSchedules = false,
        onOpenRestrictionModal = () => {},
        onGenerateSchedules = () => {},
        onSelectCourse = () => {},
    } = $props();
</script>

<header class="topbar" aria-label="Primary planning controls">
    <div class="topbar-shell">
        <p class="app-name">{appName}</p>

        <div class="topbar-right">
            <div class="topbar-actions-panel" aria-label="Primary actions">
                <button
                    class="add-button topbar-primary-button"
                    type="button"
                    onclick={() => onOpenRestrictionModal()}
                >
                    Create time restriction
                </button>
                <button
                    class="add-button topbar-primary-button"
                    type="button"
                    onclick={() => onGenerateSchedules()}
                    disabled={!canGenerateSchedules}
                >
                    {#if isLoadingSchedules}
                        Generating schedules…
                    {:else}
                        Generate schedules
                    {/if}
                </button>
            </div>

            <div class="topbar-controls">
                <div class="search-panel">
                    <div class="search-row">
                        <input
                            id="course-query"
                            class="search-input"
                            type="search"
                            bind:value={query}
                            placeholder="Search courses by code, title or GenEd"
                        />
                    </div>

                    {#if normalizedQuery && !isLoadingCourses && !coursesLoadError}
                        <ul
                            class="search-dropdown"
                            aria-label="Matching courses"
                        >
                            {#if searchDropdownCourses.length === 0}
                                <li class="search-dropdown-empty">
                                    No matching courses found.
                                </li>
                            {:else}
                                {#each searchDropdownCourses as course (course.id)}
                                    <li>
                                        <button
                                            class="search-dropdown-item"
                                            type="button"
                                            onclick={() =>
                                                onSelectCourse(course)}
                                        >
                                            <span class="search-code"
                                                >{course.id}</span
                                            >
                                            <span>
                                                <span class="search-title"
                                                    >{course.title}</span
                                                >
                                                {#if course.genedCodes.length > 0}
                                                    <span class="search-gened"
                                                        >{course.genedCodes.join(
                                                            ", ",
                                                        )}</span
                                                    >
                                                {/if}
                                            </span>
                                        </button>
                                    </li>
                                {/each}
                            {/if}
                        </ul>
                    {/if}
                </div>
            </div>
        </div>
    </div>
</header>
