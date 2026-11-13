// The popup is the whole extension: it reads the tab's video, asks the
// native host what yt2ogg would call it and what tags.conf already says,
// and hands what was confirmed to the service worker, which runs the
// download and reports it by notification, so the popup may close at once.

const HOST = "yt2ogg";
const FIELDS = ["lang", "genre", "mood"];
const $ = (id) => document.getElementById(id);

function ask(message) {
    return chrome.runtime.sendNativeMessage(HOST, message).catch((e) => ({
        ok: false,
        error: /not found/i.test(e.message)
            ? "the native host is not registered - run 'yt2ogg --register'"
            : e.message,
    }));
}

function say(text, bad) {
    $("status").textContent = text;
    $("status").className = bad ? "bad" : "";
    $("status").hidden = false;
}

// watch?v=, youtu.be/, shorts/ and music.youtube.com all name the same ID.
function videoId(raw) {
    let u;
    try { u = new URL(raw); } catch { return null; }
    const host = u.hostname.replace(/^(www|m|music)\./, "");
    if (host === "youtu.be") return u.pathname.slice(1, 12);
    if (host !== "youtube.com") return null;
    if (u.pathname === "/watch") return u.searchParams.get("v");
    const m = u.pathname.match(/^\/(?:shorts|live)\/([\w-]{11})/);
    return m && m[1];
}

// A field tags.conf has a value for is shown, not asked: it is edited there.
// One it lacks gets an input, with the words already in use as chips that
// add or remove themselves.
function renderFields(info) {
    const box = $("fields");
    box.replaceChildren();
    for (const f of FIELDS) {
        const label = document.createElement("label");
        label.textContent = f + " ";
        if (info.have[f]) {
            const v = document.createElement("span");
            v.className = "known";
            v.textContent = info.have[f].join(", ");
            label.append(v);
            box.append(label);
            continue;
        }
        const input = document.createElement("input");
        input.id = f;
        input.autocomplete = "off";
        input.placeholder = "comma separated, empty to skip";
        const chips = document.createElement("div");
        chips.className = "chips";
        const values = () => input.value.split(",").map((s) => s.trim()).filter(Boolean);
        const sync = () => {
            const on = new Set(values());
            for (const c of chips.children) c.classList.toggle("on", on.has(c.textContent));
        };
        for (const word of info.vocab[f] || []) {
            const c = document.createElement("span");
            c.className = "chip";
            c.textContent = word;
            c.addEventListener("click", () => {
                const v = values();
                input.value = (v.includes(word) ? v.filter((x) => x !== word) : [...v, word]).join(", ");
                sync();
            });
            chips.append(c);
        }
        input.addEventListener("input", sync);
        label.append(input, chips);
        box.append(label);
    }
}

// An edited artist or title may be one tags.conf knows.
async function refresh() {
    const artist = $("artist").value.trim(), title = $("title").value.trim();
    if (!artist || !title) return;
    const info = await ask({ action: "known", artist, title });
    if (info.ok) renderFields(info);
}

async function main() {
    // The last download's outcome has been seen.
    chrome.action.setBadgeText({ text: "" });
    chrome.action.setTitle({ title: "Save to the music library" });
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const id = tab && tab.url && videoId(tab.url);
    if (!id || !/^[\w-]{11}$/.test(id)) {
        say("Open a YouTube video to save it.");
        return;
    }
    const info = await ask({ action: "guess", id });
    if (!info.ok) {
        say(info.error, true);
        return;
    }
    $("artist").value = info.artist;
    $("title").value = info.title;
    renderFields(info);
    $("status").hidden = true;
    $("form").hidden = false;
    // For videos titled "Song - Artist", the other way round from the guess.
    $("swap").addEventListener("click", () => {
        [$("artist").value, $("title").value] = [$("title").value, $("artist").value];
        refresh();
    });
    $("artist").addEventListener("change", refresh);
    $("title").addEventListener("change", refresh);
    $("form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const msg = { action: "download", id, artist: $("artist").value, title: $("title").value };
        for (const f of FIELDS) if ($(f)) msg[f] = $(f).value;
        $("form").querySelector("button").disabled = true;
        // Through the service worker, which outlives the popup and posts
        // the notification when the download ends.
        const r = await chrome.runtime.sendMessage({ download: msg })
            .catch((err) => ({ ok: false, error: err.message }));
        if (!r.ok) {
            say(r.error, true);
            $("form").querySelector("button").disabled = false;
            return;
        }
        $("form").hidden = true;
        say("Downloading - a notification will say when it is saved.");
        setTimeout(() => window.close(), 1500);
    });
}

main();
