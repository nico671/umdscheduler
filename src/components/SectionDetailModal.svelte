<script lang="ts">
    import { onMount, createEventDispatcher } from "svelte";
    import { currentSemester } from "../routes/page-logic";

    export let showModal: boolean = false;
    export let sectionId: string = "";
    export let courseId: string = "";
    export let semester: string = ""; // Changed to use the current semester from the store

    const dispatch = createEventDispatcher();
    let dialog: HTMLDialogElement;
    let sectionData: any = null;
    let isLoading: boolean = true;
    let error: string | null = null;

    // Derived values for seat information
    $: openSeats = sectionData?.open_seats || 0;
    $: waitlist = sectionData?.waitlist || 0;

    // Watch for changes to showModal and sectionId props
    $: if (dialog && showModal && sectionId) {
        dialog.showModal();
        // Use selected semester or fallback to current semester
        const semesterToUse = semester || $currentSemester || "202501";
        fetchSectionDetails(semesterToUse);
    }

    async function fetchSectionDetails(semesterParam: string = "") {
        isLoading = true;
        error = null;

        try {
            // Always use the provided semester, current semester, or fallback
            const semesterToUse = semesterParam || $currentSemester || "202401";

            console.log(
                `Fetching section ${sectionId} details for semester: ${semesterToUse}`,
            );

            const response = await fetch(
                `https://api.umd.io/v1/courses/sections/${sectionId}?semester=${semesterToUse}`,
            );

            if (!response.ok) {
                throw new Error(
                    `Failed to fetch section details: ${response.status}`,
                );
            }

            const data = await response.json();

            if (Array.isArray(data) && data.length > 0) {
                sectionData = data[0];
            } else {
                throw new Error("No section data found");
            }
        } catch (err) {
            console.error("Error fetching section details:", err);
            error =
                err instanceof Error ? err.message : "Unknown error occurred";
        } finally {
            isLoading = false;
        }
    }

    function closeModal() {
        if (dialog) {
            dialog.close();
            dispatch("close");
        }
    }

    function handleDialogClose() {
        // Only dispatch the close event if we're actually showing the modal
        if (showModal) {
            dispatch("close");
        }
    }
</script>

<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
<!-- svelte-ignore a11y-click-events-have-key-events -->
<dialog
    bind:this={dialog}
    on:close={handleDialogClose}
    on:click|self={closeModal}
    class="section-modal"
>
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div class="modal-content" on:click|stopPropagation>
        {#if isLoading}
            <div class="loading">
                <div class="spinner"></div>
                <p>Loading section information...</p>
            </div>
        {:else if error}
            <div class="error-message">
                <h2>Error Loading Section Data</h2>
                <p>{error}</p>
                <button class="close-btn" on:click={closeModal}>Close</button>
            </div>
        {:else if sectionData}
            <div class="modal-header">
                <div>
                    <h1>{courseId}</h1>
                    <h2>Section {sectionData.number}</h2>
                </div>
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

            <div class="section-grid">
                <div class="section-info">
                    <!-- Display seat availability -->
                    <div class="availability">
                        <div class="availability-item">
                            <span class="label">Total Seats:</span>
                            <span class="value">{sectionData.seats}</span>
                        </div>
                        <div class="availability-item">
                            <span class="label">Open Seats:</span>
                            <span class="value">{openSeats}</span>
                        </div>
                        <div class="availability-item">
                            <span class="label">Waitlist:</span>
                            <span class="value">{waitlist}</span>
                        </div>
                    </div>

                    <!-- Display instructor information -->
                    <div class="instructors-container">
                        <h3>Instructors</h3>
                        <ul class="instructors-list">
                            {#if sectionData.instructors && sectionData.instructors.length > 0}
                                {#each sectionData.instructors as instructor}
                                    <li>{instructor}</li>
                                {/each}
                            {:else}
                                <li>No instructors listed</li>
                            {/if}
                        </ul>
                    </div>
                </div>

                <!-- Display meeting information -->
                <div class="meetings-container">
                    <h3>Meeting Times & Locations</h3>
                    {#if sectionData.meetings && sectionData.meetings.length > 0}
                        <ul class="meetings-list">
                            {#each sectionData.meetings as meeting}
                                <li class="meeting-item">
                                    <div class="meeting-days">
                                        {meeting.days || "N/A"}
                                    </div>
                                    <div class="meeting-time">
                                        {meeting.start_time || "N/A"} - {meeting.end_time ||
                                            "N/A"}
                                    </div>
                                    <div class="meeting-location">
                                        {meeting.building || ""}
                                        {meeting.room || ""}
                                    </div>
                                    <div class="meeting-type">
                                        {meeting.classtype || "Lecture"}
                                    </div>
                                </li>
                            {/each}
                        </ul>
                    {:else}
                        <p class="no-meetings">
                            No meeting information available
                        </p>
                    {/if}
                </div>
            </div>
        {:else}
            <div class="error-message">
                <p>No section data available</p>
                <button class="close-btn" on:click={closeModal}>Close</button>
            </div>
        {/if}
    </div>
</dialog>

<style>
    .section-modal {
        max-width: 600px;
        width: 90%;
        border-radius: 12px;
        border: none;
        padding: 0;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
        overflow: hidden;
    }

    .modal-content {
        padding: 24px;
        max-height: 85vh;
        overflow-y: auto;
    }

    .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 24px;
        border-bottom: 1px solid #eee;
        padding-bottom: 16px;
    }

    .modal-header h1 {
        margin: 0;
        font-size: 1.8rem;
        color: #e21833;
    }

    .modal-header h2 {
        margin: 4px 0 0 0;
        font-size: 1.2rem;
        color: #333;
    }

    .close-btn {
        background: transparent;
        border: none;
        cursor: pointer;
        padding: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        transition: background-color 0.2s;
    }

    .close-btn:hover {
        background-color: rgba(0, 0, 0, 0.05);
    }

    .section-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 24px;
    }

    @media (min-width: 768px) {
        .section-grid {
            grid-template-columns: 1fr 1fr;
        }
    }

    .section-info {
        display: flex;
        flex-direction: column;
        gap: 20px;
    }

    .availability {
        background-color: #f8f8f8;
        border-radius: 8px;
        padding: 16px;
    }

    .availability-item {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
    }

    .availability-item:last-child {
        margin-bottom: 0;
    }

    .label {
        font-weight: 500;
        color: #555;
    }

    .value {
        font-weight: 600;
    }

    h3 {
        margin: 0 0 12px 0;
        font-size: 1.1rem;
        color: #333;
    }

    .instructors-list,
    .meetings-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .instructors-list li {
        padding: 8px 0;
        border-bottom: 1px solid #eee;
    }

    .instructors-list li:last-child {
        border-bottom: none;
    }

    .meeting-item {
        display: grid;
        grid-template-columns: auto 1fr;
        grid-template-areas:
            "days time"
            "location location"
            "type type";
        gap: 8px;
        padding: 12px;
        background-color: #f8f8f8;
        border-radius: 8px;
        margin-bottom: 12px;
    }

    .meeting-days {
        grid-area: days;
        font-weight: 600;
        min-width: 50px;
    }

    .meeting-time {
        grid-area: time;
    }

    .meeting-location {
        grid-area: location;
        font-weight: 500;
    }

    .meeting-type {
        grid-area: type;
        font-size: 0.9rem;
        color: #666;
        font-style: italic;
    }

    .loading {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px 0;
    }

    .spinner {
        width: 40px;
        height: 40px;
        border: 4px solid #f3f3f3;
        border-top: 4px solid #e21833;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 16px;
    }

    @keyframes spin {
        0% {
            transform: rotate(0deg);
        }
        100% {
            transform: rotate(360deg);
        }
    }

    .error-message {
        text-align: center;
        color: #e21833;
        padding: 20px;
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
</style>
