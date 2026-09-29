/**
 * audit_log_page.js
 * Audit Log tab: list activity with pagination.
 * Requires: dashboard_common.js
 */

let currentAuditPage = 1;
let currentAuditPageSize = 20;

function getAuditActionBadge(action) {
    const normalized = (action || "").toLowerCase().trim();

    if (["deleted", "delete"].includes(normalized)) {
        return { className: "deleted", label: "DELETED" };
    }
    if (["edited", "updated", "update", "edit"].includes(normalized)) {
        return { className: "edited", label: "EDITED" };
    }
    if (["uploaded", "created", "create", "upload"].includes(normalized)) {
        return { className: "uploaded", label: "UPLOADED" };
    }

    return {
        className: "uploaded",
        label: (action || "UNKNOWN").toUpperCase(),
    };
}

async function loadAuditLogs(page = 1) {
    const listEl = document.getElementById("auditLogList");
    const emptyEl = document.getElementById("auditLogEmpty");
    const paginationEl = document.getElementById("auditLogPagination");
    const pageInfoEl = document.getElementById("auditLogPageInfo");
    const prevBtn = document.getElementById("auditLogPrevBtn");
    const nextBtn = document.getElementById("auditLogNextBtn");
    const pageSizeSelect = document.getElementById("auditLogPageSize");

    if (!listEl || !emptyEl) return;

    currentAuditPage = Math.max(1, page);

    if (pageSizeSelect) {
        pageSizeSelect.value = currentAuditPageSize;
    }

    listEl.innerHTML = `
        <div class="recent-loading" style="padding: 20px; text-align: center; color: #64748b;">
            Loading audit logs...
        </div>
    `;
    listEl.style.display = "block";
    emptyEl.style.display = "none";
    if (paginationEl) paginationEl.style.display = "none";

    try {
        const base = window.DASHBOARD_URLS.auditLogApi || "/api/audit-logs/";
        const response = await fetch(
            `${base}?page=${currentAuditPage}&page_size=${currentAuditPageSize}&t=${Date.now()}`,
            {
                method: "GET",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    Accept: "application/json",
                },
                cache: "no-store",
            }
        );

        if (!response.ok) throw new Error("Failed to load audit logs");

        const payload = await response.json();
        const logs = payload.results || [];
        const total = payload.total || 0;
        const totalPages = payload.total_pages || 1;
        currentAuditPage = payload.page || currentAuditPage;

        if (!Array.isArray(logs) || logs.length === 0) {
            listEl.innerHTML = "";
            listEl.style.display = "none";
            emptyEl.style.display = "block";
            if (paginationEl) paginationEl.style.display = "none";
            return;
        }

        listEl.innerHTML = "";

        logs.forEach((log) => {
            const badge = getAuditActionBadge(log.action);
            const sectionName = (log.section || "")
                .replace(/_/g, " ")
                .replace(/\b\w/g, (c) => c.toUpperCase());
            const details = (log.details || "").trim();
            const detailsHtml = details
                ? `<div class="recent-doc-details">${escapeHtml(details)}</div>`
                : "";

            const item = document.createElement("div");
            item.className = "recent-document-item";
            item.innerHTML = `
                <div class="recent-doc-main">
                    <div class="recent-doc-title">${escapeHtml(log.document_title || "Untitled")}</div>
                    <div class="recent-doc-meta">
                        <span class="recent-doc-section">${escapeHtml(sectionName)}</span>
                        <span class="recent-doc-date">${escapeHtml(log.created_at || "")}</span>
                        <span class="recent-doc-section">by ${escapeHtml(log.performed_by || "System")}</span>
                    </div>
                    ${detailsHtml}
                </div>
                <div class="recent-doc-status">
                    <span class="recent-doc-activity ${badge.className}">${badge.label}</span>
                </div>
            `;
            listEl.appendChild(item);
        });

        if (paginationEl && pageInfoEl && prevBtn && nextBtn) {
            const start = total === 0 ? 0 : (currentAuditPage - 1) * currentAuditPageSize + 1;
            const end = Math.min(currentAuditPage * currentAuditPageSize, total);

            pageInfoEl.textContent = `Showing ${start}–${end} of ${total}`;
            paginationEl.style.display = "flex";

            prevBtn.disabled = currentAuditPage <= 1;
            nextBtn.disabled = currentAuditPage >= totalPages;
            prevBtn.style.opacity = prevBtn.disabled ? "0.45" : "1";
            nextBtn.style.opacity = nextBtn.disabled ? "0.45" : "1";
            prevBtn.style.cursor = prevBtn.disabled ? "not-allowed" : "pointer";
            nextBtn.style.cursor = nextBtn.disabled ? "not-allowed" : "pointer";
        }
    } catch (error) {
        console.error(error);
        listEl.innerHTML = `
            <div class="recent-error" style="padding: 20px; color: #b91c1c;">
                Unable to load audit logs. Please try again.
            </div>
        `;
        if (paginationEl) paginationEl.style.display = "none";
    }
}

function changeAuditPageSize(newSize) {
    currentAuditPageSize = parseInt(newSize, 10) || 20;
    loadAuditLogs(1);
}

function goAuditPrev() {
    loadAuditLogs(currentAuditPage - 1);
}

function goAuditNext() {
    loadAuditLogs(currentAuditPage + 1);
}

document.addEventListener("DOMContentLoaded", function () {
    loadAuditLogs(1);
});

window.loadAuditLogs = loadAuditLogs;
window.changeAuditPageSize = changeAuditPageSize;
window.goAuditPrev = goAuditPrev;
window.goAuditNext = goAuditNext;
window.currentAuditPage = currentAuditPage;
