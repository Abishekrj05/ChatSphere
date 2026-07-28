(() => {
    const input = document.getElementById("message-input");
    const status = document.getElementById("typing-status");

    if (!input) return;

    let timer;

    function sendTyping(isTyping) {
        if (window.chatSocket?.readyState === WebSocket.OPEN) {
            window.chatSocket.send(JSON.stringify({
                type: "typing",
                is_typing: isTyping,
            }));
        }
    }

    input.addEventListener("input", () => {
        sendTyping(true);
        clearTimeout(timer);
        timer = setTimeout(() => sendTyping(false), 900);
    });

    const interval = setInterval(() => {
        if (!window.chatSocket) return;
        clearInterval(interval);

        window.chatSocket.addEventListener("message", (event) => {
            const data = JSON.parse(event.data);
            if (data.type === "typing" && status) {
                status.textContent = data.is_typing
                    ? `${data.username} is typing...`
                    : "Online";
            }
        });
    }, 100);
})();
