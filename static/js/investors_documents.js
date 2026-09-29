/**
 * Public Investors page.
 * Fills every section from the admin panel's published documents.
 */
(function () {
    const ANNOUNCEMENT_GROUPS = [
        { bucket: "shareholder_notice", label: "Notice to Stakeholders" },
        { bucket: "newspaper_publication", label: "Newspaper Publication" },
        { bucket: "stock_exchange_disclosure", label: "Stock Exchange Disclosures" },
    ];

    const FORM_GROUPS = [
        { bucket: "kyc_nomination", label: "KYC and Nomination Form" },
        { bucket: "tax_declaration", label: "Tax Declaration for Dividend TDS" },
        { bucket: "unclaimed_dividend", label: "Unpaid or Unclaimed Dividend" },
    ];

    const SEBI_LABELS = {
        corporate_documents: "Corporate Documents",
        board_of_directors: "Board of Directors",
        board_committees: "Committee of Board of Directors",
        codes_policies: "Codes and Policies",
        investor_grievances: "Investor Grievance",
        other: "Other",
    };

    function escapeHtml(value) {
        if (value === null || value === undefined) return "";
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function yearNumber(year) {
        const match = String(year || "").match(/(\d{4})/);
        return match ? parseInt(match[1], 10) : 0;
    }

    function quarterLabel(quarter) {
        const match = String(quarter || "").toUpperCase().match(/Q\s*([1-4])/);
        if (match) return "Quarter " + match[1];
        return quarter || "-";
    }

    function quarterRank(quarter) {
        const match = String(quarter || "").toUpperCase().match(/Q\s*([1-4])/);
        return match ? Number(match[1]) : 99;
    }

    function documentHref(doc) {
        return doc.pdf_file || doc.external_url || "";
    }

    function documentLink(doc, label) {
        const text = label || doc.title || "View document";
        const href = documentHref(doc);
        if (!href) return escapeHtml(text);
        return `<a href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">${escapeHtml(text)}</a>`;
    }

    function emptyMessage(panel, title) {
        panel.innerHTML = `
            <h2>${escapeHtml(title)}</h2>
            <p class="investor-empty">No documents have been published in this section yet.</p>
        `;
    }

    function groupByYear(documents) {
        const groups = new Map();
        documents.forEach((doc) => {
            const year = doc.financial_year || "Other";
            if (!groups.has(year)) groups.set(year, []);
            groups.get(year).push(doc);
        });
        return Array.from(groups.entries()).sort((a, b) => {
            const delta = yearNumber(b[0]) - yearNumber(a[0]);
            if (delta) return delta;
            return String(b[0]).localeCompare(String(a[0]));
        });
    }

    function table(headers, rows) {
        const head = headers.map((header) => `<th>${escapeHtml(header)}</th>`).join("");
        const body = rows.length
            ? rows.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`).join("")
            : `<tr><td colspan="${headers.length}">No documents have been published in this section yet.</td></tr>`;
        return `
            <div class="table-wrapper">
                <table>
                    <thead><tr>${head}</tr></thead>
                    <tbody>${body}</tbody>
                </table>
            </div>
        `;
    }

    function yearMenu(title, years, backAction) {
        const items = years.map(([year]) => `
            <a href="#" class="financial-item" data-open-year="${escapeHtml(year)}">
                <span>Financial Year ${escapeHtml(year)}</span>
                <span class="arrow">&#8250;</span>
            </a>
        `).join("");
        const back = backAction
            ? `<div class="back-link" data-back="${escapeHtml(backAction)}">&#8249; Back</div>`
            : "";
        return `
            <h2>${escapeHtml(title)}</h2>
            ${back}
            <div class="financial-list">${items}</div>
        `;
    }

    function linkMenu(title, items, attribute) {
        const links = items.map((item) => `
            <a href="#" class="Announcements-item" ${attribute}="${escapeHtml(item.value)}">
                <span>${escapeHtml(item.label)}</span>
                <span class="arrow">&#8250;</span>
            </a>
        `).join("");
        return `
            <h2>${escapeHtml(title)}</h2>
            <div class="financial-list">${links}</div>
        `;
    }

    function headingBlock(title, subtitle, backAction) {
        return `
            <h2>${escapeHtml(title)}</h2>
            <div class="back-link" data-back="${escapeHtml(backAction)}">&#8249; Back</div>
            ${subtitle ? `<h3 class="investor-year-heading">${escapeHtml(subtitle)}</h3>` : ""}
        `;
    }

    function renderYearTable(section) {
        const rows = section.documents.map((doc, index) => [
            String(index + 1),
            escapeHtml(doc.financial_year || "-"),
            documentLink(doc),
        ]);
        return `<h2>${escapeHtml(section.name)}</h2>` + table(
            ["Sr No", "Financial Year", "Document"],
            rows
        );
    }

    function renderFinancialYear(panel, section, year) {
        const docs = section.documents
            .filter((doc) => (doc.financial_year || "Other") === year)
            .slice()
            .sort((a, b) => quarterRank(a.quarter) - quarterRank(b.quarter));
        const rows = docs.map((doc, index) => [
            String(index + 1),
            escapeHtml(quarterLabel(doc.quarter)),
            escapeHtml(doc.release_date || "-"),
            documentLink(doc),
        ]);
        panel.innerHTML = headingBlock(section.name, "Financial Year " + year, "years")
            + table(["Sr No.", "Quarter", "Date of Release", "Document"], rows);
    }

    function renderQuarterYear(panel, section, year) {
        const docs = section.documents
            .filter((doc) => (doc.financial_year || "Other") === year)
            .slice()
            .sort((a, b) => quarterRank(a.quarter) - quarterRank(b.quarter));
        const rows = docs.map((doc, index) => [
            String(index + 1),
            escapeHtml(quarterLabel(doc.quarter)),
            documentLink(doc),
        ]);
        panel.innerHTML = headingBlock(section.name, "Financial Year " + year, "years")
            + table(["Sr No.", "Quarter", "Document"], rows);
    }

    function renderDisclosureYear(panel, section, year, backAction) {
        const docs = section.documents.filter((doc) => (doc.financial_year || "Other") === year);
        const rows = docs.map((doc, index) => [
            String(index + 1),
            documentLink(doc),
            escapeHtml(doc.disclosure_date || "-"),
        ]);
        panel.innerHTML = headingBlock(section.name, "Financial Year " + year, backAction)
            + table(["Sr No.", "Document", "Date"], rows);
    }

    function renderSubsidiaryYear(panel, section, year) {
        const docs = section.documents.filter((doc) => (doc.financial_year || "Other") === year);
        const rows = docs.map((doc, index) => [
            String(index + 1),
            escapeHtml(doc.company_name || doc.title || "-"),
            escapeHtml(doc.financial_type || "-"),
            documentLink(doc, "View"),
        ]);
        panel.innerHTML = headingBlock(section.name, "Financial Year " + year, "years")
            + table(["Sr No.", "Company Name", "Type", "Document"], rows);
    }

    function renderNoticeTable(panel, section, docs) {
        const rows = docs.map((doc, index) => [
            String(index + 1),
            documentLink(doc),
            escapeHtml(doc.notice_type || "-"),
            escapeHtml(doc.financial_year || "-"),
            escapeHtml(doc.disclosure_date || "-"),
            escapeHtml(doc.meeting_date || "-"),
        ]);
        panel.innerHTML = headingBlock(section.name, "Notice to Stakeholders", "index")
            + table(
                ["Sr No.", "Document", "Notice Type", "Financial Year", "Disclosure Date", "Meeting Date"],
                rows
            );
    }

    function renderSimpleList(panel, section, title, subtitle, docs, backAction) {
        const rows = docs.map((doc, index) => {
            const detail = doc.description || doc.applicable_to || doc.dividend_type || doc.extra_info || "";
            return [
                String(index + 1),
                documentLink(doc),
                escapeHtml(detail || "-"),
            ];
        });
        panel.innerHTML = headingBlock(title, subtitle, backAction)
            + table(["Sr No.", "Document", "Details"], rows);
    }

    function renderCustom(section) {
        const rows = section.documents.map((doc, index) => [
            String(index + 1),
            documentLink(doc),
            escapeHtml(doc.extra_info || "-"),
        ]);
        return `<h2>${escapeHtml(section.name)}</h2>` + table(
            ["Sr No.", "Document", "Details"],
            rows
        );
    }

    function renderIndex(panel, section) {
        const docs = section.documents || [];
        panel.dataset.mode = "index";
        if (!docs.length) {
            emptyMessage(panel, section.name);
            return;
        }

        if (section.layout === "year_table") {
            panel.innerHTML = renderYearTable(section);
            return;
        }

        if (section.layout === "custom") {
            panel.innerHTML = renderCustom(section);
            return;
        }

        if (section.layout === "financial_results" || section.layout === "by_year" || section.layout === "subsidiary") {
            panel.innerHTML = yearMenu(section.name, groupByYear(docs), "");
            return;
        }

        if (section.layout === "announcements") {
            const items = ANNOUNCEMENT_GROUPS
                .filter((group) => docs.some((doc) => doc.bucket === group.bucket))
                .map((group) => ({ value: group.bucket, label: group.label }));
            panel.innerHTML = items.length
                ? linkMenu(section.name, items, "data-open-bucket")
                : "";
            if (!items.length) emptyMessage(panel, section.name);
            return;
        }

        if (section.layout === "investor_forms") {
            const known = new Set(FORM_GROUPS.map((group) => group.bucket));
            const items = FORM_GROUPS
                .filter((group) => docs.some((doc) => doc.bucket === group.bucket || doc.category === group.bucket))
                .map((group) => ({ value: group.bucket, label: group.label }));
            docs.forEach((doc) => {
                const bucket = doc.bucket || doc.category || "other";
                if (!known.has(bucket) && !items.some((item) => item.value === bucket)) {
                    items.push({
                        value: bucket,
                        label: bucket.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase()),
                    });
                }
            });
            panel.innerHTML = items.length
                ? linkMenu(section.name, items, "data-open-bucket")
                : "";
            if (!items.length) emptyMessage(panel, section.name);
            return;
        }

        if (section.layout === "sebi") {
            const categories = [];
            docs.forEach((doc) => {
                const value = doc.category || "other";
                if (!categories.some((item) => item.value === value)) {
                    categories.push({
                        value: value,
                        label: SEBI_LABELS[value] || value.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase()),
                    });
                }
            });
            panel.innerHTML = linkMenu(section.name, categories, "data-open-category");
        }
    }

    function openYear(panel, section, year) {
        if (section.layout === "financial_results") {
            renderFinancialYear(panel, section, year);
            return;
        }
        if (section.layout === "subsidiary") {
            renderSubsidiaryYear(panel, section, year);
            return;
        }
        if (section.layout === "announcements") {
            const bucket = panel.dataset.bucket || "";
            const docs = section.documents.filter((doc) => doc.bucket === bucket);
            const yearDocs = docs.filter((doc) => (doc.financial_year || "Other") === year);
            renderDisclosureYear(
                panel,
                Object.assign({}, section, { documents: yearDocs, name: section.name }),
                year,
                "bucket"
            );
            panel.dataset.bucket = bucket;
            return;
        }
        renderQuarterYear(panel, section, year);
    }

    function openBucket(panel, section, bucket) {
        panel.dataset.bucket = bucket;
        const docs = section.documents.filter((doc) => doc.bucket === bucket || doc.category === bucket);
        const label = ANNOUNCEMENT_GROUPS.concat(FORM_GROUPS).find((group) => group.bucket === bucket);
        const subtitle = label ? label.label : bucket;

        if (bucket === "shareholder_notice") {
            renderNoticeTable(panel, section, docs);
            panel.dataset.bucket = bucket;
            return;
        }

        if (bucket === "newspaper_publication" || bucket === "stock_exchange_disclosure") {
            panel.innerHTML = yearMenu(section.name, groupByYear(docs), "index");
            const heading = panel.querySelector("h2");
            if (heading) heading.insertAdjacentHTML("afterend", `<h3 class="investor-year-heading">${escapeHtml(subtitle)}</h3>`);
            return;
        }

        renderSimpleList(panel, section, section.name, subtitle, docs, "index");
    }

    function openCategory(panel, section, category) {
        const docs = section.documents.filter((doc) => (doc.category || "other") === category);
        const label = SEBI_LABELS[category] || category;
        renderSimpleList(panel, section, section.name, label, docs, "index");
    }

    function activate(key) {
        document.querySelectorAll("#investorMenu li").forEach((item) => {
            item.classList.toggle("active", item.dataset.key === key);
        });
        document.querySelectorAll("#investorPanels .tab-content").forEach((panel) => {
            panel.classList.toggle("active-content", panel.dataset.key === key);
        });
    }

    function renderPage(sections) {
        const menu = document.getElementById("investorMenu");
        const panels = document.getElementById("investorPanels");
        if (!menu || !panels) return;

        menu.innerHTML = "";
        panels.innerHTML = "";

        if (!sections.length) {
            menu.innerHTML = `<li><a href="#">No sections available</a></li>`;
            panels.innerHTML = `
                <div class="tab-content active-content">
                    <h2>Investor Updates</h2>
                    <p class="investor-empty">No documents have been published yet.</p>
                </div>
            `;
            return;
        }

        sections.forEach((section, index) => {
            const item = document.createElement("li");
            item.dataset.key = section.key;
            if (index === 0) item.classList.add("active");
            item.innerHTML = `
                <a href="#">
                    <i class="fa-solid ${escapeHtml(section.icon || "fa-folder")}"></i>
                    ${escapeHtml(section.name)}
                </a>
            `;
            item.querySelector("a").addEventListener("click", function (event) {
                event.preventDefault();
                activate(section.key);
            });
            menu.appendChild(item);

            const panel = document.createElement("div");
            panel.className = "tab-content" + (index === 0 ? " active-content" : "");
            panel.dataset.key = section.key;
            panel.dataset.layout = section.layout;
            renderIndex(panel, section);
            panels.appendChild(panel);
        });

        panels.onclick = function (event) {
            const panel = event.target.closest(".tab-content");
            if (!panel) return;
            const section = sections.find((item) => item.key === panel.dataset.key);
            if (!section) return;

            const yearLink = event.target.closest("[data-open-year]");
            const bucketLink = event.target.closest("[data-open-bucket]");
            const categoryLink = event.target.closest("[data-open-category]");
            const backLink = event.target.closest("[data-back]");
            if (!yearLink && !bucketLink && !categoryLink && !backLink) return;
            event.preventDefault();

            if (yearLink) {
                openYear(panel, section, yearLink.getAttribute("data-open-year"));
                return;
            }
            if (bucketLink) {
                openBucket(panel, section, bucketLink.getAttribute("data-open-bucket"));
                return;
            }
            if (categoryLink) {
                openCategory(panel, section, categoryLink.getAttribute("data-open-category"));
                return;
            }

            const back = backLink.getAttribute("data-back");
            if (back === "bucket" && panel.dataset.bucket) {
                openBucket(panel, section, panel.dataset.bucket);
                return;
            }
            if (back === "years") {
                renderIndex(panel, section);
                return;
            }
            renderIndex(panel, section);
        };
    }

    async function loadInvestorDocuments() {
        const menu = document.getElementById("investorMenu");
        const panels = document.getElementById("investorPanels");
        if (!menu || !panels) return;

        try {
            const response = await fetch(window.INVESTOR_DOCUMENTS_URL || "/api/public-investor-documents/", {
                headers: { Accept: "application/json" },
                cache: "no-store",
            });
            if (!response.ok) throw new Error("Failed to load documents");
            const payload = await response.json();
            renderPage(Array.isArray(payload.sections) ? payload.sections : []);
        } catch (error) {
            console.error(error);
            menu.innerHTML = "";
            panels.innerHTML = `
                <div class="tab-content active-content">
                    <h2>Investor Updates</h2>
                    <p class="investor-empty">Unable to load documents. Please refresh the page.</p>
                </div>
            `;
        }
    }

    document.addEventListener("DOMContentLoaded", loadInvestorDocuments);
})();
