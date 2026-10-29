(() => {
    "use strict";

    const form = document.getElementById("report-form");
    const token = form?.elements.namedItem("submission_token");
    if (!token) return;

    // Back/reload may refetch the page while restoring its old field values.
    // Keep its submission identity with that history entry, not in shared storage.
    try {
        const state = window.history.state || {};
        if (state.reportSubmissionToken && form.dataset.renewSubmission !== "true") {
            token.value = state.reportSubmissionToken;
        } else {
            window.history.replaceState({...state, reportSubmissionToken: token.value}, "");
        }
    } catch (_) {
        // Normal submission still works when browser history storage is unavailable.
    }
})();
