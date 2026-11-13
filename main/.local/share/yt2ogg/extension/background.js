// Holds the native host's port for as long as a download runs - an open
// native port keeps this worker alive - and says how it ended. The popup
// cannot: it closes as soon as the download starts.

const HOST = "yt2ogg";

// The badge too, since macOS may keep the notification from showing; the
// popup clears it when next opened.
function notify(title, message, ok) {
    chrome.notifications.create({ type: "basic", iconUrl: "icons/icon128.png", title, message });
    chrome.action.setBadgeBackgroundColor({ color: ok ? "#1e8e3e" : "#d70015" });
    chrome.action.setBadgeText({ text: ok ? "\u2713" : "!" });
    chrome.action.setTitle({ title: title + ": " + message });
}

chrome.runtime.onMessage.addListener((m, sender, respond) => {
    if (sender.id !== chrome.runtime.id || !m.download) return;
    const port = chrome.runtime.connectNative(HOST);
    let started = false;
    port.onMessage.addListener((r) => {
        if (!started) {
            started = true;
            respond(r);
            if (!r.ok) port.disconnect();
            return;
        }
        if (!r.done) return;
        if (r.ok) notify("Saved", r.name, true);
        else notify("Not saved: " + r.name, r.error + (r.log ? "\n" + r.log : ""), false);
        port.disconnect();
    });
    port.onDisconnect.addListener(() => {
        const error = chrome.runtime.lastError?.message || "the native host closed";
        if (!started) {
            started = true;
            respond({
                ok: false,
                error: /not found/i.test(error)
                    ? "the native host is not registered - run 'yt2ogg --register'"
                    : error,
            });
        }
    });
    port.postMessage(m.download);
    return true;
});
