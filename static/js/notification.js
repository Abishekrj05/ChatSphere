(() => {
    if (!window.ChatSphere) return;
    let socket;
    let reconnectTimer;

    function showNotification(data) {
        if (data.type !== "notification") return;
        document.querySelectorAll("[data-notification-count]").forEach((badge) => {
            badge.textContent = String(Number(badge.textContent || 0) + 1);
            badge.hidden = false;
        });

        const toast = document.createElement("a");
        toast.className = "notification-toast";
        toast.href = data.id ? `/notifications/${data.id}/open/` : "/notifications/";
        const title = document.createElement("strong");
        title.textContent = data.title;
        const body = document.createElement("span");
        body.textContent = data.message;
        toast.append(title, body);
        document.body.appendChild(toast);
        requestAnimationFrame(() => toast.classList.add("visible"));
        setTimeout(() => {
            toast.classList.remove("visible");
            setTimeout(() => toast.remove(), 250);
        }, 4500);

        if (document.body.dataset.notificationSounds === "true") {
            try {
                const context = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = context.createOscillator();
                const gain = context.createGain();
                oscillator.frequency.value = 720;
                gain.gain.setValueAtTime(.05, context.currentTime);
                gain.gain.exponentialRampToValueAtTime(.001, context.currentTime + .18);
                oscillator.connect(gain).connect(context.destination);
                oscillator.start();
                oscillator.stop(context.currentTime + .18);
                oscillator.addEventListener("ended", () => context.close());
            } catch (_) {}
        }
        if (document.body.dataset.desktopNotifications === "true" &&
            "Notification" in window && Notification.permission === "granted" &&
            document.visibilityState !== "visible") {
            new Notification(data.title, { body: data.message });
        }
    }

    function connect() {
        socket = new WebSocket(window.ChatSphere.websocketUrl("/ws/notifications/"));
        socket.addEventListener("message", (event) => {
            try { showNotification(JSON.parse(event.data)); } catch (_) {}
        });
        socket.addEventListener("open", () => clearTimeout(reconnectTimer));
        socket.addEventListener("close", (event) => {
            clearTimeout(reconnectTimer);
            if (![4401, 4403].includes(event.code)) reconnectTimer = setTimeout(connect, 2500);
        });
    }
    if (document.body.dataset.desktopNotifications === "true" &&
        "Notification" in window && Notification.permission === "default") {
        Notification.requestPermission();
    }
    connect();
})();
