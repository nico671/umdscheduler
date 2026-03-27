<script>
    let {
        backdropClass = "course-modal-backdrop",
        modalClass = "course-modal",
        ariaLabel = "Dialog",
        closeLabel = "Close modal",
        onClose = () => {},
        children,
    } = $props();
</script>

<div class={backdropClass} role="presentation">
    <button
        class="modal-overlay-dismiss"
        type="button"
        aria-label={closeLabel}
        onclick={() => onClose()}
    ></button>
    <div
        class={modalClass}
        role="dialog"
        aria-modal="true"
        aria-label={ariaLabel}
    >
        {@render children?.()}
    </div>
</div>
