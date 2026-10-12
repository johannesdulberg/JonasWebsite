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
        // Nur sichtbare Bilder: ausgefilterte und die ausgeblendete Ersatzliste der Collage zählen nicht.
        items = [...group.querySelectorAll("[data-lightbox-item]")].filter((el) => el.getClientRects().length);
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

// Foto-Bibliothek: Filter ohne Neuladen und Collage am Desktop.
(() => {
    const collage = document.querySelector("[data-collage]");
    if (!collage) return;
    const source = collage.querySelector("[data-collage-source]");
    const items = [...source.querySelectorAll("[data-collage-item]")];
    const empty = document.querySelector("[data-collage-empty]");
    const desktop = window.matchMedia("(min-width: 768px)");

    // Ein Baustein: 12 Spalten x 6 Zeilen, 7 Felder ohne Lücken.
    // [Spalte von, bis, Zeile von, bis, Form] mit Form q = quer, h = hoch.
    const BLOCK = [
        [1, 5, 1, 3, "q"], [5, 8, 1, 5, "h"], [8, 13, 1, 4, "q"], [1, 5, 3, 5, "q"],
        [8, 11, 4, 7, "q"], [11, 13, 4, 7, "h"], [1, 8, 5, 7, "q"],
    ];

    const tile = (item, style) => {
        const link = item.querySelector("a").cloneNode(true);
        link.setAttribute("style", style);
        return link;
    };

    const layout = () => {
        collage.querySelector("[data-collage-view]")?.remove();
        const visible = items.filter((item) => !item.hidden);
        if (empty) empty.hidden = visible.length > 0;
        source.hidden = desktop.matches && visible.length > 0;
        if (!desktop.matches || !visible.length) return;

        const view = document.createElement("div");
        view.dataset.collageView = "";
        view.className = "grid gap-2";
        let rest = visible;
        let flip = false;
        while (rest.length >= BLOCK.length) {
            // Querformate in breite Felder, Hochformate in hohe, soweit vorhanden.
            const wide = rest.filter((item) => Number(item.dataset.ratio) >= 1);
            const tall = rest.filter((item) => Number(item.dataset.ratio) < 1);
            const chosen = BLOCK.map(([, , , , form]) =>
                (form === "h" ? tall : wide).shift() || (form === "h" ? wide : tall).shift());
            rest = rest.filter((item) => !chosen.includes(item));
            const block = document.createElement("div");
            block.className = "grid grid-cols-12 grid-rows-6 gap-2 h-[clamp(420px,46vw,640px)]";
            chosen.forEach((item, n) => {
                let [a, b, c, d] = BLOCK[n];
                if (flip) [a, b] = [14 - b, 14 - a];
                block.append(tile(item, `grid-column:${a}/${b};grid-row:${c}/${d}`));
            });
            view.append(block);
            flip = !flip;
        }
        if (rest.length) {
            // Was nicht mehr für einen Baustein reicht: eine Zeile, gleich hoch, volle Breite.
            const row = document.createElement("div");
            row.className = "flex gap-2 h-[clamp(200px,22vw,320px)]";
            rest.forEach((item) => row.append(tile(item, `flex:${item.dataset.ratio} 1 0`)));
            view.append(row);
        }
        collage.append(view);
    };

    const select = (slug) => {
        items.forEach((item) => { item.hidden = Boolean(slug) && !item.dataset.tags.split(" ").includes(slug); });
        document.querySelectorAll("[data-filter]").forEach((link) => {
            if (link.dataset.filter === slug) link.setAttribute("aria-current", "true");
            else link.removeAttribute("aria-current");
        });
        layout();
    };

    document.querySelectorAll("[data-filter]").forEach((link) => {
        link.addEventListener("click", (event) => {
            if (event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) return;
            event.preventDefault();
            history.replaceState(null, "", link.href);
            select(link.dataset.filter);
        });
    });
    desktop.addEventListener("change", layout);
    layout();
})();
