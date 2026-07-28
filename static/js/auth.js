(() => {
    document.querySelectorAll("[data-password-toggle]").forEach((button) => {
        button.addEventListener("click", () => {
            const input = button.parentElement.querySelector("input");
            const showing = input.type === "text";
            input.type = showing ? "password" : "text";
            button.textContent = showing ? "Show" : "Hide";
            button.setAttribute("aria-label", showing ? "Show password" : "Hide password");
            input.focus();
        });
    });
    document.querySelectorAll(".auth-card form").forEach((form) => {
        form.addEventListener("submit", () => {
            const button = form.querySelector('button[type="submit"]');
            if (!button || button.disabled) return;
            button.disabled = true;
            button.dataset.originalText = button.textContent;
            button.textContent = "Please wait…";
        });
    });
})();
