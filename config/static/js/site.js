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
