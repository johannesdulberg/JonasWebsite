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
