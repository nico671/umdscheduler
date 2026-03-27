<script>
    let {
        title = "Courses",
        courses = [],
        listAriaLabel = "Course list",
        emptyMessage = "No items.",
        emptyStyle = "list",
        onOpenCourse = () => {},
        onRemoveCourse = () => {},
        removeLabel = "Remove",
    } = $props();
</script>

<section class="class-list-group">
    <h3>{title}</h3>

    {#if courses.length === 0}
        {#if emptyStyle === "placeholder"}
            <div class="placeholder-block preference-placeholder">
                {emptyMessage}
            </div>
        {:else}
            <ul class="selected-list" aria-label={listAriaLabel}>
                <li class="empty-state">
                    <p>{emptyMessage}</p>
                </li>
            </ul>
        {/if}
    {:else}
        <ul class="selected-list" aria-label={listAriaLabel}>
            {#each courses as course (course.id)}
                <li class="selected-item">
                    <button
                        class="course-entry-trigger"
                        type="button"
                        aria-label={`View details for ${course.id}`}
                        onclick={() => onOpenCourse(course)}
                    >
                        <p class="course-id">{course.id}</p>
                        <h3>{course.title}</h3>
                        <p class="course-meta">{course.credits} credits</p>
                    </button>
                    <button
                        class="remove-button"
                        type="button"
                        onclick={() => onRemoveCourse(course.id)}
                    >
                        {removeLabel}
                    </button>
                </li>
            {/each}
        </ul>
    {/if}
</section>
