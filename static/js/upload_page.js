/**
 * upload_page.js
 * Upload Document tab: dynamic fields, drag-drop, form submit.
 * Requires: dashboard_common.js
 */

/* ------------------------------------------------------------------ */
/* Dynamic fields by section                                           */
/* ------------------------------------------------------------------ */
function showSectionFields(section) {
    clearDynamicFields("dynamicFields");

    const subsectionField = document.getElementById("subsectionField");
    const subsectionSelect = document.getElementById("subsection");
    const dynamicFields = document.getElementById("dynamicFields");

    if (subsectionSelect) {
        subsectionSelect.innerHTML = `<option value="">Select Subsection</option>`;
        subsectionSelect.required = false;
    }
    if (subsectionField) subsectionField.style.display = "none";
    if (!section || !dynamicFields) return;

    /* 1. Annual Report */
    if (section === "annual_report") {
        dynamicFields.appendChild(createField("Document Title", "title", "text", true));
        dynamicFields.appendChild(createSelect("Financial Year", "financial_year", financialYearOptions, true));
    }

    /* 2. Financial Results */
    else if (section === "financial_result") {
        dynamicFields.appendChild(createField("Document Title", "title", "text", true));
        dynamicFields.appendChild(createSelect("Financial Year", "financial_year", financialYearOptions, true));
        dynamicFields.appendChild(
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
        dynamicFields.appendChild(createField("Release Date", "release_date", "date", true));
    }

    /* 3. Annual Returns */
    else if (section === "annual_return") {
        dynamicFields.appendChild(createField("Document Title", "title", "text", true));
        dynamicFields.appendChild(createSelect("Financial Year", "financial_year", financialYearOptions, true));
    }

    /* 4. Corporate Announcements – needs subsection */
    else if (section === "corporate_announcements") {
        if (subsectionField) subsectionField.style.display = "block";
        if (subsectionSelect) {
            subsectionSelect.required = true;
            subsectionSelect.innerHTML = `
                <option value="">Select Subsection</option>
                <option value="shareholder_notice">Notice to Stakeholder</option>
                <option value="newspaper_publication">Newspaper Publication</option>
                <option value="stock_exchange_disclosure">Stock Exchange Disclosure</option>
            `;
        }
    }

    /* 5. Corporate Governance */
    else if (section === "corporate_governance") {
        dynamicFields.appendChild(createField("Document Title", "title", "text", true));
        dynamicFields.appendChild(createSelect("Financial Year", "financial_year", financialYearOptions, true));
    }

    /* 6. Shareholding Pattern */
    else if (section === "shareholding_pattern") {
        dynamicFields.appendChild(createField("Document Title", "title", "text", true));
        dynamicFields.appendChild(createSelect("Financial Year", "financial_year", financialYearOptions, true));
        dynamicFields.appendChild(
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
    }

    /* 7. SEBI LODR */
    else if (section === "sebi_document") {
        dynamicFields.appendChild(createField("Document Title", "title", "text", true));
        dynamicFields.appendChild(
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
    }

    /* 8. Investor Forms & Declaration */
    else if (section === "investor_form") {
        dynamicFields.appendChild(createField("Document Title", "title", "text", true));
        dynamicFields.appendChild(
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
        dynamicFields.appendChild(createField("Description", "description"));
        const categorySelect = document.getElementById("category");
        if (categorySelect) {
            categorySelect.addEventListener("change", function () {
                renderInvestorFormExtras(this.value);
            });
        }
    }

    /* Shareholder notice, including when chosen directly from the section list */
    else if (section === "shareholder_notice") {
        dynamicFields.appendChild(createField("Document Title", "title", "text", true));
        dynamicFields.appendChild(createSelect("Financial Year", "financial_year", financialYearOptions, true));
        dynamicFields.appendChild(createField("Notice Type", "notice_type"));
        dynamicFields.appendChild(createField("Disclosure Date", "disclosure_date", "date"));
        dynamicFields.appendChild(createField("Meeting Date", "meeting_date", "date"));
    }

    else if (section === "newspaper_publication" || section === "stock_exchange_disclosure") {
        dynamicFields.appendChild(createField("Document Title", "title", "text", true));
        dynamicFields.appendChild(createSelect("Financial Year", "financial_year", financialYearOptions, true));
        dynamicFields.appendChild(createField("Disclosure Date", "disclosure_date", "date"));
    }

    else if (section === "tax_declaration") {
        dynamicFields.appendChild(createField("Document Title", "title", "text", true));
        dynamicFields.appendChild(createField("Applicable To", "applicable_to"));
        dynamicFields.appendChild(createField("Description", "description"));
    }

    else if (section === "unclaimed_dividend") {
        dynamicFields.appendChild(createField("Document Title", "title", "text", true));
        dynamicFields.appendChild(createSelect("Financial Year", "financial_year", financialYearOptions, true));
        dynamicFields.appendChild(createField("Dividend Type", "dividend_type"));
        dynamicFields.appendChild(createField("Dividend Declaration Date", "dividend_declaration_date", "date"));
        dynamicFields.appendChild(createField("IEPF Transfer Due Date", "iepf_transfer_due_date", "date"));
    }

    /* 9. Subsidiary Financial */
    else if (section === "subsidiary_financial") {
        dynamicFields.appendChild(createField("Document Title", "title", "text", true));
        dynamicFields.appendChild(createSelect("Financial Year", "financial_year", financialYearOptions, true));
        dynamicFields.appendChild(createField("Company Name", "company_name", "text", true));
        dynamicFields.appendChild(createField("Financial Type", "financial_type"));
    }

    /* Custom sections – basic title field */
    else if (section && String(section).startsWith("custom_")) {
        dynamicFields.appendChild(createField("Document Title", "title", "text", true));
        dynamicFields.appendChild(createSelect("Financial Year", "financial_year", financialYearOptions, false));
    }
}

function renderInvestorFormExtras(category) {
    const existing = document.getElementById("investorFormExtras");
    if (existing) existing.remove();

    const dynamicFields = document.getElementById("dynamicFields");
    if (!dynamicFields) return;

    const wrap = document.createElement("div");
    wrap.id = "investorFormExtras";

    if (category === "tax_declaration") {
        wrap.appendChild(createField("Applicable To", "applicable_to"));
    } else if (category === "unclaimed_dividend") {
        wrap.appendChild(createSelect("Financial Year", "financial_year", financialYearOptions, true));
        wrap.appendChild(createField("Dividend Type", "dividend_type"));
        wrap.appendChild(createField("Dividend Declaration Date", "dividend_declaration_date", "date"));
        wrap.appendChild(createField("IEPF Transfer Due Date", "iepf_transfer_due_date", "date"));
    }

    if (wrap.childElementCount) dynamicFields.appendChild(wrap);
}

function showSubsectionFields(section, subsection) {
    clearDynamicFields("dynamicFields");
    const dynamicFields = document.getElementById("dynamicFields");
    if (!section || !subsection || !dynamicFields) return;

    if (section === "corporate_announcements") {
        if (subsection === "shareholder_notice") {
            dynamicFields.appendChild(createField("Document Title", "title", "text", true));
            dynamicFields.appendChild(createSelect("Financial Year", "financial_year", financialYearOptions, true));
            dynamicFields.appendChild(createField("Notice Type", "notice_type"));
            dynamicFields.appendChild(createField("Disclosure Date", "disclosure_date", "date"));
            dynamicFields.appendChild(createField("Meeting Date", "meeting_date", "date"));
        } else if (subsection === "newspaper_publication" || subsection === "stock_exchange_disclosure") {
            dynamicFields.appendChild(createField("Document Title", "title", "text", true));
            dynamicFields.appendChild(createSelect("Financial Year", "financial_year", financialYearOptions, true));
            dynamicFields.appendChild(createField("Disclosure Date", "disclosure_date", "date"));
        }
    }
}

/* ------------------------------------------------------------------ */
/* Drag & drop / file input                                            */
/* ------------------------------------------------------------------ */
function initFileUpload() {
    const fileInput = document.getElementById("documentFile");
    const dropZone = document.getElementById("dropZone");
    if (!fileInput || !dropZone) return;

    fileInput.addEventListener("change", function () {
        if (this.files.length > 0) {
            dropZone.querySelector("h4").textContent = this.files[0].name;
            dropZone.querySelector("p").textContent = "PDF selected successfully";
        }
    });

    dropZone.addEventListener("dragover", function (event) {
        event.preventDefault();
        dropZone.classList.add("drag-over");
    });

    dropZone.addEventListener("dragleave", function () {
        dropZone.classList.remove("drag-over");
    });

    dropZone.addEventListener("drop", function (event) {
        event.preventDefault();
        dropZone.classList.remove("drag-over");
        const files = event.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            dropZone.querySelector("h4").textContent = files[0].name;
            dropZone.querySelector("p").textContent = "PDF selected successfully";
        }
    });
}

/* ------------------------------------------------------------------ */
/* Form submit                                                         */
/* ------------------------------------------------------------------ */
function initUploadForm() {
    const documentUploadForm = document.getElementById("documentUploadForm");
    const uploadDocumentButton = document.getElementById("uploadDocumentButton");
    const cancelUploadButton = document.getElementById("cancelUploadButton");

    if (!documentUploadForm) return;

    documentUploadForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const section = document.getElementById("section")?.value;
        const pdfFile = document.getElementById("documentFile")?.files[0];
        const externalUrl = (document.getElementById("external_url")?.value || "").trim();

        if (!section) {
            alert("Please select a document section.");
            return;
        }
        if (!pdfFile && !externalUrl) {
            alert("Please upload a PDF or provide an external URL.");
            return;
        }

        if (pdfFile) {
            if (!pdfFile.name.toLowerCase().endsWith(".pdf")) {
                alert("Only PDF files are allowed.");
                return;
            }
            // Max 50 MB (matches UI text; adjust if backend differs)
            if (pdfFile.size > 50 * 1024 * 1024) {
                alert("File size must be less than 50 MB.");
                return;
            }
        }

        if (uploadDocumentButton) {
            uploadDocumentButton.disabled = true;
            uploadDocumentButton.textContent = "Uploading...";
        }

        const formData = new FormData(documentUploadForm);
        const csrfToken = getCookie("csrftoken");

        const isCustomSection = section && String(section).startsWith("custom_");
        if (isCustomSection) {
            formData.set("section_id", String(section).replace("custom_", ""));
            const year = (formData.get("financial_year") || "").toString().trim();
            if (year && !formData.get("extra_info")) {
                formData.set("extra_info", year);
            }
            formData.delete("section");
        }

        try {
            const uploadUrl = isCustomSection
                ? window.DASHBOARD_URLS.uploadCustomDocument || "/api/upload-custom-document/"
                : window.DASHBOARD_URLS.uploadDocument || "/api/upload-investor-document/";

            const response = await fetch(uploadUrl, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "X-Requested-With": "XMLHttpRequest",
                },
                body: formData,
            });

            const data = await response.json();

            if (response.ok && data.success) {
                alert(data.message || "Document uploaded successfully.");
                documentUploadForm.reset();
                clearDynamicFields("dynamicFields");

                // Reset dropzone text
                const dropZone = document.getElementById("dropZone");
                if (dropZone) {
                    const h4 = dropZone.querySelector("h4");
                    const p = dropZone.querySelector("p");
                    if (h4) h4.textContent = "Drag & Drop your PDF here";
                    if (p) p.innerHTML = 'or <label for="documentFile" class="browse-link">Browse Files</label>';
                }

                if (typeof loadDashboardStatistics === "function") loadDashboardStatistics();
                if (typeof loadDocuments === "function") loadDocuments();
                if (typeof loadRecentDocuments === "function") loadRecentDocuments();
            } else {
                alert(data.message || "Unable to upload the document.");
            }
        } catch (error) {
            console.error("Upload error:", error);
            alert("An error occurred while uploading the document.");
        } finally {
            if (uploadDocumentButton) {
                uploadDocumentButton.disabled = false;
                uploadDocumentButton.textContent = "↑ Upload Document";
            }
        }
    });

    if (cancelUploadButton) {
        cancelUploadButton.addEventListener("click", function () {
            documentUploadForm.reset();
            clearDynamicFields("dynamicFields");
            const subsectionField = document.getElementById("subsectionField");
            if (subsectionField) subsectionField.style.display = "none";
        });
    }
}

/* ------------------------------------------------------------------ */
/* Init                                                                */
/* ------------------------------------------------------------------ */
document.addEventListener("DOMContentLoaded", function () {
    if (typeof refreshAppSectionsFromAPI === "function") {
        refreshAppSectionsFromAPI();
    }

    initFileUpload();
    initUploadForm();

    const sectionSelect = document.getElementById("section");
    const subsectionSelect = document.getElementById("subsection");

    if (sectionSelect) {
        sectionSelect.addEventListener("change", function () {
            showSectionFields(this.value);
        });
    }

    if (subsectionSelect) {
        subsectionSelect.addEventListener("change", function () {
            const section = document.getElementById("section")?.value;
            showSubsectionFields(section, this.value);
        });
    }
});

window.showSectionFields = showSectionFields;
window.showSubsectionFields = showSubsectionFields;
