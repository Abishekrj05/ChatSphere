(() => {
    const form = document.getElementById("ai-form");
    if (!form) return;

    const input = document.getElementById("ai-input");
    const list = document.getElementById("ai-message-list");
    const welcome = document.getElementById("ai-welcome");
    const errorBox = document.getElementById("ai-error");
    const submit = form.querySelector('button[type="submit"]');
    const clearButton = document.getElementById("clear-ai-chat");
    const csrfToken = form.querySelector('[name="csrfmiddlewaretoken"]').value;
    const storageKey = "chatsphere-ai-history-v1";
    let history = [];

    function resizeInput() {
        input.style.height = "auto";
        input.style.height = `${Math.min(input.scrollHeight, 140)}px`;
    }

    function scrollToBottom() {
        list.scrollTop = list.scrollHeight;
    }

    function appendMessage(text, role, save = true) {
        welcome.hidden = true;
        const row = document.createElement("div");
        row.className = `ai-message-row ${role}`;

        const avatar = document.createElement("span");
        avatar.className = "ai-message-avatar";
        avatar.textContent = role === "user" ? "You" : "AI";

        const bubble = document.createElement("div");
        bubble.className = "ai-message-bubble";
        bubble.textContent = text;
        row.append(avatar, bubble);
        list.appendChild(row);

        if (save) {
            history.push({ role, content: text });
            history = history.slice(-20);
            localStorage.setItem(storageKey, JSON.stringify(history));
        }
        scrollToBottom();
        return row;
    }

    function showThinking() {
        const row = document.createElement("div");
        row.className = "ai-message-row assistant thinking-row";
        const avatar = document.createElement("span");
        avatar.className = "ai-message-avatar";
        avatar.textContent = "AI";
        const dots = document.createElement("div");
        dots.className = "ai-thinking";
        dots.innerHTML = "<span></span><span></span><span></span>";
        row.append(avatar, dots);
        list.appendChild(row);
        scrollToBottom();
        return row;
    }

    function loadHistory() {
        try {
            const stored = JSON.parse(localStorage.getItem(storageKey) || "[]");
            if (!Array.isArray(stored)) return;
            history = stored
                .filter((item) =>
                    ["user", "assistant"].includes(item?.role) &&
                    typeof item?.content === "string"
                )
                .slice(-20);
            history.forEach((item) => appendMessage(item.content, item.role, false));
        } catch {
            localStorage.removeItem(storageKey);
        }
    }

    async function sendPrompt(prompt) {
        if (!prompt || submit.disabled) return;
        const previousHistory = [...history];
        appendMessage(prompt, "user");
        input.value = "";
        resizeInput();
        errorBox.textContent = "";
        submit.disabled = true;
        const thinking = showThinking();

        try {
            const response = await fetch(form.dataset.endpoint, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken,
                },
                body: JSON.stringify({
                    message: prompt,
                    history: previousHistory.slice(-10),
                }),
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || "The assistant is unavailable.");
            }
            thinking.remove();
            appendMessage(data.reply, "assistant");
        } catch (error) {
            thinking.remove();
            errorBox.textContent = error.message;
        } finally {
            submit.disabled = false;
            input.focus();
        }
    }

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        sendPrompt(input.value.trim());
    });

    input.addEventListener("input", resizeInput);
    input.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            form.requestSubmit();
        }
    });

    document.querySelectorAll("[data-ai-prompt]").forEach((button) => {
        button.addEventListener("click", () => sendPrompt(button.dataset.aiPrompt));
    });

    clearButton.addEventListener("click", () => {
        if (history.length && !window.confirm("Clear this AI conversation?")) return;
        history = [];
        localStorage.removeItem(storageKey);
        list.querySelectorAll(".ai-message-row").forEach((item) => item.remove());
        welcome.hidden = false;
        errorBox.textContent = "";
        input.focus();
    });

    loadHistory();
    resizeInput();
})();
