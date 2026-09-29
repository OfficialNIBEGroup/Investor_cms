/**
 * dashboard_common.js
 * Shared helpers, constants and utilities used across all Investor Dashboard pages.
 * Load this file first on every page.
 *
 * Expected global injected by Django template (in base or page):
 *   window.CURRENT_USER_ROLE  (string)
 *   window.IS_ADMIN           (boolean)
 *   window.DASHBOARD_URLS     (object with API endpoint URLs)
 */

/* ------------------------------------------------------------------ */
/* Role (fallback if not injected)                                     */
/* ------------------------------------------------------------------ */
window.CURRENT_USER_ROLE = window.CURRENT_USER_ROLE || "EMPLOYEE";
window.IS_ADMIN = window.IS_ADMIN === true || window.CURRENT_USER_ROLE === "ADMIN";

/* ------------------------------------------------------------------ */
/* URL registry – override these from Django template                  */
/* ------------------------------------------------------------------ */
window.DASHBOARD_URLS = window.DASHBOARD_URLS || {
    // Documents
    documentsApi: "/api/dashboard/documents/",
    uploadDocument: "/api/upload-investor-document/",
    uploadCustomDocument: "/api/upload-custom-document/",
    editDocument: "/api/edit-investor-document/",          // append id/section
    updateDocument: "/api/update-investor-document/",
    deleteDocument: "/api/delete-investor-document/",

    // Dashboard stats
    dashboardStats: "/api/dashboard/statistics/",
    recentDocuments: "/api/recent-document-activity/",
    downloadSummaryReport: "/api/download-summary-report/",

    // Audit
    auditLogApi: "/api/audit-log/",

    // Employees
    employeesList: "/api/employees/",
    saveEmployee: "/api/employees/save/",
    toggleEmployeeStatus: "/api/employees/toggle-status/",
    deleteEmployee: "/api/employees/delete/",

    // Sections
    sectionsListApi: "/api/sections/",
    createSection: "/api/sections/create/",
    updateSection: "/api/sections/update/",
    toggleSectionStatus: "/api/sections/toggle-status/",
    deleteSection: "/api/sections/delete/",
    createSubsection: "/api/subsections/create/",
    updateSubsection: "/api/subsections/update/",
    deleteSubsection: "/api/subsections/delete/",
};

/* ------------------------------------------------------------------ */
/* Financial year options                                              */
/* ------------------------------------------------------------------ */
const financialYearOptions = [
    { value: "2027-28", label: "Financial Year 2027-28" },
    { value: "2026-27", label: "Financial Year 2026-27" },
    { value: "2025-26", label: "Financial Year 2025-26" },
    { value: "2024-25", label: "Financial Year 2024-25" },
    { value: "2023-24", label: "Financial Year 2023-24" },
    { value: "2022-23", label: "Financial Year 2022-23" },
];

/* ------------------------------------------------------------------ */
/* Default section tree (refreshed from API when available)            */
/* ------------------------------------------------------------------ */
let investorSections = [
    { key: "annual_report", name: "Annual Report" },
    { key: "financial_result", name: "Financial Results" },
    { key: "annual_return", name: "Annual Returns" },
    {
        key: "corporate_announcements",
        name: "Corporate Announcements",
        children: [
            { key: "shareholder_notice", name: "Notice to Stakeholder" },
            { key: "newspaper_publication", name: "Newspaper Publication" },
            { key: "stock_exchange_disclosure", name: "Stock Exchange Disclosure" },
        ],
    },
    { key: "corporate_governance", name: "Corporate Governance" },
    { key: "shareholding_pattern", name: "Shareholding Pattern" },
    { key: "sebi_document", name: "Disclosure under Regulations 46 of SEBI LODR" },
    {
        key: "investor_form",
        name: "Investor Forms & Declaration",
        children: [
            { key: "kyc_nomination", name: "KYC and Nomination Form" },
            { key: "tax_declaration", name: "Tax Declaration for Dividend TDS Related" },
            { key: "unclaimed_dividend", name: "Unpaid or Unclaimed Dividend Details" },
        ],
    },
    { key: "subsidiary_financial", name: "Subsidiary Financial" },
];

/* ------------------------------------------------------------------ */
/* Utilities                                                           */
/* ------------------------------------------------------------------ */

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === name + "=") {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function escapeHtml(value) {
    if (value === null || value === undefined) return "";
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function getSectionDisplayName(section) {
    function findInTree(items) {
        if (!items) return null;
        for (const item of items) {
            if (item.key === section) return item.name;
            if (item.children) {
                const childName = findInTree(item.children);
                if (childName) return childName;
            }
        }
        return null;
    }
    return findInTree(investorSections) || section;
}

function toggleSidebar() {
    const sidebar = document.querySelector(".sidebar");
    if (sidebar) sidebar.classList.toggle("mobile-open");
}

/**
 * Create a labelled input field (used by upload + edit forms)
 */
function createField(label, name, type = "text", required = false) {
    const group = document.createElement("div");
    group.className = "form-group";
    group.innerHTML = `
        <label for="${name}">
            ${label}
            ${required ? "<span>*</span>" : ""}
        </label>
        <input type="${type}" id="${name}" name="${name}" ${required ? "required" : ""}>
    `;
    return group;
}

/**
 * Create a labelled select field
 */
function createSelect(label, name, options, required = false) {
    const group = document.createElement("div");
    group.className = "form-group";

    let optionsHTML = `<option value="">Select ${label}</option>`;
    options.forEach((option) => {
        optionsHTML += `<option value="${option.value}">${option.label}</option>`;
    });

    group.innerHTML = `
        <label for="${name}">
            ${label}
            ${required ? "<span>*</span>" : ""}
        </label>
        <select id="${name}" name="${name}" ${required ? "required" : ""}>
            ${optionsHTML}
        </select>
    `;
    return group;
}

function clearDynamicFields(containerId = "dynamicFields") {
    const el = document.getElementById(containerId);
    if (el) el.innerHTML = "";
}

/**
 * Refresh section dropdowns + investorSections from the Sections API.
 * Safe to call on any page.
 */
async function refreshAppSectionsFromAPI() {
    try {
        const response = await fetch(
            (window.DASHBOARD_URLS.sectionsListApi || "/api/sections/") + "?active_only=1",
            {
                credentials: "same-origin",
                headers: { "X-Requested-With": "XMLHttpRequest" },
            }
        );
        if (!response.ok) return;
        const sections = await response.json();
        if (!Array.isArray(sections)) return;

        // Keep system hierarchy; append custom sections
        const customOnly = sections.filter((s) => !s.is_system && s.is_active);

        // Remove previous custom_* entries
        investorSections = (investorSections || []).filter(
            (s) => !(s.key && String(s.key).startsWith("custom_"))
        );

        customOnly.forEach((s) => {
            investorSections.push({
                key: "custom_" + s.id,
                name: s.name,
                is_custom: true,
                section_id: s.id,
                icon: s.icon || "📁",
                children: (s.subsections || []).map((sub) => ({
                    key: "sub_" + sub.id,
                    name: sub.name,
                    subsection_id: sub.id,
                })),
            });
        });

        // Rebuild Upload <select id="section">
        const uploadSelect = document.getElementById("section");
        if (uploadSelect) {
            const current = uploadSelect.value;
            let html = '<option value="">Select Section</option>';
            sections
                .filter((s) => s.is_active)
                .forEach((s) => {
                    if (s.is_system && s.model_key) {
                        html += `<option value="${s.model_key}">${escapeHtml(s.name)}</option>`;
                    } else if (!s.is_system) {
                        html += `<option value="custom_${s.id}">${escapeHtml(s.icon || "📁")} ${escapeHtml(s.name)}</option>`;
                    }
                });
            // Ensure composite options exist
            [
                ["corporate_announcements", "Corporate Announcements"],
                ["investor_form", "Investor Forms & Declaration"],
            ].forEach(([val, label]) => {
                if (!html.includes(`value="${val}"`)) {
                    html += `<option value="${val}">${label}</option>`;
                }
            });
            uploadSelect.innerHTML = html;
            if (current) uploadSelect.value = current;
        }

        // Rebuild Documents filter <select id="documentSectionFilter">
        const filterSelect = document.getElementById("documentSectionFilter");
        if (filterSelect) {
            const current = filterSelect.value;
            let html = '<option value="all">All Sections</option>';
            sections
                .filter((s) => s.is_active)
                .forEach((s) => {
                    if (s.is_system && s.model_key) {
                        html += `<option value="${s.model_key}">${escapeHtml(s.name)}</option>`;
                    } else if (!s.is_system) {
                        html += `<option value="custom_${s.id}">${escapeHtml(s.name)}</option>`;
                    }
                });
            [
                ["corporate_announcements", "Corporate Announcements"],
                ["investor_form", "Investor Forms & Declaration"],
            ].forEach(([val, label]) => {
                if (!html.includes(`value="${val}"`)) {
                    html += `<option value="${val}">${label}</option>`;
                }
            });
            filterSelect.innerHTML = html;
            if (current) filterSelect.value = current;
        }

        // Refresh dashboard stats if the function exists on this page
        if (typeof loadDashboardStatistics === "function") {
            try {
                loadDashboardStatistics();
            } catch (e) {}
        }
    } catch (e) {
        console.error("refreshAppSectionsFromAPI failed:", e);
    }
}

/* Export for modules that expect globals */
window.financialYearOptions = financialYearOptions;
window.investorSections = investorSections;
window.getCookie = getCookie;
window.escapeHtml = escapeHtml;
window.getSectionDisplayName = getSectionDisplayName;
window.toggleSidebar = toggleSidebar;
window.createField = createField;
window.createSelect = createSelect;
window.clearDynamicFields = clearDynamicFields;
window.refreshAppSectionsFromAPI = refreshAppSectionsFromAPI;
