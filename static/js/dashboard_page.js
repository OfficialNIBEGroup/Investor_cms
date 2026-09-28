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

        // Map of count element IDs → API keys (adjust keys to match your backend)
        const countMap = {
            countAnnualReports: data.annual_report || data.counts?.annual_report || 0,
            countFinancialResults: data.financial_result || data.counts?.financial_result || 0,
            countAnnualReturns: data.annual_return || data.counts?.annual_return || 0,
            countCorporateAnnouncements: data.corporate_announcements || data.counts?.corporate_announcements || 0,
            countCorporateGovernance: data.corporate_governance || data.counts?.corporate_governance || 0,
            countShareholdingPattern: data.shareholding_pattern || data.counts?.shareholding_pattern || 0,
            countSebiLodr: data.sebi_document || data.counts?.sebi_document || 0,
            countInvestorFormsDeclaration: data.investor_form || data.counts?.investor_form || 0,
            countSubsidiaryFinancial: data.subsidiary_financial || data.counts?.subsidiary_financial || 0,
        };

        Object.entries(countMap).forEach(([id, value]) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        });

        const total =
            data.total ||
            Object.values(countMap).reduce((sum, n) => sum + Number(n || 0), 0);

        const summaryTotal = document.getElementById("summaryTotal");
        const donutTotal = document.getElementById("donutTotal");
        if (summaryTotal) summaryTotal.textContent = total;
        if (donutTotal) donutTotal.textContent = total;

        // Build section summary grid + update donut
        updateDonutAndSummary(data, total);
    } catch (error) {
        console.error("loadDashboardStatistics error:", error);
    }
}

function updateDonutAndSummary(data, total) {
    const grid = document.getElementById("sectionSummaryGrid");
    if (!grid) return;

    const sections = window.investorSections || [];
    const colors = [
        "#38bdf8", "#a78bfa", "#818cf8", "#34d399", "#2dd4bf",
        "#60a5fa", "#f59e0b", "#fb7185", "#c084fc", "#22c55e",
        "#14b8a6", "#6366f1", "#0ea5e9",
    ];

    grid.innerHTML = "";
    let offset = 0;

    sections.forEach((section, index) => {
        const key = section.key;
        const count =
            (data.counts && data.counts[key]) ||
            data[key] ||
            0;
        const pct = total > 0 ? (count / total) * 100 : 0;

        // Update donut segment if present
        const segment = document.getElementById(`donutSegment${index + 1}`);
        if (segment) {
            segment.setAttribute("stroke-dasharray", `${pct} ${100 - pct}`);
            segment.setAttribute("stroke-dashoffset", String(-offset));
            offset += pct;
        }

        const item = document.createElement("div");
        item.className = "section-summary-item";
        item.innerHTML = `
            <span class="summary-dot" style="background:${colors[index % colors.length]}"></span>
            <span class="summary-label">${escapeHtml(section.name)}</span>
            <strong class="summary-count">${count}</strong>
        `;
        grid.appendChild(item);
    });
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
            window.DASHBOARD_URLS.recentDocuments || "/api/dashboard/recent-documents/",
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
        items.slice(0, 8).forEach((doc) => {
            const title = doc.title || "Untitled Document";
            const sectionName = getSectionDisplayName(doc.section);
            const activityDate =
                doc.date ||
                doc.release_date ||
                doc.disclosure_date ||
                doc.created_at ||
                "-";

            let linkHtml = escapeHtml(title);
            if (doc.pdf_file) {
                linkHtml = `<a href="${escapeHtml(doc.pdf_file)}" target="_blank" rel="noopener noreferrer">${escapeHtml(title)}</a>`;
            } else if (doc.external_url) {
                linkHtml = `<a href="${escapeHtml(doc.external_url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(title)}</a>`;
            } else {
                linkHtml = `<span class="recent-doc-title">${escapeHtml(title)}</span>`;
            }

            const item = document.createElement("div");
            item.className = "recent-document-item";
            item.innerHTML = `
                <div class="recent-doc-main">
                    <div class="recent-doc-title">${linkHtml}</div>
                    <div class="recent-doc-meta">
                        <span class="recent-doc-section">${escapeHtml(sectionName)}</span>
                        <span class="recent-doc-date">${escapeHtml(activityDate)}</span>
                    </div>
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
