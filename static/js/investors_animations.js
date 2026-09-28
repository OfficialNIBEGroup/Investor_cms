// Investor page visual enhancements only — does not touch tab-switching logic in Main.js

document.addEventListener("DOMContentLoaded", function () {

    // 1) Fade/slide up ONLY the glance stat cards (always visible on page load).
    // NOTE: We deliberately do NOT apply this to .table-wrapper / .financial-list /
    // .Stackholders-table, because many of those (e.g. Stock Exchange Disclosures,
    // per-financial-year tables) start hidden with inline style="display:none" and
    // are revealed later via onclick handlers in Main.js. An IntersectionObserver
    // never fires on elements that are display:none, so animating them would leave
    // that content permanently invisible even after the user opens that tab.
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add("revealed");
                revealObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.15 });

    document.querySelectorAll(".glance-card").forEach(el => {
        revealObserver.observe(el);
    });

    // 2) Animate the numeric counters in the "At a Glance" strip
    const counters = document.querySelectorAll(".glance-number[data-count]");
    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            const el = entry.target;
            const target = parseInt(el.getAttribute("data-count"), 10);
            let current = 0;
            const duration = 900;
            const stepTime = Math.max(Math.floor(duration / target), 30);

            const timer = setInterval(() => {
                current += 1;
                el.textContent = current;
                if (current >= target) {
                    el.textContent = target;
                    clearInterval(timer);
                }
            }, stepTime);

            counterObserver.unobserve(el);
        });
    }, { threshold: 0.5 });

    counters.forEach(el => counterObserver.observe(el));
});
