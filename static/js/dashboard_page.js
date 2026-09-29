/**
 * dashboard_page.js
 * Dashboard tab: statistics cards, donut chart, recent documents, summary download.
 * Requires: dashboard_common.js
 */

async function loadDashboardStatistics() {
    try {
        const response = await fetch(window.DASHBOARD_URLS.dashboardStats || "/api/dashboard/statistics/", {
            method: "GET",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                Accept: "application/json",
            },
            cache: "no-store",
        });

        if (!response.ok) throw new Error("Failed to load statistics");

        const data = await response.json();

        // Correct keys from the real API response
        const sectionCounts = data.section_counts || {};
        const total = data.total_documents || 0;

        // Top section cards
        const countMap = {
            countAnnualReports: sectionCounts.annual_report || 0,
            countFinancialResults: sectionCounts.financial_result || 0,
            countAnnualReturns: sectionCounts.annual_return || 0,
            countCorporateAnnouncements: sectionCounts.corporate_announcements || 0,
            countCorporateGovernance: sectionCounts.corporate_governance || 0,
            countShareholdingPattern: sectionCounts.shareholding_pattern || 0,
            countSebiLodr: sectionCounts.sebi_document || 0,
            countInvestorFormsDeclaration: sectionCounts.investor_form || 0,
            countSubsidiaryFinancial: sectionCounts.subsidiary_financial || 0,
        };

        Object.entries(countMap).forEach(([id, value]) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        });

        // Total numbers
        const summaryTotal = document.getElementById("summaryTotal");
        const donutTotal = document.getElementById("donutTotal");
        if (summaryTotal) summaryTotal.textContent = total;
        if (donutTotal) donutTotal.textContent = total;

        // Build legend + dynamic donut
        updateDonutAndSummary(sectionCounts, total);
    } catch (error) {
        console.error("loadDashboardStatistics error:", error);
    }
}

function updateDonutAndSummary(sectionCounts, total) {
    const grid = document.getElementById("sectionSummaryGrid");
    if (!grid) return;

    // Prefer sections from common.js
    let sections = window.investorSections || [];

    // Fallback if investorSections is empty
    if (!sections.length && sectionCounts) {
        sections = Object.keys(sectionCounts).map(key => ({
            key: key,
            name: key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())
        }));
    }

    const colorClasses = [
        "section-color-1", "section-color-2", "section-color-3", "section-color-4",
        "section-color-5", "section-color-6", "section-color-7", "section-color-8",
        "section-color-9", "section-color-10", "section-color-11", "section-color-12",
        "section-color-13"
    ];

    // Colors matching the SVG circles in HTML
    const svgColors = [
        "#38bdf8", "#a78bfa", "#818cf8", "#34d399", "#2dd4bf",
        "#60a5fa", "#f59e0b", "#fb7185", "#c084fc", "#22c55e",
        "#14b8a6", "#6366f1", "#0ea5e9"
    ];

    grid.innerHTML = "";
    let offset = 0;

    // Reset all donut segments
    for (let i = 1; i <= 13; i++) {
        const seg = document.getElementById(`donutSegment${i}`);
        if (seg) {
            seg.setAttribute("stroke-dasharray", "0 100");
            seg.setAttribute("stroke-dashoffset", "0");
        }
    }

    sections.forEach((section, index) => {
        const key = section.key;
        const count = Number(sectionCounts[key] || 0);
        const pct = total > 0 ? (count / total) * 100 : 0;

        // Update SVG segment (this makes the donut dynamic)
        const segment = document.getElementById(`donutSegment${index + 1}`);
        if (segment) {
            segment.setAttribute("stroke", svgColors[index % svgColors.length]);
            segment.setAttribute("stroke-dasharray", `${pct} ${100 - pct}`);
            segment.setAttribute("stroke-dashoffset", String(-offset));
            offset += pct;
        }

        // Legend card
        const item = document.createElement("div");
        item.className = "section-stat";
        item.innerHTML = `
            <div class="section-stat-top">
                <span class="legend-dot ${colorClasses[index % colorClasses.length]}"></span>
                <span class="section-stat-name">${escapeHtml(section.name)}</span>
            </div>
            <div class="section-stat-bottom">
                <strong>${count}</strong>
                <span>docs</span>
            </div>
        `;
        grid.appendChild(item);
    });

    console.log("Donut updated → total:", total, "sections:", sections.length, "offset:", offset);
}

function recentActivityBadge(entry) {
    const action = String(entry.action || entry.activity || "").toLowerCase();
    if (action.includes("delete")) {
        return { label: "Deleted", className: "deleted" };
    }
    if (action.includes("edit") || action.includes("update")) {
        return { label: "Edited", className: "edited" };
    }
    return { label: "Created", className: "uploaded" };
}

async function loadRecentDocuments() {
    const listEl = document.getElementById("recentDocumentsList");
    const emptyEl = document.getElementById("recentDocumentsEmpty");
    if (!listEl) return;

    listEl.innerHTML = `<div class="recent-loading" style="padding:20px;text-align:center;color:#64748b;">Loading recent documents...</div>`;
    listEl.style.display = "block";
    if (emptyEl) emptyEl.style.display = "none";

    try {
        const response = await fetch(
            window.DASHBOARD_URLS.recentDocuments || "/api/recent-document-activity/",
            {
                method: "GET",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    Accept: "application/json",
                },
                cache: "no-store",
            }
        );

        if (!response.ok) throw new Error("Failed to load recent documents");

        const docs = await response.json();
        const items = Array.isArray(docs) ? docs : docs.results || [];

        if (!items.length) {
            listEl.innerHTML = "";
            listEl.style.display = "none";
            if (emptyEl) emptyEl.style.display = "block";
            return;
        }

        listEl.innerHTML = "";
        items.slice(0, 8).forEach((entry) => {
            const title = entry.title || entry.document_title || "Untitled Document";
            const sectionName = getSectionDisplayName(entry.section);
            const activityDate = entry.date || entry.created_at || "-";
            const badge = recentActivityBadge(entry);
            const actor = entry.performed_by ? `by ${entry.performed_by}` : "";
            const details = (entry.details || "").trim();

            let linkHtml = escapeHtml(title);
            if (badge.className !== "deleted" && entry.pdf_file) {
                linkHtml = `<a href="${escapeHtml(entry.pdf_file)}" target="_blank" rel="noopener noreferrer">${escapeHtml(title)}</a>`;
            } else if (badge.className !== "deleted" && entry.external_url) {
                linkHtml = `<a href="${escapeHtml(entry.external_url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(title)}</a>`;
            }

            const item = document.createElement("div");
            item.className = "recent-document-item";
            item.innerHTML = `
                <div class="recent-doc-main">
                    <div class="recent-doc-title">${linkHtml}</div>
                    <div class="recent-doc-meta">
                        <span class="recent-doc-section">${escapeHtml(sectionName)}</span>
                        <span class="recent-doc-date">${escapeHtml(activityDate)}</span>
                        ${actor ? `<span class="recent-doc-section">${escapeHtml(actor)}</span>` : ""}
                    </div>
                    ${details ? `<div class="recent-doc-details">${escapeHtml(details)}</div>` : ""}
                </div>
                <div class="recent-doc-status">
                    <span class="recent-doc-activity ${badge.className}">${badge.label}</span>
                </div>
            `;
            listEl.appendChild(item);
        });
    } catch (error) {
        console.error("loadRecentDocuments error:", error);
        listEl.innerHTML = `<div class="recent-error" style="padding:20px;color:#b91c1c;">Unable to load recent documents.</div>`;
    }
}

/* Download Summary Report */
document.addEventListener("DOMContentLoaded", function () {
    const downloadBtn = document.getElementById("downloadSummaryBtn");
    if (!downloadBtn) return;

    downloadBtn.addEventListener("click", async function () {
        const originalText = downloadBtn.innerHTML;
        downloadBtn.disabled = true;
        downloadBtn.innerHTML = "Generating PDF...";

        try {
            const response = await fetch(
                window.DASHBOARD_URLS.downloadSummaryReport || "/api/download-summary-report/",
                {
                    method: "GET",
                    headers: { "X-Requested-With": "XMLHttpRequest" },
                }
            );

            if (!response.ok) throw new Error("Failed to generate report");

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "NIBE_Investor_Summary_Report.pdf";
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error("Download error:", error);
            alert("Failed to download Summary Report. Please try again.");
        } finally {
            downloadBtn.disabled = false;
            downloadBtn.innerHTML = originalText;
        }
    });
});

/* Page init */
document.addEventListener("DOMContentLoaded", function () {
    if (typeof refreshAppSectionsFromAPI === "function") {
        refreshAppSectionsFromAPI();
    }
    loadDashboardStatistics();
    loadRecentDocuments();
});

window.loadDashboardStatistics = loadDashboardStatistics;
window.loadRecentDocuments = loadRecentDocuments;