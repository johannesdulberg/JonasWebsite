// Terminbuchung, vorerst nur Oberfläche.
//
// Freie Zeiten entstehen aus den Arbeitszeiten in data-hours (z. B.
// "1,2,3,4,5;09:00-12:00,13:00-17:00") im Abstand von data-step Minuten, für
// die nächsten data-weeks Wochen. Vergangene Zeiten fallen weg, gebucht wird
// noch nichts. Später liefert der Server die freien Zeiten.
(() => {
    const root = document.querySelector("[data-booking]");
    if (!root) return;

    const $ = (selector) => root.ownerDocument.querySelector(selector);
    const [dayPart, rangePart] = root.dataset.hours.split(";");
    const workdays = dayPart.split(",").map(Number); // 1 = Montag … 7 = Sonntag
    const ranges = rangePart.split(",").map((range) => range.split("-").map((t) => {
        const [h, m] = t.split(":").map(Number);
        return h * 60 + m;
    }));
    const step = Number(root.dataset.step) || 30;
    const weeks = Number(root.dataset.weeks) || 6;

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const lastDay = new Date(today);
    lastDay.setDate(lastDay.getDate() + weeks * 7);

    const isoWeekday = (date) => ((date.getDay() + 6) % 7) + 1;
    const sameDay = (a, b) => a && b && a.toDateString() === b.toDateString();
    const pad = (n) => String(n).padStart(2, "0");
    const fmtTime = (minutes) => `${pad(Math.floor(minutes / 60))}:${pad(minutes % 60)}`;
    const fmtDay = (date) => date.toLocaleDateString("de-DE", { weekday: "long", day: "numeric", month: "long" });

    const slotsFor = (date) => {
        if (!workdays.includes(isoWeekday(date)) || date < today || date > lastDay) return [];
        const now = new Date();
        const times = [];
        ranges.forEach(([start, end]) => {
            for (let t = start; t + step <= end; t += step) {
                const when = new Date(date);
                when.setHours(0, t, 0, 0);
                // Heute nur Zeiten, die mindestens eine Stunde in der Zukunft liegen.
                if (when - now > 60 * 60 * 1000) times.push(t);
            }
        });
        return times;
    };

    let month = new Date(today.getFullYear(), today.getMonth(), 1);
    let chosenDay = null;
    let chosenTime = null;

    const toggles = {};
    root.ownerDocument.querySelectorAll("[data-booking-toggle]").forEach((button) => {
        toggles[button.dataset.bookingToggle] = button;
    });
    const panel = (name) => root.ownerDocument.querySelector(`[data-booking-panel="${name}"]`);
    const setOpen = (name, open) => {
        toggles[name].setAttribute("aria-expanded", String(open));
        panel(name).toggleAttribute("data-open", open);
    };
    const isOpen = (name) => toggles[name].getAttribute("aria-expanded") === "true";

    // ---------------------------------------------------------------- Kalender
    const renderCalendar = () => {
        $("[data-booking-month-label]").textContent = month.toLocaleDateString("de-DE", { month: "long", year: "numeric" });
        const days = $("[data-booking-days]");
        days.replaceChildren();
        const offset = isoWeekday(month) - 1;
        for (let i = 0; i < offset; i += 1) days.append(document.createElement("span"));

        const count = new Date(month.getFullYear(), month.getMonth() + 1, 0).getDate();
        for (let d = 1; d <= count; d += 1) {
            const date = new Date(month.getFullYear(), month.getMonth(), d);
            const free = slotsFor(date).length > 0;
            const button = document.createElement("button");
            button.type = "button";
            button.textContent = d;
            button.disabled = !free;
            button.setAttribute("aria-label", fmtDay(date));
            const selected = sameDay(date, chosenDay);
            button.className = "aspect-square rounded-full text-sm transition-colors " + (
                selected ? "bg-accent text-paper font-medium"
                    : free ? "font-medium hover:bg-black/5"
                        : "text-black/20 cursor-default");
            if (sameDay(date, today) && !selected) button.classList.add("underline", "underline-offset-4");
            button.addEventListener("click", () => chooseDay(date));
            days.append(button);
        }

        const first = new Date(today.getFullYear(), today.getMonth(), 1);
        const last = new Date(lastDay.getFullYear(), lastDay.getMonth(), 1);
        root.querySelector('[data-booking-month="-1"]').disabled = month <= first;
        root.querySelector('[data-booking-month="1"]').disabled = month >= last;
    };

    root.querySelectorAll("[data-booking-month]").forEach((button) => {
        button.addEventListener("click", () => {
            month = new Date(month.getFullYear(), month.getMonth() + Number(button.dataset.bookingMonth), 1);
            renderCalendar();
        });
    });

    // ------------------------------------------------------------------ Zeiten
    const renderSlots = () => {
        const box = $("[data-booking-slots]");
        box.replaceChildren();
        slotsFor(chosenDay).forEach((t) => {
            const button = document.createElement("button");
            button.type = "button";
            button.textContent = fmtTime(t);
            const selected = t === chosenTime;
            button.className = "rounded-md border py-2.5 text-sm transition-colors " + (
                selected ? "border-accent bg-accent text-paper font-medium" : "border-line hover:border-ink");
            button.addEventListener("click", () => chooseTime(t));
            box.append(button);
        });
    };

    const update = () => {
        const dayLabel = $("[data-booking-day-label]");
        dayLabel.textContent = chosenDay ? fmtDay(chosenDay) : "Tag wählen";
        dayLabel.classList.toggle("text-muted", !chosenDay);

        const timeLabel = $("[data-booking-time-label]");
        timeLabel.textContent = chosenTime !== null ? `${fmtTime(chosenTime)} Uhr` : chosenDay ? "Uhrzeit wählen" : "Erst einen Tag wählen";
        timeLabel.classList.toggle("text-muted", chosenTime === null);
        toggles.slots.disabled = !chosenDay;

        $("[data-booking-next]").disabled = chosenTime === null;
    };

    const chooseDay = (date) => {
        if (!sameDay(date, chosenDay)) chosenTime = null;
        chosenDay = date;
        renderCalendar();
        renderSlots();
        update();
        setOpen("calendar", false);
        setOpen("slots", true);
    };

    const chooseTime = (t) => {
        chosenTime = t;
        renderSlots();
        update();
        setOpen("slots", false);
        $("[data-booking-next]").focus();
    };

    toggles.calendar.addEventListener("click", () => {
        const open = !isOpen("calendar");
        setOpen("calendar", open);
        if (open) setOpen("slots", false);
    });
    toggles.slots.addEventListener("click", () => {
        const open = !isOpen("slots");
        setOpen("slots", open);
        if (open) setOpen("calendar", false);
    });
    toggles.message.addEventListener("click", () => setOpen("message", !isOpen("message")));

    // ------------------------------------------------------------- Schritt 2
    const step1 = root.querySelector('[data-booking-step="1"]');
    const step2 = root.querySelector('[data-booking-step="2"]');
    $("[data-booking-next]").addEventListener("click", () => {
        $("[data-booking-summary]").textContent = `${fmtDay(chosenDay)}, ${fmtTime(chosenTime)} Uhr`;
        step1.hidden = true;
        step2.hidden = false;
        step2.querySelector("input").focus();
    });
    root.querySelector("[data-booking-back]").addEventListener("click", () => {
        step2.hidden = true;
        step1.hidden = false;
    });
    step2.addEventListener("submit", (event) => {
        event.preventDefault();
        root.querySelector("[data-booking-note]").hidden = false;
    });

    // Den ersten Monat mit freien Tagen zeigen (am Monatsende ist das der nächste).
    const firstFree = new Date(today);
    while (firstFree <= lastDay && !slotsFor(firstFree).length) firstFree.setDate(firstFree.getDate() + 1);
    month = new Date(firstFree.getFullYear(), firstFree.getMonth(), 1);

    renderCalendar();
    update();
})();
