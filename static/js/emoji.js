(() => {
    const toggle = document.getElementById("emoji-button");
    const picker = document.getElementById("emoji-bar");
    const input = document.getElementById("message-input");
    if (!toggle || !picker || !input) return;

    const categories = [
        { id: "recent", icon: "🕘", label: "Recent", emojis: "" },
        { id: "smileys", icon: "😀", label: "Smileys & emotion", emojis: "😀 😃 😄 😁 😆 😅 😂 🤣 😊 😇 🙂 🙃 😉 😌 😍 🥰 😘 😗 😙 😚 😋 😛 😝 😜 🤪 🤨 🧐 🤓 😎 🥸 🤩 🥳 😏 😒 😞 😔 😟 😕 🙁 ☹️ 😣 😖 😫 😩 🥺 😢 😭 😤 😠 😡 🤬 🤯 😳 🥵 🥶 😱 😨 😰 😥 😓 🤗 🤔 🫣 🤭 🫢 🫡 🤫 🫠 🤥 😶 🫥 😐 🫤 😑 😬 🙄 😯 😦 😧 😮 😲 🥱 😴 🤤 😪 😵 😵‍💫 🤐 🥴 🤢 🤮 🤧 😷 🤒 🤕 🤑 🤠 😈 👿 👹 👺 🤡 💩 👻 💀 ☠️ 👽 👾 🤖 🎃 😺 😸 😹 😻 😼 😽 🙀 😿 😾 ❤️ 🧡 💛 💚 💙 💜 🖤 🤍 🤎 💔 ❤️‍🔥 ❤️‍🩹 ❣️ 💕 💞 💓 💗 💖 💘 💝 💟 💋 💯 💢 💥 💫 💦 💨 🕳️ 💬 👁️‍🗨️ 🗨️ 🗯️ 💭 💤" },
        { id: "people", icon: "👋", label: "People & body", emojis: "👋 🤚 🖐️ ✋ 🖖 🫱 🫲 🫳 🫴 👌 🤌 🤏 ✌️ 🤞 🫰 🤟 🤘 🤙 👈 👉 👆 👇 ☝️ 🫵 👍 👎 ✊ 👊 🤛 🤜 👏 🙌 🫶 👐 🤲 🤝 🙏 ✍️ 💅 🤳 💪 🦾 🦵 🦿 🦶 👂 🦻 👃 🧠 🫀 🫁 🦷 🦴 👀 👁️ 👅 👄 🫦 👶 🧒 👦 👧 🧑 👱 👨 🧔 👩 🧓 👴 👵 🙍 🙎 🙅 🙆 💁 🙋 🧏 🙇 🤦 🤷 👮 👷 💂 🕵️ 👩‍⚕️ 👩‍🌾 👩‍🍳 👩‍🎓 👩‍🎤 👩‍🏫 👩‍🏭 👩‍💻 👩‍💼 👩‍🔧 👩‍🔬 👩‍🎨 👩‍🚒 👩‍✈️ 👩‍🚀 👩‍⚖️ 👰 🤵 👸 🤴 🥷 🦸 🦹 🧙 🧚 🧛 🧜 🧝 🧞 🧟 💆 💇 🚶 🧍 🧎 🏃 💃 🕺 🕴️ 👯 🧖 🧗 🤺 🏇 ⛷️ 🏂 🏌️ 🏄 🚣 🏊 ⛹️ 🏋️ 🚴 🚵 🤸 🤼 🤽 🤾 🤹 🧘 🛀 🛌 👭 👫 👬 💏 💑 👪 🗣️ 👤 👥 🫂" },
        { id: "nature", icon: "🐻", label: "Animals & nature", emojis: "🐶 🐱 🐭 🐹 🐰 🦊 🐻 🐼 🐻‍❄️ 🐨 🐯 🦁 🐮 🐷 🐽 🐸 🐵 🙈 🙉 🙊 🐒 🐔 🐧 🐦 🐤 🐣 🐥 🦆 🦅 🦉 🦇 🐺 🐗 🐴 🦄 🐝 🪱 🐛 🦋 🐌 🐞 🐜 🪰 🪲 🪳 🦟 🦗 🕷️ 🕸️ 🦂 🐢 🐍 🦎 🦖 🦕 🐙 🦑 🦐 🦞 🦀 🐡 🐠 🐟 🐬 🐳 🐋 🦈 🦭 🐊 🐅 🐆 🦓 🦍 🦧 🐘 🦛 🦏 🐪 🐫 🦒 🦘 🦬 🐃 🐂 🐄 🐎 🐖 🐏 🐑 🦙 🐐 🦌 🐕 🐩 🦮 🐕‍🦺 🐈 🐈‍⬛ 🪶 🐓 🦃 🦤 🦚 🦜 🦢 🦩 🕊️ 🐇 🦝 🦨 🦡 🦫 🦦 🦥 🐁 🐀 🐿️ 🦔 🐾 🐉 🐲 🌵 🎄 🌲 🌳 🌴 🪵 🌱 🌿 ☘️ 🍀 🎍 🪴 🎋 🍃 🍂 🍁 🍄 🐚 🪨 🌾 💐 🌷 🌹 🥀 🌺 🌸 🌼 🌻 🌞 🌝 🌛 🌜 🌚 🌕 🌖 🌗 🌘 🌑 🌒 🌓 🌔 🌙 🌎 🌍 🌏 🪐 💫 ⭐ 🌟 ✨ ⚡ ☄️ 💥 🔥 🌪️ 🌈 ☀️ 🌤️ ⛅ 🌥️ ☁️ 🌦️ 🌧️ ⛈️ 🌩️ 🌨️ ❄️ ☃️ ⛄ 🌬️ 💨 💧 💦 ☔ ☂️ 🌊 🌫️" },
        { id: "food", icon: "🍔", label: "Food & drink", emojis: "🍏 🍎 🍐 🍊 🍋 🍌 🍉 🍇 🍓 🫐 🍈 🍒 🍑 🥭 🍍 🥥 🥝 🍅 🍆 🥑 🥦 🥬 🥒 🌶️ 🫑 🌽 🥕 🫒 🧄 🧅 🥔 🍠 🫘 🥐 🥯 🍞 🥖 🥨 🧀 🥚 🍳 🧈 🥞 🧇 🥓 🥩 🍗 🍖 🌭 🍔 🍟 🍕 🫓 🥪 🥙 🧆 🌮 🌯 🫔 🥗 🥘 🫕 🥫 🍝 🍜 🍲 🍛 🍣 🍱 🥟 🦪 🍤 🍙 🍚 🍘 🍥 🥠 🥮 🍢 🍡 🍧 🍨 🍦 🥧 🧁 🍰 🎂 🍮 🍭 🍬 🍫 🍿 🍩 🍪 🌰 🥜 🍯 🥛 🍼 🫖 ☕ 🍵 🧃 🥤 🧋 🍶 🍺 🍻 🥂 🍷 🥃 🍸 🍹 🧉 🍾 🧊 🥄 🍴 🍽️ 🥣 🥡 🥢 🧂" },
        { id: "activities", icon: "⚽", label: "Activities", emojis: "⚽ 🏀 🏈 ⚾ 🥎 🎾 🏐 🏉 🥏 🎱 🪀 🏓 🏸 🏒 🏑 🥍 🏏 🪃 🥅 ⛳ 🪁 🏹 🎣 🤿 🥊 🥋 🎽 🛹 🛼 🛷 ⛸️ 🥌 🎿 ⛷️ 🏂 🪂 🏋️ 🤼 🤸 ⛹️ 🤺 🤾 🏌️ 🏇 🧘 🏄 🏊 🤽 🚣 🧗 🚵 🚴 🏆 🥇 🥈 🥉 🏅 🎖️ 🏵️ 🎗️ 🎫 🎟️ 🎪 🤹 🎭 🩰 🎨 🎬 🎤 🎧 🎼 🎹 🥁 🪘 🎷 🎺 🪗 🎸 🪕 🎻 🎲 ♟️ 🎯 🎳 🎮 🎰 🧩" },
        { id: "travel", icon: "🚗", label: "Travel & places", emojis: "🚗 🚕 🚙 🚌 🚎 🏎️ 🚓 🚑 🚒 🚐 🛻 🚚 🚛 🚜 🦯 🦽 🦼 🛴 🚲 🛵 🏍️ 🛺 🚨 🚔 🚍 🚘 🚖 🚡 🚠 🚟 🚃 🚋 🚞 🚝 🚄 🚅 🚈 🚂 🚆 🚇 🚊 🚉 ✈️ 🛫 🛬 🛩️ 💺 🛰️ 🚀 🛸 🚁 🛶 ⛵ 🚤 🛥️ 🛳️ ⛴️ 🚢 ⚓ 🪝 ⛽ 🚧 🚦 🚥 🗺️ 🗿 🗽 🗼 🏰 🏯 🏟️ 🎡 🎢 🎠 ⛲ ⛱️ 🏖️ 🏝️ 🏜️ 🌋 ⛰️ 🏔️ 🗻 🏕️ ⛺ 🛖 🏠 🏡 🏘️ 🏚️ 🏗️ 🏭 🏢 🏬 🏣 🏤 🏥 🏦 🏨 🏪 🏫 🏩 💒 🏛️ ⛪ 🕌 🛕 🕍 ⛩️ 🕋 🌅 🌄 🌠 🎇 🎆 🌇 🌆 🏙️ 🌃 🌌 🌉 🌁" },
        { id: "objects", icon: "💡", label: "Objects", emojis: "⌚ 📱 📲 💻 ⌨️ 🖥️ 🖨️ 🖱️ 🖲️ 🕹️ 🗜️ 💽 💾 💿 📀 📼 📷 📸 📹 🎥 📽️ 🎞️ 📞 ☎️ 📟 📠 📺 📻 🎙️ 🎚️ 🎛️ 🧭 ⏱️ ⏲️ ⏰ 🕰️ ⌛ ⏳ 📡 🔋 🪫 🔌 💡 🔦 🕯️ 🪔 🧯 🛢️ 💸 💵 💴 💶 💷 🪙 💰 💳 💎 ⚖️ 🪜 🧰 🪛 🔧 🔨 ⚒️ 🛠️ ⛏️ 🪚 🔩 ⚙️ 🪤 🧱 ⛓️ 🧲 🔫 💣 🧨 🪓 🔪 🗡️ ⚔️ 🛡️ 🚬 ⚰️ 🪦 ⚱️ 🔮 📿 🧿 🪬 💈 ⚗️ 🔭 🔬 🕳️ 🩹 🩺 💊 💉 🩸 🧬 🦠 🧫 🧪 🌡️ 🧹 🪠 🧺 🧻 🚽 🚿 🛁 🧼 🪥 🪒 🧽 🪣 🧴 🛎️ 🔑 🗝️ 🚪 🪑 🛋️ 🛏️ 🪞 🪟 🛍️ 🛒 🎁 🎈 🎏 🎀 🪄 🪅 🎊 🎉 🪩 🧸 🪆 🖼️ 🧵 🪡 🧶 🪢 👓 🕶️ 🥽 🥼 🦺 👔 👕 👖 🧣 🧤 🧥 🧦 👗 👘 🥻 🩱 🩲 🩳 👙 👚 👛 👜 👝 🛍️ 🎒 🩴 👞 👟 🥾 🥿 👠 👡 🩰 👢 👑 👒 🎩 🎓 🧢 🪖 ⛑️ 💄 💍 💼" },
        { id: "symbols", icon: "❤️", label: "Symbols", emojis: "🏧 🚮 🚰 ♿ 🚹 🚺 🚻 🚼 🚾 🛂 🛃 🛄 🛅 ⚠️ 🚸 ⛔ 🚫 🚳 🚭 🚯 🚱 🚷 📵 🔞 ☢️ ☣️ ⬆️ ↗️ ➡️ ↘️ ⬇️ ↙️ ⬅️ ↖️ ↕️ ↔️ ↩️ ↪️ ⤴️ ⤵️ 🔃 🔄 🔙 🔚 🔛 🔜 🔝 🛐 ⚛️ 🕉️ ✡️ ☸️ ☯️ ✝️ ☦️ ☪️ ☮️ 🕎 🔯 ♈ ♉ ♊ ♋ ♌ ♍ ♎ ♏ ♐ ♑ ♒ ♓ ⛎ 🔀 🔁 🔂 ▶️ ⏩ ⏭️ ⏯️ ◀️ ⏪ ⏮️ 🔼 ⏫ 🔽 ⏬ ⏸️ ⏹️ ⏺️ ⏏️ 🎦 🔅 🔆 📶 📳 📴 ♀️ ♂️ ⚧️ ✖️ ➕ ➖ ➗ 🟰 ♾️ ‼️ ⁉️ ❓ ❔ ❕ ❗ 〰️ 💱 💲 ⚕️ ♻️ ⚜️ 🔱 📛 🔰 ⭕ ✅ ☑️ ✔️ ❌ ❎ ➰ ➿ 〽️ ✳️ ✴️ ❇️ ©️ ®️ ™️ #️⃣ *️⃣ 0️⃣ 1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣ 8️⃣ 9️⃣ 🔟 🔠 🔡 🔢 🔣 🔤 🅰️ 🆎 🅱️ 🆑 🆒 🆓 ℹ️ 🆔 Ⓜ️ 🆕 🆖 🅾️ 🆗 🅿️ 🆘 🆙 🆚 🈁 🈂️ 🈷️ 🈶 🈯 🉐 🈹 🈚 🈲 🉑 🈸 🈴 🈳 ㊗️ ㊙️ 🈺 🈵 🔴 🟠 🟡 🟢 🔵 🟣 🟤 ⚫ ⚪ 🟥 🟧 🟨 🟩 🟦 🟪 🟫 ⬛ ⬜ ◼️ ◻️ ◾ ◽ ▪️ ▫️ 🔶 🔷 🔸 🔹 🔺 🔻 💠 🔘 🔳 🔲" },
        { id: "flags", icon: "🏳️", label: "Flags", emojis: "🏁 🚩 🎌 🏴 🏳️ 🏳️‍🌈 🏳️‍⚧️ 🏴‍☠️ 🇺🇳 🇮🇳 🇦🇺 🇧🇷 🇨🇦 🇨🇳 🇫🇷 🇩🇪 🇮🇩 🇮🇹 🇯🇵 🇲🇽 🇳🇱 🇳🇿 🇵🇰 🇵🇭 🇷🇺 🇸🇦 🇸🇬 🇿🇦 🇰🇷 🇪🇸 🇱🇰 🇸🇪 🇨🇭 🇹🇭 🇹🇷 🇦🇪 🇬🇧 🇺🇸 🇻🇳" }
    ];
    const aliases = {
        laugh: "😂 🤣", love: "😍 🥰 ❤️ 💕 💖", happy: "😀 😃 😄 😁 😊", sad: "😞 😔 😢 😭 ☹️",
        angry: "😠 😡 🤬", thanks: "🙏", pray: "🙏", okay: "👌 🆗", yes: "👍 ✅", no: "👎 ❌",
        party: "🥳 🎉 🎊", fire: "🔥", heart: "❤️ 🧡 💛 💚 💙 💜 🖤 🤍 🤎", hug: "🤗 🫂",
        kiss: "😘 💋", food: "🍔 🍕 🍟 🍜", drink: "☕ 🍵 🥤 🍺", dog: "🐶 🐕", cat: "🐱 🐈",
        car: "🚗 🚕", plane: "✈️", phone: "📱 ☎️", computer: "💻 🖥️", gift: "🎁", music: "🎵 🎶 🎧",
        india: "🇮🇳", flag: "🏁 🚩 🏳️", check: "✅ ✔️", warning: "⚠️", star: "⭐ 🌟"
    };
    const parse = (value) => value.trim() ? value.trim().split(/\s+/u) : [];
    categories.forEach((category) => { category.items = parse(category.emojis); });

    let recent = [];
    try { recent = JSON.parse(localStorage.getItem("chatEmojiRecent") || "[]"); } catch (_) {}
    recent = Array.isArray(recent) ? recent.slice(0, 32) : [];

    picker.innerHTML = `
        <div class="emoji-picker-head">
            <label><span>⌕</span><input type="search" class="emoji-search" placeholder="Search emoji" aria-label="Search emoji"></label>
            <select class="emoji-tone" aria-label="Emoji skin tone" title="Skin tone">
                <option value="">👋</option><option value="🏻">🏻</option><option value="🏼">🏼</option>
                <option value="🏽">🏽</option><option value="🏾">🏾</option><option value="🏿">🏿</option>
            </select>
            <button type="button" class="emoji-close" aria-label="Close emoji picker">&times;</button>
        </div>
        <div class="emoji-categories" role="tablist"></div>
        <div class="emoji-results" tabindex="0"></div>
        <div class="emoji-picker-foot">Choose an emoji</div>`;
    const search = picker.querySelector(".emoji-search");
    const tabs = picker.querySelector(".emoji-categories");
    const results = picker.querySelector(".emoji-results");
    const footer = picker.querySelector(".emoji-picker-foot");
    const tonePicker = picker.querySelector(".emoji-tone");
    const toneable = new Set(Array.from("👋🤚🖐✋🖖👌🤌🤏✌🤞🫰🤟🤘🤙👈👉👆👇☝🫵👍👎✊👊🤛🤜👏🙌🫶👐🤲🙏✍💅🤳💪🦵🦶👂👃"));

    categories.forEach((category) => {
        const tab = document.createElement("button");
        tab.type = "button";
        tab.dataset.category = category.id;
        tab.title = category.label;
        tab.setAttribute("role", "tab");
        tab.textContent = category.icon;
        tabs.appendChild(tab);
    });

    const insertEmoji = (emoji) => {
        const tone = tonePicker.value;
        if (tone && toneable.has(Array.from(emoji)[0]) && !/[🏻🏼🏽🏾🏿]/u.test(emoji)) {
            const parts = Array.from(emoji);
            emoji = parts[0] + tone + parts.slice(1).join("");
        }
        const start = input.selectionStart ?? input.value.length;
        const end = input.selectionEnd ?? input.value.length;
        input.setRangeText(emoji, start, end, "end");
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.focus();
        recent = [emoji, ...recent.filter((item) => item !== emoji)].slice(0, 32);
        try { localStorage.setItem("chatEmojiRecent", JSON.stringify(recent)); } catch (_) {}
    };

    const renderButtons = (items, emptyMessage = "No emojis found") => {
        results.innerHTML = "";
        if (!items.length) {
            results.innerHTML = `<div class="emoji-empty">${emptyMessage}</div>`;
            return;
        }
        const fragment = document.createDocumentFragment();
        items.forEach((emoji) => {
            const option = document.createElement("button");
            option.type = "button";
            option.className = "emoji-option";
            option.textContent = emoji;
            option.title = "Insert " + emoji;
            option.setAttribute("aria-label", "Insert emoji " + emoji);
            option.addEventListener("click", () => insertEmoji(emoji));
            fragment.appendChild(option);
        });
        results.appendChild(fragment);
    };

    const showCategory = (id) => {
        const category = categories.find((item) => item.id === id) || categories[1];
        tabs.querySelectorAll("button").forEach((tab) => {
            const active = tab.dataset.category === category.id;
            tab.classList.toggle("active", active);
            tab.setAttribute("aria-selected", String(active));
        });
        search.value = "";
        footer.textContent = category.label;
        renderButtons(category.id === "recent" ? recent : category.items,
            category.id === "recent" ? "Your recently used emojis will appear here." : "No emojis found");
        results.scrollTop = 0;
    };

    tabs.addEventListener("click", (event) => {
        const tab = event.target.closest("button[data-category]");
        if (tab) showCategory(tab.dataset.category);
    });
    search.addEventListener("input", () => {
        const term = search.value.trim().toLowerCase();
        if (!term) return showCategory("smileys");
        tabs.querySelectorAll("button").forEach((tab) => tab.classList.remove("active"));
        const matched = new Set();
        categories.slice(1).forEach((category) => {
            if (category.label.toLowerCase().includes(term) || category.id.includes(term)) {
                category.items.forEach((emoji) => matched.add(emoji));
            }
        });
        Object.entries(aliases).forEach(([name, emojis]) => {
            if (name.includes(term) || term.includes(name)) parse(emojis).forEach((emoji) => matched.add(emoji));
        });
        footer.textContent = `Search results for “${search.value.trim()}”`;
        renderButtons([...matched]);
    });

    const openPicker = () => {
        picker.classList.add("open");
        picker.setAttribute("aria-hidden", "false");
        toggle.setAttribute("aria-expanded", "true");
        showCategory(recent.length ? "recent" : "smileys");
        search.focus();
    };
    const closePicker = () => {
        picker.classList.remove("open");
        picker.setAttribute("aria-hidden", "true");
        toggle.setAttribute("aria-expanded", "false");
    };
    toggle.setAttribute("aria-haspopup", "dialog");
    toggle.setAttribute("aria-expanded", "false");
    picker.setAttribute("aria-hidden", "true");
    toggle.addEventListener("click", (event) => {
        event.stopPropagation();
        picker.classList.contains("open") ? closePicker() : openPicker();
    });
    picker.querySelector(".emoji-close").addEventListener("click", closePicker);
    document.addEventListener("click", (event) => {
        if (!picker.contains(event.target) && event.target !== toggle) closePicker();
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && picker.classList.contains("open")) closePicker();
    });
})();
