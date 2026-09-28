// Sitewide scroll-reveal for public pages (Home, About, Divisions, Contact, Investors).
// Not loaded on the CMS dashboard or login pages, which use a separate base template.
// Only targets elements that are visible on page load (no display:none toggled
// content on these pages), so there is no risk of content getting stuck hidden.

document.addEventListener("DOMContentLoaded", function () {

    const revealSelectors = [
        ".team-card", ".office-card", ".vision-card", ".info-card", ".accordion-item",
        ".component-card", ".bbg-product-card", ".bbg-wwd-card", ".bbg-vm-card",
        ".feature-box", ".cuas-image-card", ".emi-cap-card", ".media-card", ".lt-card",
        ".bbg-sustain-item", ".bbg-plant-spec-item", ".logo-item"
    ].join(", ");

    const elements = document.querySelectorAll(revealSelectors);

    elements.forEach(el => {
        // Skip anything that isn't actually rendered/visible on load
        // (defensive check, even though these pages have no hidden tabs).
        if (el.offsetParent === null) return;
        el.classList.add("js-reveal");
    });

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add("revealed");
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.12 });

    document.querySelectorAll(".js-reveal").forEach(el => observer.observe(el));
});
