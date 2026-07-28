window.ChatSphere = window.ChatSphere || {};

window.ChatSphere.websocketUrl = function (path) {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    return `${protocol}://${window.location.host}${path}`;
};
