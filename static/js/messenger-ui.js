(() => {
    const search = document.querySelector(".conversation-search input");
    const conversations = Array.from(document.querySelectorAll(".conversation-item"));
    const filterButtons = Array.from(
        document.querySelectorAll("[data-conversation-filter]")
    );
    let activeFilter = "all";

    function filterConversations() {
        const query = search?.value.trim().toLowerCase() || "";
        conversations.forEach((item) => {
            const matchesQuery =
                !query || item.textContent.toLowerCase().includes(query);
            const matchesFilter =
                (activeFilter === "all" &&
                    item.dataset.conversationArchived !== "true") ||
                (activeFilter === "unread" &&
                    item.dataset.conversationUnread === "true" &&
                    item.dataset.conversationArchived !== "true") ||
                (activeFilter === "groups" &&
                    item.dataset.conversationKind === "group" &&
                    item.dataset.conversationArchived !== "true") ||
                (activeFilter === "archived" &&
                    item.dataset.conversationArchived === "true");
            item.hidden = !(matchesQuery && matchesFilter);
        });
    }

    if (search && conversations.length) {
        search.addEventListener("input", filterConversations);
        search.closest("form").addEventListener("submit", (event) => {
            if (search.value.trim()) return;
            event.preventDefault();
        });
    }

    filterButtons.forEach((button) => {
        button.addEventListener("click", () => {
            activeFilter = button.dataset.conversationFilter;
            filterButtons.forEach((item) =>
                item.classList.toggle("active", item === button)
            );
            filterConversations();
        });
    });

    const messageInput = document.getElementById("message-input");
    if (messageInput?.tagName === "TEXTAREA") {
        const resize = () => {
            messageInput.style.height = "auto";
            messageInput.style.height = `${Math.min(messageInput.scrollHeight, 112)}px`;
        };
        messageInput.addEventListener("input", resize);
        messageInput.addEventListener("keydown", (event) => {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                messageInput.form.requestSubmit();
                requestAnimationFrame(resize);
            }
        });
    }

    document.querySelectorAll('.message-form input[type="file"]').forEach((field) => {
        field.addEventListener("change", () => {
            const old = document.querySelector(".attachment-chip");
            old?.remove();
            if (!field.files.length) return;
            document.querySelectorAll('.message-form input[type="file"]').forEach((other) => {
                if (other !== field) other.value = "";
            });
            const chip = document.createElement("div");
            chip.className = "attachment-chip";
            chip.textContent = field.files[0].name;
            const remove = document.createElement("button");
            remove.type = "button";
            remove.textContent = "×";
            remove.setAttribute("aria-label", "Remove attachment");
            remove.addEventListener("click", () => {
                field.value = "";
                chip.remove();
            });
            chip.appendChild(remove);
            document.getElementById("message-error").before(chip);
        });
    });
})();
