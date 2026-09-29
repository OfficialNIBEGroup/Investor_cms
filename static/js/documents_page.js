/**
 * documents_page.js
 * Documents tab: list, search, filters, client-side pagination, edit & delete.
 * Requires: dashboard_common.js
 */

let allDocuments = [];
let currentDocPage = 1;
let currentDocPageSize = 20;

/* ------------------------------------------------------------------ */
/* Filters                                                             */
/* ------------------------------------------------------------------ */
function populateYearFilterOptions(documents) {
    const documentYearFilter = document.getElementById("documentYearFilter");
    if (!documentYearFilter) return;

    const previousValue = documentYearFilter.value || "all";
    const years = Array.from(
        new Set(
            documents
                .map((doc) => doc.financial_year)
                .filter((year) => year && year !== "-")
        )
    )
        .sort()
        .reverse();

    documentYearFilter.innerHTML =
        `<option value="all">Financial Year</option>` +
        years.map((year) => `<option value="${escapeHtml(year)}">${escapeHtml(year)}</option>`).join("");

    if (years.includes(previousValue) || previousValue === "all") {
        documentYearFilter.value = previousValue;
    }
}

function getFilteredDocuments() {
    const documentSearch = document.getElementById("documentSearch");
    const documentSectionFilter = document.getElementById("documentSectionFilter");
    const documentYearFilter = document.getElementById("documentYearFilter");
    const documentStatusFilter = document.getElementById("documentStatusFilter");

    const searchValue = documentSearch ? documentSearch.value.trim().toLowerCase() : "";
    const selectedSection = documentSectionFilter ? documentSectionFilter.value : "all";
    const selectedYear = documentYearFilter ? documentYearFilter.value : "all";
    const selectedStatus = documentStatusFilter ? documentStatusFilter.value : "all";

    const corporateChildren = [
        "shareholder_notice",
        "newspaper_publication",
        "stock_exchange_disclosure",
    ];
    const investorFormChildren = [
        "tax_declaration",
        "unclaimed_dividend",
        "kyc_nomination",
    ];

    return allDocuments.filter((doc) => {
        const title = (doc.title || "Untitled Document").toLowerCase();
        const sectionKey = (doc.section || "").toLowerCase();
        const sectionName = getSectionDisplayName(doc.section).toLowerCase();
        const financialYear = doc.financial_year || "-";
        const date = (
            doc.date ||
            doc.release_date ||
            doc.disclosure_date ||
            doc.meeting_date ||
            doc.created_at ||
            "-"
        )
            .toString()
            .toLowerCase();

        const isPublished =
            doc.published === true || doc.published === "true" || doc.published === 1;
        const statusText = isPublished ? "published" : "unpublished";

        const haystack = [title, sectionName, financialYear, date, statusText].join(" ");
        const searchMatches = !searchValue || haystack.includes(searchValue);

        let sectionMatches = true;
        if (selectedSection !== "all") {
            const selectedName = getSectionDisplayName(selectedSection).toLowerCase();
            if (selectedSection === "corporate_announcements") {
                sectionMatches =
                    sectionName === selectedName ||
                    corporateChildren.some(
                        (child) =>
                            sectionKey === child ||
                            sectionName === getSectionDisplayName(child).toLowerCase()
                    );
            } else if (selectedSection === "investor_form") {
                sectionMatches =
                    sectionName === selectedName ||
                    investorFormChildren.some(
                        (child) =>
                            sectionKey === child ||
                            sectionName === getSectionDisplayName(child).toLowerCase()
                    );
            } else {
                sectionMatches =
                    sectionKey === selectedSection || sectionName === selectedName;
            }
        }

        const yearMatches = selectedYear === "all" || financialYear === selectedYear;
        const statusMatches = selectedStatus === "all" || statusText === selectedStatus;

        return searchMatches && sectionMatches && yearMatches && statusMatches;
    });
}

/* ------------------------------------------------------------------ */
/* Table rendering                                                     */
/* ------------------------------------------------------------------ */
function buildDocumentRow(doc) {
    const row = document.createElement("tr");
    const title = doc.title || "Untitled Document";

    let documentLink = escapeHtml(title);
    if (doc.pdf_file) {
        documentLink = `
            <a href="${escapeHtml(doc.pdf_file)}" target="_blank" rel="noopener noreferrer">
                ${escapeHtml(title)}
            </a>`;
    } else if (doc.external_url) {
        documentLink = `
            <a href="${escapeHtml(doc.external_url)}" target="_blank" rel="noopener noreferrer">
                ${escapeHtml(title)}
            </a>`;
    }

    const section = getSectionDisplayName(doc.section);
    const financialYear = doc.financial_year || "-";
    const date =
        doc.date ||
        doc.release_date ||
        doc.disclosure_date ||
        doc.meeting_date ||
        doc.created_at ||
        "-";

    const isPublished =
        doc.published === true || doc.published === "true" || doc.published === 1;
    const statusBadge = isPublished
        ? `<span class="status-badge published">Published</span>`
        : `<span class="status-badge unpublished">Unpublished</span>`;

    row.innerHTML = `
        <td>${documentLink}</td>
        <td>${escapeHtml(section)}</td>
        <td>${escapeHtml(financialYear)}</td>
        <td>${escapeHtml(date)}</td>
        <td>${statusBadge}</td>
        <td>
            <div class="document-actions">
                <button type="button" class="action-btn edit-btn"
                        onclick="openEditModal(${doc.id}, '${escapeHtml(doc.section)}')"
                        title="Edit document">✎ Edit</button>
                <button type="button" class="action-btn delete-btn"
                        onclick="deleteDocument(${doc.id}, '${escapeHtml(doc.section)}')"
                        title="Delete document">🗑 Delete</button>
            </div>
        </td>
    `;
    return row;
}

function updateDocumentsPagination(totalFiltered) {
    const paginationEl = document.getElementById("documentsPagination");
    const pageInfoEl = document.getElementById("documentsPageInfo");
    const prevBtn = document.getElementById("documentsPrevBtn");
    const nextBtn = document.getElementById("documentsNextBtn");
    const pageSizeSelect = document.getElementById("documentsPageSize");

    if (!paginationEl || !pageInfoEl || !prevBtn || !nextBtn) return;

    if (pageSizeSelect) pageSizeSelect.value = String(currentDocPageSize);

    const totalPages = Math.max(1, Math.ceil(totalFiltered / currentDocPageSize));
    if (currentDocPage > totalPages) currentDocPage = totalPages;
    if (currentDocPage < 1) currentDocPage = 1;

    const start = totalFiltered === 0 ? 0 : (currentDocPage - 1) * currentDocPageSize + 1;
    const end = Math.min(currentDocPage * currentDocPageSize, totalFiltered);

    pageInfoEl.textContent = `Showing ${start}–${end} of ${totalFiltered}`;
    paginationEl.style.display = "flex";

    prevBtn.disabled = currentDocPage <= 1;
    nextBtn.disabled = currentDocPage >= totalPages || totalFiltered === 0;
    prevBtn.style.opacity = prevBtn.disabled ? "0.45" : "1";
    nextBtn.style.opacity = nextBtn.disabled ? "0.45" : "1";
    prevBtn.style.cursor = prevBtn.disabled ? "not-allowed" : "pointer";
    nextBtn.style.cursor = nextBtn.disabled ? "not-allowed" : "pointer";
}

function renderDocumentsTable() {
    const tableBody = document.getElementById("documentsTableBody");
    if (!tableBody) return;

    const filtered = getFilteredDocuments();
    const totalFiltered = filtered.length;
    const totalPages = Math.max(1, Math.ceil(totalFiltered / currentDocPageSize));

    if (currentDocPage > totalPages) currentDocPage = totalPages;

    const startIndex = (currentDocPage - 1) * currentDocPageSize;
    const pageDocs = filtered.slice(startIndex, startIndex + currentDocPageSize);

    tableBody.innerHTML = "";

    if (totalFiltered === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="table-empty">No documents available.</td>
            </tr>`;
        updateDocumentsPagination(0);
        return;
    }

    pageDocs.forEach((doc) => tableBody.appendChild(buildDocumentRow(doc)));
    updateDocumentsPagination(totalFiltered);
}

function setSelectValue(id, value) {
    const el = document.getElementById(id);
    if (!el) return;
    const wanted = value == null ? "" : String(value);
    if (
        el.tagName === "SELECT" &&
        wanted &&
        !Array.from(el.options).some((option) => option.value === wanted)
    ) {
        const option = document.createElement("option");
        option.value = wanted;
        option.textContent = wanted;
        el.appendChild(option);
    }
    el.value = wanted;
}

function applyDocumentFilters() {
    currentDocPage = 1;
    renderDocumentsTable();
}

function goDocumentsPage(page) {
    if (page < 1) return;
    currentDocPage = page;
    renderDocumentsTable();
}

function goDocumentsPrev() {
    goDocumentsPage(currentDocPage - 1);
}

function goDocumentsNext() {
    goDocumentsPage(currentDocPage + 1);
}

function changeDocumentsPageSize(newSize) {
    currentDocPageSize = parseInt(newSize, 10) || 20;
    currentDocPage = 1;
    renderDocumentsTable();
}

/* ------------------------------------------------------------------ */
/* Load documents                                                      */
/* ------------------------------------------------------------------ */
async function loadDocuments() {
    const tableBody = document.getElementById("documentsTableBody");
    if (!tableBody) return;

    tableBody.innerHTML = `
        <tr>
            <td colspan="6" class="table-empty">Loading documents...</td>
        </tr>`;

    const paginationEl = document.getElementById("documentsPagination");
    if (paginationEl) paginationEl.style.display = "none";

    try {
        const response = await fetch(window.DASHBOARD_URLS.documentsApi || "/api/dashboard/documents/", {
            method: "GET",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                Accept: "application/json",
            },
            cache: "no-store",
        });

        if (!response.ok) throw new Error("Failed to load documents.");

        const documents = await response.json();
        allDocuments = Array.isArray(documents) ? documents : [];

        // Most recently uploaded / edited first
        allDocuments.sort((a, b) => {
            const aTime = Math.max(
                a.created_at ? new Date(a.created_at).getTime() : 0,
                a.updated_at ? new Date(a.updated_at).getTime() : 0
            );
            const bTime = Math.max(
                b.created_at ? new Date(b.created_at).getTime() : 0,
                b.updated_at ? new Date(b.updated_at).getTime() : 0
            );
            return bTime - aTime;
        });

        populateYearFilterOptions(allDocuments);
        currentDocPage = 1;
        renderDocumentsTable();
    } catch (error) {
        console.error("Documents Loading Error:", error);
        allDocuments = [];
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="table-empty">Unable to load documents.</td>
            </tr>`;
        if (paginationEl) paginationEl.style.display = "none";
    }
}

/* ------------------------------------------------------------------ */
/* Edit Document                                                       */
/* ------------------------------------------------------------------ */
async function openEditModal(documentId, section) {
    const overlay = document.getElementById("editModalOverlay");
    const form = document.getElementById("editDocumentForm");
    const dynamicFields = document.getElementById("editDynamicFields");
    if (!overlay || !form || !dynamicFields) return;

    form.reset();
    dynamicFields.innerHTML = "";

    document.getElementById("edit_document_id").value = documentId;
    document.getElementById("edit_section").value = section;
    document.getElementById("edit_section_display").value = getSectionDisplayName(section);

    try {
        // Adjust URL pattern to match your backend
        const base = window.DASHBOARD_URLS.editDocument || "/api/edit-investor-document/";
        const response = await fetch(`${base}${documentId}/${section}/`, {
            method: "GET",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                Accept: "application/json",
            },
        });

        const result = await response.json();
        if (!result.success) {
            alert(result.message || "Could not load document.");
            return;
        }

        const doc = result.document;
        buildEditFields(section, doc);

        if (doc.external_url) {
            document.getElementById("edit_external_url").value = doc.external_url;
        }

        // Publish status
        const publishedTrue = form.querySelector('input[name="published"][value="true"]');
        const publishedFalse = form.querySelector('input[name="published"][value="false"]');
        if (doc.published) {
            if (publishedTrue) publishedTrue.checked = true;
        } else {
            if (publishedFalse) publishedFalse.checked = true;
        }

        overlay.classList.add("active");
    } catch (error) {
        console.error(error);
        alert("Failed to load document data.");
    }
}

function closeEditModal() {
    const overlay = document.getElementById("editModalOverlay");
    if (overlay) overlay.classList.remove("active");
}

function buildEditFields(section, doc) {
    const container = document.getElementById("editDynamicFields");
    if (!container) return;
    container.innerHTML = "";

    container.appendChild(createField("Document Title", "title", "text", true));
    const titleEl = document.getElementById("title");
    if (titleEl) titleEl.value = doc.title || "";

    if (section === "annual_report" || section === "annual_return") {
        container.appendChild(createSelect("Financial Year", "financial_year", financialYearOptions, true));
        const fy = document.getElementById("financial_year");
        setSelectValue("financial_year", doc.financial_year);
    } else if (section === "financial_result") {
        container.appendChild(createSelect("Financial Year", "financial_year", financialYearOptions, true));
        container.appendChild(
            createSelect(
                "Quarter",
                "quarter",
                [
                    { value: "Q1", label: "Q1" },
                    { value: "Q2", label: "Q2" },
                    { value: "Q3", label: "Q3" },
                    { value: "Q4", label: "Q4" },
                    { value: "Annual", label: "Annual" },
                ],
                true
            )
        );
        container.appendChild(createField("Release Date", "release_date", "date", true));
        const fy = document.getElementById("financial_year");
        const q = document.getElementById("quarter");
        const rd = document.getElementById("release_date");
        setSelectValue("financial_year", doc.financial_year);
        setSelectValue("quarter", doc.quarter);
        if (rd && doc.release_date) rd.value = doc.release_date;
    } else if (section === "corporate_governance" || section === "shareholding_pattern") {
        container.appendChild(createSelect("Financial Year", "financial_year", financialYearOptions, true));
        const fy = document.getElementById("financial_year");
        setSelectValue("financial_year", doc.financial_year);
        container.appendChild(
            createSelect(
                "Quarter",
                "quarter",
                [
                    { value: "Q1", label: "Q1" },
                    { value: "Q2", label: "Q2" },
                    { value: "Q3", label: "Q3" },
                    { value: "Q4", label: "Q4" },
                    { value: "Annual", label: "Annual" },
                ],
                section === "shareholding_pattern"
            )
        );
        const q = document.getElementById("quarter");
        setSelectValue("quarter", doc.quarter);
    } else if (section === "shareholder_notice") {
        container.appendChild(createSelect("Financial Year", "financial_year", financialYearOptions, true));
        container.appendChild(createField("Notice Type", "notice_type"));
        container.appendChild(createField("Disclosure Date", "disclosure_date", "date"));
        container.appendChild(createField("Meeting Date", "meeting_date", "date"));
        const fy = document.getElementById("financial_year");
        const notice = document.getElementById("notice_type");
        const disclosure = document.getElementById("disclosure_date");
        const meeting = document.getElementById("meeting_date");
        setSelectValue("financial_year", doc.financial_year);
        if (notice) notice.value = doc.notice_type || "";
        if (disclosure && doc.disclosure_date) disclosure.value = doc.disclosure_date;
        if (meeting && doc.meeting_date) meeting.value = doc.meeting_date;
    } else if (section === "newspaper_publication" || section === "stock_exchange_disclosure") {
        container.appendChild(createSelect("Financial Year", "financial_year", financialYearOptions, true));
        container.appendChild(createField("Disclosure Date", "disclosure_date", "date"));
        const fy = document.getElementById("financial_year");
        const disclosure = document.getElementById("disclosure_date");
        setSelectValue("financial_year", doc.financial_year);
        if (disclosure && doc.disclosure_date) disclosure.value = doc.disclosure_date;
    } else if (section === "sebi_document") {
        container.appendChild(
            createSelect(
                "Category",
                "category",
                [
                    { value: "corporate_documents", label: "Corporate Documents" },
                    { value: "board_of_directors", label: "Board of Directors" },
                    { value: "board_committees", label: "Committee of Board of Directors" },
                    { value: "codes_policies", label: "Codes and Policies" },
                    { value: "investor_grievances", label: "Investor Grievance" },
                ],
                true
            )
        );
        const cat = document.getElementById("category");
        setSelectValue("category", doc.category);
    } else if (section === "investor_form") {
        container.appendChild(
            createSelect(
                "Form Type",
                "category",
                [
                    { value: "kyc_nomination", label: "KYC and Nomination Form" },
                    { value: "tax_declaration", label: "Tax Declaration for Dividend TDS Related" },
                    { value: "unclaimed_dividend", label: "Unpaid or Unclaimed Dividend Details" },
                ],
                true
            )
        );
        container.appendChild(createField("Description", "description"));
        const cat = document.getElementById("category");
        const desc = document.getElementById("description");
        setSelectValue("category", doc.category);
        if (desc) desc.value = doc.description || "";
    } else if (section === "subsidiary_financial") {
        container.appendChild(createSelect("Financial Year", "financial_year", financialYearOptions, true));
        container.appendChild(createField("Company Name", "company_name", "text", true));
        container.appendChild(createField("Financial Type", "financial_type"));
        const fy = document.getElementById("financial_year");
        const cn = document.getElementById("company_name");
        const ft = document.getElementById("financial_type");
        setSelectValue("financial_year", doc.financial_year);
        if (cn) cn.value = doc.company_name || "";
        if (ft) ft.value = doc.financial_type || "";
    } else if (section === "tax_declaration") {
        container.appendChild(createField("Applicable To", "applicable_to"));
        container.appendChild(createField("Description", "description"));
        const applicable = document.getElementById("applicable_to");
        const desc = document.getElementById("description");
        if (applicable) applicable.value = doc.applicable_to || "";
        if (desc) desc.value = doc.description || "";
    } else if (section === "unclaimed_dividend") {
        container.appendChild(createSelect("Financial Year", "financial_year", financialYearOptions, true));
        container.appendChild(createField("Dividend Type", "dividend_type"));
        container.appendChild(createField("Dividend Declaration Date", "dividend_declaration_date", "date"));
        container.appendChild(createField("IEPF Transfer Due Date", "iepf_transfer_due_date", "date"));
        const fy = document.getElementById("financial_year");
        const dtype = document.getElementById("dividend_type");
        const declared = document.getElementById("dividend_declaration_date");
        const iepf = document.getElementById("iepf_transfer_due_date");
        setSelectValue("financial_year", doc.financial_year);
        if (dtype) dtype.value = doc.dividend_type || "";
        if (declared && doc.dividend_declaration_date) declared.value = doc.dividend_declaration_date;
        if (iepf && doc.iepf_transfer_due_date) iepf.value = doc.iepf_transfer_due_date;
    } else if (section && String(section).startsWith("custom_")) {
        container.appendChild(createField("Extra Info", "extra_info"));
        const extra = document.getElementById("extra_info");
        if (extra) extra.value = doc.extra_info || "";
    }
}

/* Edit form submit */
document.addEventListener("DOMContentLoaded", function () {
    const editForm = document.getElementById("editDocumentForm");
    if (!editForm) return;

    editForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        const btn = document.getElementById("saveEditButton");
        const original = btn ? btn.textContent : "";
        if (btn) {
            btn.disabled = true;
            btn.textContent = "Saving...";
        }

        try {
            const formData = new FormData(editForm);
            const csrfToken = getCookie("csrftoken");
            const documentId = document.getElementById("edit_document_id").value;
            const section = document.getElementById("edit_section").value;

            const updateUrl =
                window.DASHBOARD_URLS.updateDocument || "/api/update-investor-document/";
            const response = await fetch(updateUrl, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "X-Requested-With": "XMLHttpRequest",
                },
                body: formData,
            });

            const result = await response.json();
            if (!response.ok || !result.success) {
                throw new Error(result.message || "Failed to save changes.");
            }

            alert(result.message || "Document updated successfully.");
            closeEditModal();
            loadDocuments();
            if (typeof loadDashboardStatistics === "function") loadDashboardStatistics();
            if (typeof loadRecentDocuments === "function") loadRecentDocuments();
        } catch (error) {
            console.error(error);
            alert(error.message || "Failed to save changes.");
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.textContent = original;
            }
        }
    });
});

/* ------------------------------------------------------------------ */
/* Delete Document                                                     */
/* ------------------------------------------------------------------ */
async function deleteDocument(documentId, section) {
    if (!confirm("Delete this document permanently?\nThis cannot be undone.")) return;

    try {
        const csrfToken = getCookie("csrftoken");
        const deleteUrl =
            window.DASHBOARD_URLS.deleteDocument || "/api/delete-investor-document/";
        const response = await fetch(deleteUrl, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken,
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/json",
                Accept: "application/json",
            },
            body: JSON.stringify({ document_id: documentId, section }),
        });

        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || "Failed to delete document.");
        }

        alert(result.message || "Document deleted.");
        loadDocuments();
        if (typeof loadDashboardStatistics === "function") loadDashboardStatistics();
        if (typeof loadRecentDocuments === "function") loadRecentDocuments();
    } catch (error) {
        console.error(error);
        alert(error.message || "Failed to delete document.");
    }
}

/* ------------------------------------------------------------------ */
/* Event listeners                                                     */
/* ------------------------------------------------------------------ */
document.addEventListener("DOMContentLoaded", function () {
    if (typeof refreshAppSectionsFromAPI === "function") {
        refreshAppSectionsFromAPI();
    }
    loadDocuments();

    const documentSearch = document.getElementById("documentSearch");
    const documentSectionFilter = document.getElementById("documentSectionFilter");
    const documentYearFilter = document.getElementById("documentYearFilter");
    const documentStatusFilter = document.getElementById("documentStatusFilter");

    if (documentSearch) documentSearch.addEventListener("input", applyDocumentFilters);
    if (documentSectionFilter) documentSectionFilter.addEventListener("change", applyDocumentFilters);
    if (documentYearFilter) documentYearFilter.addEventListener("change", applyDocumentFilters);
    if (documentStatusFilter) documentStatusFilter.addEventListener("change", applyDocumentFilters);

    // Close edit modal when clicking overlay
    document.addEventListener("click", function (e) {
        const overlay = document.getElementById("editModalOverlay");
        if (overlay && e.target === overlay) closeEditModal();
    });
});

window.loadDocuments = loadDocuments;
window.openEditModal = openEditModal;
window.closeEditModal = closeEditModal;
window.deleteDocument = deleteDocument;
window.goDocumentsPage = goDocumentsPage;
window.goDocumentsPrev = goDocumentsPrev;
window.goDocumentsNext = goDocumentsNext;
window.changeDocumentsPageSize = changeDocumentsPageSize;
window.applyDocumentFilters = applyDocumentFilters;
