<script lang="ts">
    import { onMount } from "svelte";
    import {
        currentSemester,
        availableSemesters,
        formatSemester,
    } from "../routes/page-logic";

    export let onChange: ((semester: string) => void) | null = null;

    function handleSemesterChange(event: Event) {
        const target = event.target as HTMLSelectElement;
        if (target && target.value) {
            $currentSemester = target.value;

            if (onChange) {
                onChange($currentSemester);
            }
        }
    }
</script>

<div class="semester-selector">
    <select
        value={$currentSemester}
        on:change={handleSemesterChange}
        aria-label="Select semester"
    >
        {#if $availableSemesters.length === 0}
            <option value="202508">Loading semesters...</option>
        {:else}
            {#each $availableSemesters as semester}
                <option value={semester}>{formatSemester(semester)}</option>
            {/each}
        {/if}
    </select>
</div>

<style>
    .semester-selector {
        position: relative;
    }

    select {
        appearance: none;
        background-color: white;
        border: 1px solid var(--neutral-300);
        border-radius: var(--radius-md);
        padding: var(--space-2) var(--space-4);
        padding-right: 32px;
        cursor: pointer;
        font-size: 0.9rem;
        color: var(--neutral-800);
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23757575' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: right 8px center;
        background-size: 16px;
    }

    select:focus {
        outline: none;
        border-color: var(--primary);
        box-shadow: 0 0 0 2px rgba(226, 24, 51, 0.1);
    }
</style>
