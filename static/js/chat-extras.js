(() => {
    const form = document.getElementById("message-form");
    const conversationNode = document.getElementById("conversation-id");
    if (!form || !conversationNode) return;
    const conversationId = JSON.parse(conversationNode.textContent);
    const csrf = form.querySelector("[name=csrfmiddlewaretoken]").value;
    const errorBox = document.getElementById("message-error");
    const progress = document.getElementById("upload-progress");
    const voiceButton = document.getElementById("voice-record-button");
    const voiceInput = form.querySelector('input[name="voice_note"]');

    function openDialog({ title, message = "", value = null, confirmText = "OK", danger = false }) {
        return new Promise((resolve) => {
            const dialog = document.createElement("dialog");
            dialog.className = "app-dialog";
            const panel = document.createElement("form");
            panel.method = "dialog";
            const heading = document.createElement("h2");
            heading.textContent = title;
            panel.appendChild(heading);
            if (message) {
                const copy = document.createElement("p");
                copy.textContent = message;
                panel.appendChild(copy);
            }
            let input;
            if (value !== null) {
                input = document.createElement("textarea");
                input.value = value;
                input.maxLength = 4000;
                input.rows = 4;
                panel.appendChild(input);
            }
            const actions = document.createElement("div");
            actions.className = "app-dialog-actions";
            const cancel = document.createElement("button");
            cancel.type = "button";
            cancel.className = "secondary-button";
            cancel.textContent = "Cancel";
            const confirm = document.createElement("button");
            confirm.type = "submit";
            confirm.className = danger ? "danger-button" : "primary-button";
            confirm.textContent = confirmText;
            actions.append(cancel, confirm);
            panel.appendChild(actions);
            dialog.appendChild(panel);
            document.body.appendChild(dialog);
            const finish = (result) => {
                dialog.close();
                dialog.remove();
                resolve(result);
            };
            cancel.addEventListener("click", () => finish(null));
            dialog.addEventListener("cancel", (event) => {
                event.preventDefault(); finish(null);
            });
            panel.addEventListener("submit", (event) => {
                event.preventDefault();
                finish(input ? input.value.trim() : true);
            });
            dialog.showModal();
            (input || confirm).focus();
        });
    }
    window.ChatDialogs = {
        confirm: (title, message, confirmText = "Confirm", danger = false) =>
            openDialog({ title, message, confirmText, danger }),
        prompt: (title, value) => openDialog({ title, value, confirmText: "Save" }),
        info: (title, message) => openDialog({ title, message, confirmText: "Close" }),
        deleteMessage: (mine) => new Promise((resolve) => {
            const dialog = document.createElement("dialog");
            dialog.className = "app-dialog delete-message-dialog";
            const panel = document.createElement("div");
            const title = document.createElement("h2");
            title.textContent = "Delete message?";
            const copy = document.createElement("p");
            copy.textContent = mine
                ? "Choose whether to remove this message only for you or for everyone."
                : "This message will be removed only from your chat.";
            const actions = document.createElement("div");
            actions.className = "delete-choice-actions";
            const addChoice = (label, value, className = "") => {
                const button = document.createElement("button");
                button.type = "button";
                button.textContent = label;
                button.className = className;
                button.addEventListener("click", () => finish(value));
                actions.appendChild(button);
            };
            addChoice("Delete for me", "me");
            if (mine) addChoice("Delete for everyone", "everyone", "destructive-action");
            addChoice("Cancel", null);
            panel.append(title, copy, actions);
            dialog.appendChild(panel);
            document.body.appendChild(dialog);
            const finish = (value) => {
                dialog.close();
                dialog.remove();
                resolve(value);
            };
            dialog.addEventListener("cancel", (event) => {
                event.preventDefault();
                finish(null);
            });
            dialog.showModal();
        }),
    };

    async function post(url, formData) {
        const response = await fetch(url, {
            method: "POST", headers: { "X-CSRFToken": csrf }, body: formData,
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Unable to complete this action.");
        return data;
    }

    document.addEventListener("click", async (event) => {
        const actionButton = event.target.closest("[data-conversation-action]");
        if (actionButton) {
            const action = actionButton.dataset.conversationAction;
            if (["clear", "block"].includes(action)) {
                const approved = await window.ChatDialogs.confirm(
                    action === "clear" ? "Clear this chat?" : "Change blocked status?",
                    action === "clear"
                        ? "Messages will be hidden from your chat history. This cannot be undone."
                        : "This changes whether you and this person can exchange messages.",
                    action === "clear" ? "Clear chat" : "Continue",
                    true,
                );
                if (!approved) return;
            }
            const data = new FormData();
            data.append("action", action);
            try {
                await post(`/chat/${conversationId}/action/`, data);
                if (["archive", "clear"].includes(action)) location.href = "/chats/";
                else location.reload();
            } catch (error) { errorBox.textContent = error.message; }
            return;
        }
        const inviteButton = event.target.closest("[data-copy-invite]");
        if (inviteButton) {
            await navigator.clipboard.writeText(inviteButton.dataset.copyInvite);
            inviteButton.textContent = "Invite link copied";
            return;
        }
        const messageButton = event.target.closest("[data-message-action]");
        if (!messageButton) return;
        const message = messageButton.closest("[data-message-id]");
        const id = message?.dataset.messageId;
        if (messageButton.dataset.messageAction === "copy") {
            await navigator.clipboard.writeText(message.dataset.content);
        } else if (messageButton.dataset.messageAction === "info") {
            const response = await fetch(`/messages/${id}/info/`);
            const data = await response.json();
            await window.ChatDialogs.info(
                "Message information",
                `Status: ${data.status}\nSent: ${new Date(data.sent_at).toLocaleString()}${data.delivered_at ? `\nDelivered: ${new Date(data.delivered_at).toLocaleString()}` : ""}${data.read_at ? `\nRead: ${new Date(data.read_at).toLocaleString()}` : ""}`
            );
        } else if (messageButton.dataset.messageAction === "forward") {
            openForwardDialog(id);
        }
    });

    function openForwardDialog(messageId) {
        const conversations = [...document.querySelectorAll("[data-conversation-id]")];
        const dialog = document.createElement("dialog");
        dialog.className = "forward-dialog";
        dialog.innerHTML = `<form method="dialog"><header><strong>Forward message</strong><button value="cancel" aria-label="Close">×</button></header><div class="forward-targets"></div></form>`;
        const targets = dialog.querySelector(".forward-targets");
        conversations.forEach((item) => {
            const button = document.createElement("button");
            button.type = "button";
            button.textContent = item.dataset.conversationTitle;
            button.addEventListener("click", async () => {
                const data = new FormData();
                data.append("conversation_id", item.dataset.conversationId);
                try {
                    await post(`/messages/${messageId}/forward/`, data);
                    dialog.close(); dialog.remove();
                } catch (error) { errorBox.textContent = error.message; }
            });
            targets.appendChild(button);
        });
        document.body.appendChild(dialog);
        dialog.addEventListener("close", () => dialog.remove());
        dialog.showModal();
    }

    let recorder;
    let chunks = [];
    let timer;
    let startedAt;
    voiceButton?.addEventListener("click", async () => {
        if (recorder?.state === "recording") {
            recorder.stop();
            return;
        }
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            recorder = new MediaRecorder(stream);
            chunks = [];
            recorder.addEventListener("dataavailable", (event) => chunks.push(event.data));
            recorder.addEventListener("stop", () => {
                clearInterval(timer);
                const blob = new Blob(chunks, { type: recorder.mimeType || "audio/webm" });
                const file = new File([blob], `voice-${Date.now()}.webm`, { type: blob.type });
                const transfer = new DataTransfer();
                transfer.items.add(file);
                voiceInput.files = transfer.files;
                stream.getTracks().forEach((track) => track.stop());
                voiceButton.classList.remove("recording");
                voiceButton.textContent = "●";
                form.requestSubmit();
            });
            recorder.start();
            startedAt = Date.now();
            voiceButton.classList.add("recording");
            timer = setInterval(() => {
                const seconds = Math.floor((Date.now() - startedAt) / 1000);
                voiceButton.textContent = `■ ${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
            }, 500);
        } catch (_) {
            errorBox.textContent = "Microphone permission is required to record a voice message.";
        }
    });

    form.addEventListener("submit", () => {
        if ([...form.querySelectorAll('input[type="file"]')].some((field) => field.files.length)) {
            progress.hidden = false;
            progress.querySelector("span").style.width = "70%";
        }
    });

    const list = document.getElementById("message-list");
    ["dragenter", "dragover"].forEach((name) => list.addEventListener(name, (event) => {
        event.preventDefault(); list.classList.add("dragging-file");
    }));
    ["dragleave", "drop"].forEach((name) => list.addEventListener(name, (event) => {
        event.preventDefault(); list.classList.remove("dragging-file");
    }));
    list.addEventListener("drop", (event) => {
        const file = event.dataTransfer.files[0];
        if (!file) return;
        const target = file.type.startsWith("image/") ?
            form.querySelector('input[name="image"]') :
            (file.type.startsWith("audio/") ? voiceInput : form.querySelector('input[name="document"]'));
        const transfer = new DataTransfer();
        transfer.items.add(file);
        target.files = transfer.files;
        target.dispatchEvent(new Event("change", { bubbles: true }));
    });
})();
