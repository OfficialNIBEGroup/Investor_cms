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
    documentsApi: window.appUrl("/api/dashboard-documents/"),
    uploadDocument: window.appUrl("/api/upload-investor-document/"),
    uploadCustomDocument: window.appUrl("/api/upload-custom-document/"),
    editDocument: window.appUrl("/api/edit-investor-document/"),          // append id/section
    updateDocument: window.appUrl("/api/update-investor-document/"),
    deleteDocument: window.appUrl("/api/delete-investor-document/"),

    // Dashboard stats
    dashboardStats: window.appUrl("/api/dashboard-statistics/"),
    recentDocuments: window.appUrl("/api/recent-document-activity/"),
    downloadSummaryReport: window.appUrl("/api/download-summary-report/"),

    // Audit
    auditLogApi: window.appUrl("/api/audit-logs/"),

    // Employees
    employeesList: window.appUrl("/api/employees/"),
    saveEmployee: window.appUrl("/api/employees/save/"),
    toggleEmployeeStatus: window.appUrl("/api/employees/toggle-status/"),
    deleteEmployee: window.appUrl("/api/employees/delete/"),

    // Sections
    sectionsListApi: window.appUrl("/api/sections/"),
    createSection: window.appUrl("/api/sections/create/"),
    updateSection: window.appUrl("/api/sections/update/"),
    toggleSectionStatus: window.appUrl("/api/sections/toggle-status/"),
    deleteSection: window.appUrl("/api/sections/delete/"),
    createSubsection: window.appUrl("/api/subsections/create/"),
    updateSubsection: window.appUrl("/api/subsections/update/"),
    deleteSubsection: window.appUrl("/api/subsections/delete/"),
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
    { value: "2021-22", label: "Financial Year 2021-22" },
    { value: "2020-21", label: "Financial Year 2020-21" },
    { value: "2019-20", label: "Financial Year 2019-20" },
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
const ALLOWED_UPLOAD_SECTIONS = [
    { value: "annual_report", label: "Annual Report" },
    { value: "financial_result", label: "Financial Result" },
    { value: "annual_return", label: "Annual Returns" },
    { value: "corporate_announcements", label: "Corporate Announcement" },
    { value: "corporate_governance", label: "Corporate Governance" },
    { value: "shareholding_pattern", label: "Shareholding Pattern" },
    { value: "sebi_document", label: "SEBI Documents" },
    { value: "investor_form", label: "Investor Forms" },
    { value: "subsidiary_financial", label: "Subsidiary Financials" },
  ];

  const uploadSelect = document.getElementById("section");
  if (uploadSelect) {
    const current = uploadSelect.value;
    uploadSelect.innerHTML =
      '<option value="">Select Section</option>' +
      ALLOWED_UPLOAD_SECTIONS.map(
        (opt) => `<option value="${opt.value}">${escapeHtml(opt.label)}</option>`
      ).join("");
    if (current) uploadSelect.value = current;
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
