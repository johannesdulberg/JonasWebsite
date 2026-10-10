// Menü-Knopf auf schmalen Bildschirmen: klappt die Hauptnavigation auf und zu.
document.querySelectorAll("[data-nav-toggle]").forEach((button) => {
    const nav = document.getElementById(button.getAttribute("aria-controls"));
    if (!nav) return;
    button.addEventListener("click", () => {
        const open = button.getAttribute("aria-expanded") === "true";
        button.setAttribute("aria-expanded", String(!open));
        nav.classList.toggle("hidden", open);
    });
});

// Bildreihen (data-strip): Pfeile blättern um knapp eine Ansichtsbreite und
// verschwinden am jeweiligen Ende.
document.querySelectorAll("[data-strip]").forEach((strip) => {
    const track = strip.querySelector("[data-strip-track]");
    const prev = strip.querySelector("[data-strip-prev]");
    const next = strip.querySelector("[data-strip-next]");
    if (!track || !prev || !next) return;

    const update = () => {
        const max = track.scrollWidth - track.clientWidth;
        prev.hidden = track.scrollLeft <= 1;
        next.hidden = track.scrollLeft >= max - 1;
    };
    const page = (direction) => track.scrollBy({ left: direction * track.clientWidth * 0.8 });

    prev.addEventListener("click", () => page(-1));
    next.addEventListener("click", () => page(1));
    track.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    // Die Breite steht erst fest, wenn die Bilder ihre Maße kennen.
    window.addEventListener("load", update);
    update();
});

// Videos (data-autoplay-visible) laufen nur, solange sie sichtbar sind.
if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) entry.target.play().catch(() => {});
            else entry.target.pause();
        });
    }, { threshold: 0.25 });
    document.querySelectorAll("video[data-autoplay-visible]").forEach((video) => observer.observe(video));
}

// Formular, das noch nichts verschickt: Absenden abfangen und das offen sagen.
document.querySelectorAll("form[data-inactive-form]").forEach((form) => {
    form.addEventListener("submit", (event) => {
        event.preventDefault();
        const note = form.querySelector("[data-form-note]");
        if (note) note.hidden = false;
    });
});

// Großansicht: Ein Klick auf ein Galeriebild (data-lightbox-item) öffnet es groß.
// Blättern lässt sich durch alle Bilder desselben Bereichs (data-lightbox-group),
// mit den Pfeilen, den Pfeiltasten oder per Wischen. Esc oder das X schließt.
(() => {
    const groups = document.querySelectorAll("[data-lightbox-group]");
    if (!groups.length || typeof HTMLDialogElement === "undefined") return;

    const icon = (path) =>
        `<svg class="size-9" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="${path}" /></svg>`;
    const buttonClass = "absolute flex size-12 items-center justify-center transition-colors hover:text-accent";

    const dialog = document.createElement("dialog");
    dialog.setAttribute("aria-label", "Großansicht");
    dialog.className = "m-0 h-dvh max-h-none w-screen max-w-none bg-paper p-0 text-ink backdrop:bg-paper";
    dialog.innerHTML = `
        <div class="flex h-full flex-col">
            <div class="flex min-h-0 flex-1 items-center justify-center px-3 pt-16 md:px-28" data-lightbox-stage>
                <img class="max-h-full max-w-full object-contain" alt="" data-lightbox-image>
            </div>
            <p class="flex h-20 shrink-0 items-center justify-center px-6 text-center text-sm" data-lightbox-caption></p>
        </div>
        <button type="button" class="${buttonClass} left-2 top-2 hidden md:flex" data-lightbox-fullscreen aria-label="Vollbild">${icon("M6 15V6h9M30 21v9h-9M6 6l9 9M30 30l-9-9")}</button>
        <button type="button" class="${buttonClass} right-2 top-2" data-lightbox-close aria-label="Schließen">${icon("M7 7l22 22M29 7L7 29")}</button>
        <button type="button" class="${buttonClass} left-1 top-1/2 -translate-y-1/2 md:left-6" data-lightbox-prev aria-label="Vorheriges Bild">${icon("M22 6L10 18l12 12")}</button>
        <button type="button" class="${buttonClass} right-1 top-1/2 -translate-y-1/2 md:right-6" data-lightbox-next aria-label="Nächstes Bild">${icon("M14 6l12 12-12 12")}</button>`;
    document.body.append(dialog);

    const image = dialog.querySelector("[data-lightbox-image]");
    const caption = dialog.querySelector("[data-lightbox-caption]");
    const prev = dialog.querySelector("[data-lightbox-prev]");
    const next = dialog.querySelector("[data-lightbox-next]");
    const fullscreen = dialog.querySelector("[data-lightbox-fullscreen]");
    if (!dialog.requestFullscreen) fullscreen.remove();

    let items = [];
    let index = 0;
    let opener = null;

    const show = (position) => {
        index = (position + items.length) % items.length;
        const item = items[index];
        image.src = item.href;
        image.alt = item.dataset.caption || "";
        caption.textContent = item.dataset.caption || "";
        // Die Nachbarn vorladen, damit das Blättern nicht wartet.
        [index - 1, index + 1].forEach((neighbour) => {
            const other = items[(neighbour + items.length) % items.length];
            if (other) new Image().src = other.href;
        });
    };

    const open = (group, item) => {
        items = [...group.querySelectorAll("[data-lightbox-item]")];
        opener = item;
        prev.hidden = next.hidden = items.length < 2;
        show(items.indexOf(item));
        document.documentElement.classList.add("overflow-hidden");
        dialog.showModal();
    };

    groups.forEach((group) => {
        group.addEventListener("click", (event) => {
            const item = event.target.closest("[data-lightbox-item]");
            // Mit Strg/Cmd oder mittlerer Maustaste bleibt es ein normaler Link.
            if (!item || event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) return;
            event.preventDefault();
            open(group, item);
        });
    });

    prev.addEventListener("click", () => show(index - 1));
    next.addEventListener("click", () => show(index + 1));
    dialog.querySelector("[data-lightbox-close]").addEventListener("click", () => dialog.close());
    fullscreen.addEventListener("click", () => {
        if (document.fullscreenElement) document.exitFullscreen();
        else dialog.requestFullscreen().catch(() => {});
    });

    dialog.addEventListener("keydown", (event) => {
        if (items.length < 2) return;
        if (event.key === "ArrowLeft") show(index - 1);
        if (event.key === "ArrowRight") show(index + 1);
    });

    // Klick neben das Bild schließt, wie bei einem Hintergrund.
    dialog.querySelector("[data-lightbox-stage]").addEventListener("click", (event) => {
        if (event.target === event.currentTarget) dialog.close();
    });

    // Wischen auf Touch-Geräten.
    let startX = null;
    dialog.addEventListener("touchstart", (event) => { startX = event.changedTouches[0].clientX; }, { passive: true });
    dialog.addEventListener("touchend", (event) => {
        if (startX === null || items.length < 2) return;
        const distance = event.changedTouches[0].clientX - startX;
        if (Math.abs(distance) > 50) show(index + (distance < 0 ? 1 : -1));
        startX = null;
    }, { passive: true });

    dialog.addEventListener("close", () => {
        document.documentElement.classList.remove("overflow-hidden");
        if (document.fullscreenElement) document.exitFullscreen();
        image.removeAttribute("src");
        if (opener) opener.focus();
    });
})();
