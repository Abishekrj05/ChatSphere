(() => {
    const conversationElement = document.getElementById("conversation-id");
    const userElement = document.getElementById("current-user-id");

    if (!conversationElement || !userElement) return;

    const conversationId = JSON.parse(conversationElement.textContent);
    const currentUserId = JSON.parse(userElement.textContent);
    const presenceElement = document.getElementById("presence-visible");
    const presenceVisible = presenceElement ? JSON.parse(presenceElement.textContent) : true;

    let socket;
    let reconnectTimer;

    const form = document.getElementById("message-form");
    const input = document.getElementById("message-input");
    const messageList = document.getElementById("message-list");
    const errorBox = document.getElementById("message-error");
    const fileInputs = Array.from(form.querySelectorAll('input[type="file"]'));
    const csrfToken = form.querySelector('[name="csrfmiddlewaretoken"]').value;
    const replyPreview = document.getElementById("reply-preview");
    const typingStatus = document.getElementById("typing-status");
    let baseStatus = typingStatus?.textContent.trim() || "";
    let replyToId = null;

    const searchToggle = document.getElementById("chat-search-toggle");
    const searchPanel = document.getElementById("chat-search-panel");
    const searchInput = document.getElementById("chat-search-input");
    const searchClose = document.getElementById("chat-search-close");
    const searchCount = document.getElementById("chat-search-count");

    function filterMessages() {
        const query = searchInput.value.trim().toLowerCase();
        let matches = 0;
        messageList.querySelectorAll("[data-message-id]").forEach((message) => {
            const visible = !query ||
                message.dataset.content.toLowerCase().includes(query) ||
                message.dataset.sender.toLowerCase().includes(query);
            message.hidden = !visible;
            message.classList.toggle("search-match", Boolean(query && visible));
            if (query && visible) matches += 1;
        });
        messageList.querySelectorAll(".date-divider").forEach((divider) => {
            divider.hidden = Boolean(query);
        });
        searchCount.textContent = query ? `${matches} found` : "";
    }

    function closeSearch() {
        searchPanel.hidden = true;
        searchInput.value = "";
        filterMessages();
    }

    searchToggle?.addEventListener("click", () => {
        searchPanel.hidden = false;
        searchInput.focus();
    });
    searchClose?.addEventListener("click", closeSearch);
    searchInput?.addEventListener("input", filterMessages);
    searchInput?.addEventListener("keydown", (event) => {
        if (event.key === "Escape") closeSearch();
    });

    document.querySelector("[data-jump-message]")?.addEventListener("click", (event) => {
        const message = messageList.querySelector(
            `[data-message-id="${event.currentTarget.dataset.jumpMessage}"]`
        );
        if (!message) return;
        message.scrollIntoView({ behavior: "smooth", block: "center" });
        message.classList.add("message-flash");
        setTimeout(() => message.classList.remove("message-flash"), 1400);
    });

    function connectSocket() {
        if (socket && [WebSocket.CONNECTING, WebSocket.OPEN].includes(socket.readyState)) {
            return;
        }
        if (typingStatus) typingStatus.textContent = "connecting…";
        socket = new WebSocket(
            window.ChatSphere.websocketUrl(`/ws/chat/${conversationId}/`)
        );
        window.chatSocket = socket;

        socket.addEventListener("open", () => {
            clearTimeout(reconnectTimer);
            document.body.classList.remove("chat-disconnected");
            input.disabled = false;
            input.placeholder = "Type a message";
            if (typingStatus) typingStatus.textContent = baseStatus;
        });
        socket.addEventListener("message", handleSocketMessage);
        socket.addEventListener("error", () => {
            if (typingStatus) typingStatus.textContent = "connection problem";
        });
        socket.addEventListener("close", (event) => {
            document.body.classList.add("chat-disconnected");
            input.disabled = true;
            input.placeholder = "Reconnecting…";
            if (typingStatus) typingStatus.textContent = "reconnecting…";
            clearTimeout(reconnectTimer);
            if (![4401, 4403].includes(event.code)) {
                reconnectTimer = setTimeout(connectSocket, 1800);
            } else if (typingStatus) {
                typingStatus.textContent = event.code === 4401 ? "signed out" : "access denied";
            }
        });
    }

    function scrollToBottom() {
        messageList.scrollTop = messageList.scrollHeight;
    }

    function appendMessage(data) {
        const wrapper = document.createElement("article");
        wrapper.className = "chat-message";
        wrapper.dataset.messageId = data.id;
        wrapper.dataset.sender = data.sender || "";
        wrapper.dataset.content = data.content || "";

        if (Number(data.sender_id) === Number(currentUserId)) {
            wrapper.classList.add("mine");
        }

        if (
            data.sender &&
            document.body.dataset.groupChat === "true" &&
            Number(data.sender_id) !== Number(currentUserId)
        ) {
            const sender = document.createElement("strong");
            sender.textContent = data.sender;
            wrapper.appendChild(sender);
        }
        if (data.is_forwarded) {
            const forwarded = document.createElement("span");
            forwarded.className = "forwarded-label";
            forwarded.textContent = "↪ Forwarded";
            wrapper.appendChild(forwarded);
        }

        if (data.reply_to) {
            const reply = document.createElement("blockquote");
            reply.className = "reply-context";
            reply.textContent = `${data.reply_to.sender}: ${data.reply_to.content}`;
            wrapper.appendChild(reply);
        }

        if (data.content) {
            const text = document.createElement("div");
            text.className = "message-content";
            text.textContent = data.content;
            wrapper.appendChild(text);
        }

        if (data.image_url) {
            const imageLink = document.createElement("a");
            imageLink.href = data.image_url;
            imageLink.target = "_blank";
            imageLink.rel = "noopener";
            const image = document.createElement("img");
            image.src = data.image_url;
            image.alt = "Shared image";
            imageLink.appendChild(image);
            wrapper.appendChild(imageLink);
        }

        if (data.document_url) {
            const link = document.createElement("a");
            link.href = data.document_url;
            link.className = "document-card";
            link.target = "_blank";
            link.rel = "noopener";
            const icon = document.createElement("span");
            icon.className = "document-icon";
            icon.textContent = "↧";
            const copy = document.createElement("span");
            const name = document.createElement("strong");
            name.textContent = data.document_name || "Open document";
            const type = document.createElement("small");
            type.textContent = "Document";
            copy.append(name, type);
            link.append(icon, copy);
            wrapper.appendChild(link);
        }

        if (data.voice_note_url) {
            const audio = document.createElement("audio");
            audio.src = data.voice_note_url;
            audio.controls = true;
            wrapper.appendChild(audio);
        }

        const time = document.createElement("small");
        time.textContent = new Date(data.created_at).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
        });

        const meta = document.createElement("footer");
        meta.className = "message-meta";
        meta.appendChild(time);
        if (Number(data.sender_id) === Number(currentUserId) && !data.is_deleted) {
            const tick = document.createElement("span");
            tick.className = `read-tick${data.status === "read" ? " read" : ""}`;
            tick.dataset.messageStatus = data.id;
            tick.textContent = data.status === "sent" ? "✓" : "✓✓";
            tick.title = data.status[0].toUpperCase() + data.status.slice(1);
            time.append(" ", tick);
        }
        wrapper.appendChild(meta);
        addMessageActions(wrapper, Number(data.sender_id) === Number(currentUserId));
        messageList.appendChild(wrapper);
        scrollToBottom();
    }

    function addMessageActions(wrapper, mine) {
        const menu = document.createElement("details");
        menu.className = "message-menu";
        const summary = document.createElement("summary");
        summary.textContent = "⌄";
        summary.setAttribute("aria-label", "Message actions");
        const actions = document.createElement("div");
        actions.className = "message-menu-popover";
        const addButton = (action, label, emoji = "", parent = actions) => {
            const button = document.createElement("button");
            button.type = "button";
            button.dataset.messageAction = action;
            if (emoji) button.dataset.emoji = emoji;
            button.textContent = label;
            if (action === "delete") button.className = "destructive-action";
            parent.appendChild(button);
        };
        addButton("reply", "Reply");
        addButton("pin", "Pin");
        if (mine) {
            addButton("edit", "Edit");
        }
        addButton("delete", "Delete");
        menu.append(summary, actions);
        wrapper.appendChild(menu);

        const quick = document.createElement("div");
        quick.className = "quick-reaction";
        const quickToggle = document.createElement("button");
        quickToggle.type = "button";
        quickToggle.dataset.reactionToggle = "";
        quickToggle.setAttribute("aria-label", "React to message");
        quickToggle.textContent = "☺";
        const tray = document.createElement("div");
        tray.className = "quick-reaction-tray";
        ["👍", "❤️", "😂", "😮", "😢", "🙏"].forEach((emoji) =>
            addButton("react", emoji, emoji, tray)
        );
        quick.append(quickToggle, tray);
        wrapper.appendChild(quick);
    }

    function updateReactions(wrapper, reactions) {
        let summary = wrapper.querySelector(".reaction-summary");
        if (!summary) {
            summary = document.createElement("div");
            summary.className = "reaction-summary";
            wrapper.querySelector(".message-meta").before(summary);
        }
        summary.replaceChildren();
        reactions.forEach((reaction) => {
            const item = document.createElement("span");
            item.textContent = `${reaction.emoji} ${reaction.count}`;
            summary.appendChild(item);
        });
    }

    async function postAction(url, body) {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken,
                ...(body instanceof FormData ? {} : { "Content-Type": "application/json" }),
            },
            body,
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "The action could not be completed.");
        return data;
    }

    function clearReply() {
        replyToId = null;
        replyPreview.hidden = true;
        replyPreview.querySelector("span").textContent = "";
    }

    replyPreview.querySelector("button").addEventListener("click", clearReply);

    messageList.addEventListener("click", async (event) => {
        const reactionToggle = event.target.closest("[data-reaction-toggle]");
        if (reactionToggle) {
            event.stopPropagation();
            const quick = reactionToggle.closest(".quick-reaction");
            messageList.querySelectorAll(".quick-reaction.open").forEach((item) => {
                if (item !== quick) item.classList.remove("open");
            });
            quick.classList.toggle("open");
            return;
        }
        const button = event.target.closest("[data-message-action]");
        if (!button) return;
        const wrapper = button.closest("[data-message-id]");
        const id = wrapper.dataset.messageId;
        const action = button.dataset.messageAction;
        errorBox.textContent = "";
        button.closest("details")?.removeAttribute("open");
        button.closest(".quick-reaction")?.classList.remove("open");

        try {
            if (action === "reply") {
                replyToId = id;
                replyPreview.querySelector("span").textContent =
                    `Replying to ${wrapper.dataset.sender}: ${wrapper.dataset.content.slice(0, 80)}`;
                replyPreview.hidden = false;
                input.focus();
            } else if (action === "edit") {
                const content = window.ChatDialogs
                    ? await window.ChatDialogs.prompt("Edit message", wrapper.dataset.content)
                    : window.prompt("Edit message", wrapper.dataset.content);
                if (content !== null && content.trim()) {
                    await postAction(`/messages/${id}/edit/`, JSON.stringify({ content }));
                }
            } else if (action === "delete") {
                const mine = wrapper.classList.contains("mine");
                const scope = window.ChatDialogs?.deleteMessage
                    ? await window.ChatDialogs.deleteMessage(mine)
                    : (window.confirm("Delete this message?") ? (mine ? "everyone" : "me") : null);
                if (scope) {
                    const result = await postAction(
                        `/messages/${id}/delete/`,
                        JSON.stringify({ scope })
                    );
                    if (result.scope === "me") wrapper.remove();
                }
            } else if (action === "react") {
                const formData = new FormData();
                formData.append("emoji", button.dataset.emoji);
                await postAction(`/messages/${id}/react/`, formData);
            } else if (action === "pin") {
                await postAction(`/messages/${id}/pin/`, "{}");
            }
        } catch (error) {
            errorBox.textContent = error.message;
        }
    });

    messageList.addEventListener("toggle", (event) => {
        if (!event.target.matches(".message-menu") || !event.target.open) return;
        messageList.querySelectorAll(".message-menu[open]").forEach((menu) => {
            if (menu !== event.target) menu.removeAttribute("open");
        });
    }, true);

    document.addEventListener("click", (event) => {
        if (!event.target.closest(".quick-reaction")) {
            messageList.querySelectorAll(".quick-reaction.open").forEach((item) =>
                item.classList.remove("open")
            );
        }
        if (event.target.closest(".message-menu")) return;
        messageList.querySelectorAll(".message-menu[open]").forEach((menu) =>
            menu.removeAttribute("open")
        );
    });

    function handleSocketMessage(event) {
        const data = JSON.parse(event.data);
        if (data.type === "typing" && typingStatus) {
            typingStatus.textContent = data.is_typing
                ? `${data.username} is typing…`
                : baseStatus;
        }
        if (data.type === "presence" && typingStatus && presenceVisible) {
            baseStatus = data.is_online ? "online" : "last seen recently";
            typingStatus.textContent = baseStatus;
        }
        if (data.type === "error") {
            errorBox.textContent = data.message || "The message could not be sent.";
        }
        if (data.type === "message") appendMessage(data);
        if (data.type === "message_event") {
            const wrapper = messageList.querySelector(
                `[data-message-id="${data.message_id}"]`
            );
            if (!wrapper) return;
            if (data.action === "edited") {
                wrapper.dataset.content = data.content;
                wrapper.querySelector(".message-content").textContent = data.content;
                const small = wrapper.querySelector(".message-meta small");
                if (!small.textContent.includes("edited")) small.append(" · edited");
            } else if (data.action === "deleted") {
                wrapper.classList.add("deleted");
                wrapper.querySelector(".message-content").innerHTML = "<em>Message deleted</em>";
                wrapper.querySelectorAll("img, audio, .message-menu").forEach((item) => item.remove());
            } else if (data.action === "reactions") {
                updateReactions(wrapper, data.reactions);
            } else if (data.action === "pinned") {
                let pin = wrapper.querySelector(".pin-indicator");
                if (data.is_pinned && !pin) {
                    pin = document.createElement("span");
                    pin.className = "pin-indicator";
                    pin.textContent = "Pinned";
                    wrapper.querySelector(".message-meta").prepend(pin);
                } else if (!data.is_pinned && pin) {
                    pin.remove();
                }
            } else if (data.action === "status") {
                const tick = wrapper.querySelector("[data-message-status]");
                if (tick) {
                    tick.textContent = data.status === "sent" ? "✓" : "✓✓";
                    tick.title = data.status[0].toUpperCase() + data.status.slice(1);
                    tick.classList.toggle("read", data.status === "read");
                }
            }
        }
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const message = input.value.trim();
        const hasFile = fileInputs.some((field) => field.files.length);

        if (!message && !hasFile) return;
        errorBox.textContent = "";

        if (hasFile) {
            const submitButton = form.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            try {
                const formData = new FormData(form);
                if (replyToId) formData.append("reply_to", replyToId);
                const response = await fetch(form.dataset.uploadUrl, {
                    method: "POST",
                    body: formData,
                    headers: { "X-Requested-With": "XMLHttpRequest" },
                });
                if (!response.ok) {
                    const data = await response.json();
                    const errors = Object.values(data.errors || {})
                        .flat()
                        .map((item) => item.message)
                        .join(" ");
                    throw new Error(errors || "The attachment could not be sent.");
                }
                form.reset();
                document.querySelector(".attachment-chip")?.remove();
                clearReply();
                input.focus();
            } catch (error) {
                errorBox.textContent = error.message;
            } finally {
                submitButton.disabled = false;
                const progress = document.getElementById("upload-progress");
                if (progress) progress.hidden = true;
            }
            return;
        }

        if (socket.readyState !== WebSocket.OPEN) {
            errorBox.textContent = "The connection is unavailable. Refresh the page.";
            return;
        }

        socket.send(JSON.stringify({
            type: "message",
            message,
            reply_to: replyToId,
        }));
        input.value = "";
        clearReply();
        input.focus();
    });

    connectSocket();
    scrollToBottom();
})();
