function hideIfExists(id){
    const el = document.getElementById(id);
    if (el) {
        el.style.display = "none";
    }
}

function showIfExists(id){
    const el = document.getElementById(id);
    if (el) {
        el.style.display = "block";
    }
}

function showTab(tabId, element){

    event.preventDefault();

    // Hide all content
    document.querySelectorAll('.tab-content').forEach(tab=>{
        tab.style.display='none';
    });

    // Remove active class
    document.querySelectorAll('.investor-sidebar li').forEach(item=>{
        item.classList.remove('active');
    });

    // Show selected content
    document.getElementById(tabId).style.display='block';

    // Active menu item
    element.parentElement.classList.add('active');


    document.getElementById("fy2025Page").style.display = "none";
    document.getElementById("fy2024Page").style.display = "none";
    document.getElementById("fy2023Page").style.display = "none";
    document.getElementById("fy2022Page").style.display = "none";

    document.getElementById("showStackholders").style.display = "none";
    document.getElementById("showNewspaperPublication").style.display = "none";
    document.getElementById("showStockExchange").style.display = "none";


    document.getElementById("NP2026").style.display = "none";
    document.getElementById("NP2025").style.display = "none";
    document.getElementById("NP2024").style.display = "none";

    document.getElementById("SED2026").style.display = "none";
    document.getElementById("SED2025").style.display = "none";
    document.getElementById("SED2024").style.display = "none";

    document.getElementById("sp2025Page").style.display = "none";
    document.getElementById("sp2024Page").style.display = "none";
    document.getElementById("sp2023Page").style.display = "none";
    document.getElementById("sp2022Page").style.display = "none";

    hideIfExists("sf2025Page");
    hideIfExists("sf2024Page");
    hideIfExists("sf2023Page");
    hideIfExists("sf2022Page");

}


window.onload = function(){

    document.getElementById('annualReports').style.display='block';
    document.getElementById('financialResults').style.display='none';
    document.getElementById('AnnualReturns').style.display='none';
    document.getElementById('CorporateAnnouncements').style.display='none';
    document.getElementById('showNewspaperPublication').style.display='none';
    document.getElementById("showStockExchange").style.display = "none";
    document.getElementById("CorporateGovernance").style.display = "none";
    document.getElementById("ShareholdingPattern").style.display = "none";
    document.getElementById("Disclosure46").style.display = "none";
    document.getElementById("InvestorForms").style.display = "none";
    document.getElementById("SubsidiaryFinancials").style.display = "none";

}


function showFY2026(){

    document.getElementById("financialResults")
            .style.display = "none";

    document.getElementById("fy2026Page")
            .style.display = "block";
}


function showFY2025(){

    document.getElementById("financialResults")
            .style.display = "none";

    document.getElementById("fy2025Page")
            .style.display = "block";
}


function showFY2024(){

    document.getElementById("financialResults")
            .style.display = "none";

    document.getElementById("fy2024Page")
            .style.display = "block";
}


function showFY2023(){

    document.getElementById("financialResults")
            .style.display = "none";

    document.getElementById("fy2023Page")
            .style.display = "block";
}


function showFY2022(){

    document.getElementById("financialResults")
            .style.display = "none";

    document.getElementById("fy2022Page")
            .style.display = "block";
}


function backToFinancialResults(){

    document.getElementById("fy2026Page")
            .style.display = "none";

    document.getElementById("fy2025Page")
            .style.display = "none";

    document.getElementById("fy2024Page")
            .style.display = "none";

    document.getElementById("fy2023Page")
            .style.display = "none";

    document.getElementById("fy2022Page")
            .style.display = "none";

    document.getElementById("financialResults")
            .style.display = "block";
}


/* ====================================================
   CORPORATE ANNOUNCEMENTS
==================================================== */


function NoticeToStackholders(){

    document.getElementById("CorporateAnnouncements")
            .style.display = "none";

    document.getElementById("showStackholders")
            .style.display = "block";
}

/* ====================================================
   SHAREHOLDER NOTICES API
==================================================== */

async function loadShareholderNotices() {

    try {

        const response = await fetch("/api/shareholder-notices/");

        if (!response.ok) {
            throw new Error("Failed to load shareholder notices");
        }

        const notices = await response.json();

        const tableBody =
            document.getElementById("shareholderNoticesTableBody");

        if (!tableBody) {
            return;
        }

        tableBody.innerHTML = "";

        notices.forEach((notice, index) => {

            const documentUrl =
                notice.pdf_file || notice.external_url;

            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${index + 1}</td>

                <td>${notice.title}</td>

                <td>${notice.notice_type}</td>

                <td>${notice.financial_year}</td>

                <td>${notice.disclosure_date || "-"}</td>

                <td>${notice.meeting_date || "-"}</td>

                <td>
                    ${
                        documentUrl
                        ? `<a href="${documentUrl}"
                              target="_blank"
                              rel="noopener noreferrer">
                              View Results
                           </a>`
                        : `<span>Document unavailable</span>`
                    }
                </td>
            `;

            tableBody.appendChild(row);

        });

    } catch (error) {

        console.error(
            "Error loading shareholder notices:",
            error
        );

    }

}

document.addEventListener(
    "DOMContentLoaded",
    loadShareholderNotices
);

/* Financial Year Pages - Newspaper Publication */

function showNP2026(){

    document.getElementById("showNewspaperPublication")
            .style.display = "none";

    document.getElementById("NP2026")
            .style.display = "block";
}


function showNP2025(){

    document.getElementById("showNewspaperPublication")
            .style.display = "none";

    document.getElementById("NP2025")
            .style.display = "block";
}


function showNP2024(){

    document.getElementById("showNewspaperPublication")
            .style.display = "none";

    document.getElementById("NP2024")
            .style.display = "block";
}


/* Newspaper Publication */

function NewspaperPublication(){

    document.getElementById("CorporateAnnouncements")
            .style.display = "none";

    document.getElementById("showStockExchange")
            .style.display = "none";

    document.getElementById("SED2026")
            .style.display = "none";

    document.getElementById("SED2025")
            .style.display = "none";

    document.getElementById("SED2024")
            .style.display = "none";

    document.getElementById("showNewspaperPublication")
            .style.display = "block";
}


/* Back To Newspaper Publication */

function backToNewspaperPublication(){

    document.getElementById("NP2026")
            .style.display = "none";

    document.getElementById("NP2025")
            .style.display = "none";

    document.getElementById("NP2024")
            .style.display = "none";

    document.getElementById("showNewspaperPublication")
            .style.display = "block";
}

/* ====================================================
   NEWSPAPER PUBLICATION API
==================================================== */

async function loadNewspaperPublications() {

    try {

        const response =
            await fetch("/api/newspaper-publications/");

        if (!response.ok) {
            throw new Error("Failed to load newspaper publications");
        }

        const publications = await response.json();

        const yearBodies = {
            "2026-27": document.getElementById("np2026TableBody"),
            "2025-26": document.getElementById("np2025TableBody"),
            "2024-25": document.getElementById("np2024TableBody")
        };

        // Clear existing rows
        Object.values(yearBodies).forEach(tableBody => {

            if (tableBody) {
                tableBody.innerHTML = "";
            }

        });

        publications.forEach((publication) => {

            const tableBody =
                yearBodies[publication.financial_year];

            if (!tableBody) {
                return;
            }

            const documentUrl =
                publication.pdf_file ||
                publication.external_url;

            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${tableBody.children.length + 1}</td>

                <td>${publication.title}</td>

                <td>${publication.disclosure_date || "-"}</td>

                <td>
                    ${
                        documentUrl
                        ? `<a href="${documentUrl}"
                              target="_blank"
                              rel="noopener noreferrer">
                              View
                           </a>`
                        : `<span>Document unavailable</span>`
                    }
                </td>
            `;

            tableBody.appendChild(row);

        });

    } catch (error) {

        console.error(
            "Error loading newspaper publications:",
            error
        );

    }

}

document.addEventListener(
    "DOMContentLoaded",
    loadNewspaperPublications
);

/* Stock Exchange Disclosures */

function StockExchangeExclosers(){

    document.getElementById("CorporateAnnouncements")
            .style.display = "none";

    document.getElementById("showNewspaperPublication")
            .style.display = "none";

    document.getElementById("NP2026")
            .style.display = "none";

    document.getElementById("NP2025")
            .style.display = "none";

    document.getElementById("NP2024")
            .style.display = "none";

    document.getElementById("showStockExchange")
            .style.display = "block";
}

/* ====================================================
   STOCK EXCHANGE DISCLOSURE API
==================================================== */

async function loadStockExchangeDisclosures() {

    try {

        const response =
            await fetch("/api/stock-exchange-disclosures/");

        if (!response.ok) {
            throw new Error("Failed to load stock exchange disclosures");
        }

        const disclosures = await response.json();

        const yearBodies = {
            "2026-27":
                document.getElementById("sed2026TableBody"),

            "2025-26":
                document.getElementById("sed2025TableBody"),

            "2024-25":
                document.getElementById("sed2024TableBody")
        };

        // Clear existing rows
        Object.values(yearBodies).forEach(tableBody => {

            if (tableBody) {
                tableBody.innerHTML = "";
            }

        });

        disclosures.forEach((disclosure) => {

            const tableBody =
                yearBodies[disclosure.financial_year];

            if (!tableBody) {
                return;
            }

            const documentUrl =
                disclosure.pdf_file ||
                disclosure.external_url;

            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${tableBody.children.length + 1}</td>

                <td>${disclosure.title}</td>

                <td>${disclosure.disclosure_date || "-"}</td>

                <td>
                    ${
                        documentUrl
                        ? `<a href="${documentUrl}"
                              target="_blank"
                              rel="noopener noreferrer">
                              View
                           </a>`
                        : `<span>Document unavailable</span>`
                    }
                </td>
            `;

            tableBody.appendChild(row);

        });

    } catch (error) {

        console.error(
            "Error loading stock exchange disclosures:",
            error
        );

    }

}

document.addEventListener(
    "DOMContentLoaded",
    loadStockExchangeDisclosures
);

/* Financial Year Pages - Stock Exchange Disclosures */

function showSED2026(){

    document.getElementById("showStockExchange")
            .style.display = "none";

    document.getElementById("SED2026")
            .style.display = "block";
}


function showSED2025(){

    document.getElementById("showStockExchange")
            .style.display = "none";

    document.getElementById("SED2025")
            .style.display = "block";
}


function showSED2024(){

    document.getElementById("showStockExchange")
            .style.display = "none";

    document.getElementById("SED2024")
            .style.display = "block";
}


/* Back To Corporate Announcements */

function backToCorporateAnnouncements(){

    document.querySelectorAll(
        '#showStackholders, #showNewspaperPublication, #showStockExchange, #NP2026, #NP2025, #NP2024, #SED2026, #SED2025, #SED2024'
    ).forEach(el => {

        if(el){
            el.style.display = "none";
        }

    });

    document.getElementById("CorporateAnnouncements")
            .style.display = "block";
}


/* Back To Stock Exchange Disclosures */

function backToStockExchangeDisclosures(){

    document.getElementById("SED2026")
            .style.display = "none";

    document.getElementById("SED2025")
            .style.display = "none";

    document.getElementById("SED2024")
            .style.display = "none";

    document.getElementById("showStockExchange")
            .style.display = "block";
}


/* ====================================================
   CORPORATE GOVERNANCE
==================================================== */


function showCG2025(){

    document.getElementById("CorporateGovernance")
            .style.display = "none";

    document.getElementById("cg2025Page")
            .style.display = "block";
}


function showCG2024(){

    document.getElementById("CorporateGovernance")
            .style.display = "none";

    document.getElementById("cg2024Page")
            .style.display = "block";
}


function showCG2023(){

    document.getElementById("CorporateGovernance")
            .style.display = "none";

    document.getElementById("cg2023Page")
            .style.display = "block";
}


function showCG2022(){

    document.getElementById("CorporateGovernance")
            .style.display = "none";

    document.getElementById("cg2022Page")
            .style.display = "block";
}

async function loadCorporateGovernance() {
    try {
        const response = await fetch("/api/corporate-governance/");

        if (!response.ok) {
            throw new Error("Failed to load corporate governance");
        }

        const results = await response.json();

        const yearBodies = {
            "2025-26": document.getElementById("cg2025TableBody"),
            "2024-25": document.getElementById("cg2024TableBody"),
            "2023-24": document.getElementById("cg2023TableBody"),
            "2022-23": document.getElementById("cg2022TableBody")
        };

        // Clear existing rows
        Object.values(yearBodies).forEach(tableBody => {
            if (tableBody) {
                tableBody.innerHTML = "";
            }
        });

        // Add API data to the correct financial year
        results.forEach((result) => {

            const tableBody = yearBodies[result.financial_year];

            if (!tableBody) {
                return;
            }

            const documentUrl =
                result.pdf_file || result.external_url;

            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${tableBody.children.length + 1}</td>

                <td>${result.quarter}</td>

                <td>
                    ${
                        documentUrl
                        ? `<a href="${documentUrl}"
                              target="_blank"
                              rel="noopener noreferrer">
                              View Results
                           </a>`
                        : `<span>Document unavailable</span>`
                    }
                </td>
            `;

            tableBody.appendChild(row);
        });

    } catch (error) {
        console.error(
            "Error loading corporate governance:",
            error
        );
    }
}

document.addEventListener(
    "DOMContentLoaded",
    loadCorporateGovernance
);


function backToCorporateGovernance(){

    document.getElementById("cg2025Page").style.display = "none";
    document.getElementById("cg2024Page").style.display = "none";
    document.getElementById("cg2023Page").style.display = "none";
    document.getElementById("cg2022Page").style.display = "none";

    document.getElementById("CorporateGovernance").style.display = "block";
}


/* ====================================================
   SHAREHOLDING PATTERN
==================================================== */


function showSP2026(){

    document.getElementById("ShareholdingPattern").style.display = "none";
    document.getElementById("sp2026Page").style.display = "block";
}


function showSP2025(){

    document.getElementById("ShareholdingPattern").style.display = "none";
    document.getElementById("sp2025Page").style.display = "block";
}


function showSP2024(){

    document.getElementById("ShareholdingPattern").style.display = "none";
    document.getElementById("sp2024Page").style.display = "block";
}


function showSP2023(){

    document.getElementById("ShareholdingPattern").style.display = "none";
    document.getElementById("sp2023Page").style.display = "block";
}


function showSP2022(){

    document.getElementById("ShareholdingPattern").style.display = "none";
    document.getElementById("sp2022Page").style.display = "block";
}

/* ====================================================
   SHAREHOLDING PATTERN API
==================================================== */

async function loadShareholdingPattern() {

    try {

        const response = await fetch("/api/shareholding-pattern/");

        if (!response.ok) {
            throw new Error("Failed to load shareholding pattern");
        }

        const results = await response.json();

        const yearBodies = {
            "2026-27": document.getElementById("sp2026ResultsBody"),
            "2025-26": document.getElementById("sp2025ResultsBody"),
            "2024-25": document.getElementById("sp2024ResultsBody"),
            "2023-24": document.getElementById("sp2023ResultsBody"),
            "2022-23": document.getElementById("sp2022ResultsBody")
        };

        // Clear existing hard-coded rows
        Object.values(yearBodies).forEach(tableBody => {

            if (tableBody) {
                tableBody.innerHTML = "";
            }

        });


        results.forEach((result) => {

            const tableBody = yearBodies[result.financial_year];

            if (!tableBody) {
                return;
            }

            const documentUrl =
                result.pdf_file || result.external_url;

            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${tableBody.children.length + 1}</td>

                <td>${result.quarter}</td>

                <td>
                    ${
                        documentUrl
                        ? `<a href="${documentUrl}"
                              target="_blank"
                              rel="noopener noreferrer">
                              View Document
                           </a>`
                        : `<span>Document unavailable</span>`
                    }
                </td>
            `;

            tableBody.appendChild(row);

        });

    } catch (error) {

        console.error(
            "Error loading shareholding pattern:",
            error
        );

    }

}


document.addEventListener(
    "DOMContentLoaded",
    loadShareholdingPattern
);

function backToShareholdingPattern(){

    document.getElementById("sp2026Page").style.display = "none";
    document.getElementById("sp2025Page").style.display = "none";
    document.getElementById("sp2024Page").style.display = "none";
    document.getElementById("sp2023Page").style.display = "none";
    document.getElementById("sp2022Page").style.display = "none";

    document.getElementById("ShareholdingPattern").style.display = "block";
}


/* ====================================================
   DISCLOSURE UNDER REGULATION 46
==================================================== */


function CorporateDocuments(){

    document.getElementById("Disclosure46").style.display = "none";
    document.getElementById("showCorporateDocuments").style.display = "block";
}


function BoardOfDirectors(){

    document.getElementById("Disclosure46").style.display = "none";
    document.getElementById("showBoardOfDirectors").style.display = "block";
}


function CodesPolicies(){

    document.getElementById("Disclosure46").style.display = "none";
    document.getElementById("showCodesPolicies").style.display = "block";
}

function BoardCommittees(){

    document.getElementById("Disclosure46").style.display = "none";
    document.getElementById("showBoardCommittees").style.display = "block";

}

function InvestorGrievances(){

    document.getElementById("Disclosure46").style.display = "none";
    document.getElementById("showInvestorGrievances").style.display = "block";
}


function backToDisclosure46(){

    document.getElementById("Disclosure46").style.display = "block";

    document.getElementById("showCorporateDocuments").style.display = "none";

    document.getElementById("showBoardOfDirectors").style.display = "none";

    document.getElementById("showBoardCommittees").style.display = "none";

    document.getElementById("showCodesPolicies").style.display = "none";

    document.getElementById("showInvestorGrievances").style.display = "none";

}


function Disclosure46(){

    // Hide all tab contents
    document.querySelectorAll(".tab-content").forEach(function(tab){

        tab.style.display = "none";
        tab.classList.remove("active-content");

    });

    // Show Disclosure46
    document.getElementById("Disclosure46").style.display = "block";
    document.getElementById("Disclosure46").classList.add("active-content");
}

/* ====================================================
   SEBI LODR DISCLOSURES API
==================================================== */

async function loadSEBIDocuments() {

    try {

        const response = await fetch("/api/sebi-documents/");

        if (!response.ok) {
            throw new Error("Failed to load SEBI documents");
        }

        const documents = await response.json();

        const categoryBodies = {

            "corporate_documents":
                document.getElementById("corporateDocumentsTableBody"),

            "board_of_directors":
                document.getElementById("boardOfDirectorsTableBody"),

            "board_committees":
                document.getElementById("boardCommitteesTableBody"),

            "codes_policies":
                document.getElementById("codesPoliciesTableBody"),

            "investor_grievances":
                document.getElementById("investorGrievancesTableBody")

        };

        Object.values(categoryBodies).forEach(tableBody => {

            if (tableBody) {
                tableBody.innerHTML = "";
            }

        });

        documents.forEach((item) => {

            const tableBody = categoryBodies[item.category];

            if (!tableBody) {
                return;
            }

            const documentUrl =
                item.pdf_file || item.external_url;

            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${tableBody.children.length + 1}</td>

                <td>${item.title}</td>

                <td>
                    ${
                        documentUrl
                        ? `<a href="${documentUrl}"
                              target="_blank"
                              rel="noopener noreferrer">
                              View
                           </a>`
                        : `<span>Document unavailable</span>`
                    }
                </td>
            `;

            tableBody.appendChild(row);

        });

    } catch (error) {

        console.error(
            "Error loading SEBI documents:",
            error
        );

    }

}

document.addEventListener(
    "DOMContentLoaded",
    loadSEBIDocuments
);

/* ====================================================
   INVESTOR FORMS & DECLARATIONS
==================================================== */


function KYCForms(){

    document.getElementById("InvestorForms").style.display = "none";
    document.getElementById("showKYCForms").style.display = "block";
}


function TaxDeclaration(){

    document.getElementById("InvestorForms").style.display = "none";
    document.getElementById("showTaxDeclaration").style.display = "block";
}

/* ====================================================
   TAX DECLARATIONS API
==================================================== */

async function loadTaxDeclarations() {

    try {

        const response = await fetch("/api/tax-declarations/");

        if (!response.ok) {
            throw new Error("Failed to load tax declarations");
        }

        const results = await response.json();

        const tableBody =
            document.getElementById("taxDeclarationTableBody");

        if (!tableBody) {
            return;
        }

        // Clear existing hard-coded rows
        tableBody.innerHTML = "";

        results.forEach((result, index) => {

            const documentUrl =
                result.pdf_file || result.external_url;

            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${index + 1}</td>

                <td>${result.title || "-"}</td>

                <td>${result.description || "-"}</td>

                <td>${result.applicable_to || "-"}</td>

                <td>
                    ${
                        documentUrl
                        ? `<a href="${documentUrl}"
                              target="_blank"
                              rel="noopener noreferrer">
                              View
                           </a>`
                        : `<span>Document unavailable</span>`
                    }
                </td>
            `;

            tableBody.appendChild(row);

        });

    } catch (error) {

        console.error(
            "Error loading tax declarations:",
            error
        );

    }

}


document.addEventListener(
    "DOMContentLoaded",
    loadTaxDeclarations
);

function UnpaidDividend(){

    document.getElementById("InvestorForms").style.display = "none";
    document.getElementById("showUnpaidDividend").style.display = "block";
}

/* ====================================================
   UNPAID / UNCLAIMED DIVIDEND API
==================================================== */

async function loadUnclaimedDividends() {

    try {

        const response = await fetch("/api/unclaimed-dividends/");

        if (!response.ok) {
            throw new Error("Failed to load unclaimed dividends");
        }

        const results = await response.json();

        const tableBody =
            document.getElementById("unclaimedDividendTableBody");

        if (!tableBody) {
            return;
        }

        // Clear existing hard-coded rows
        tableBody.innerHTML = "";

        results.forEach((result, index) => {

            const documentUrl =
                result.pdf_file || result.external_url;

            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${index + 1}</td>

                <td>${result.financial_year}</td>

                <td>${result.dividend_declaration_date || "-"}</td>

                <td>${result.dividend_type || "-"}</td>

                <td>${result.iepf_transfer_due_date || "-"}</td>

                <td>
                    ${
                        documentUrl
                        ? `<a href="${documentUrl}"
                              target="_blank"
                              rel="noopener noreferrer">
                              View
                           </a>`
                        : `<span>Document unavailable</span>`
                    }
                </td>
            `;

            tableBody.appendChild(row);

        });

    } catch (error) {

        console.error(
            "Error loading unclaimed dividends:",
            error
        );

    }

}


document.addEventListener(
    "DOMContentLoaded",
    loadUnclaimedDividends
);


function backToInvestorForms(){

    document.getElementById("InvestorForms").style.display = "block";

    document.getElementById("showKYCForms").style.display = "none";
    document.getElementById("showTaxDeclaration").style.display = "none";
    document.getElementById("showUnpaidDividend").style.display = "none";
}


function InvestorForms(){

    document.querySelectorAll(".tab-content").forEach(function(tab){
        tab.style.display = "none";
    });

    document.getElementById("InvestorForms").style.display = "block";
}


/* ====================================================
   SUBSIDIARY FINANCIALS
==================================================== */


function showSF2025(){

    document.getElementById("SubsidiaryFinancials").style.display="none";
    showIfExists("sf2025Page");
}


function showSF2024(){

    document.getElementById("SubsidiaryFinancials").style.display="none";
    showIfExists("sf2024Page");
}


function showSF2023(){

    document.getElementById("SubsidiaryFinancials").style.display="none";
    showIfExists("sf2023Page");
}


function showSF2022(){

    document.getElementById("SubsidiaryFinancials").style.display="none";
    showIfExists("sf2022Page");
}


function backToSubsidiaryFinancials(){

    hideIfExists("sf2025Page");
    hideIfExists("sf2024Page");
    hideIfExists("sf2023Page");
    hideIfExists("sf2022Page");

    document.getElementById("SubsidiaryFinancials").style.display = "block";
}


/* ====================================================
   SCROLL REVEAL ANIMATION
==================================================== */


const revealElements=document.querySelectorAll(".reveal-left,.reveal-right");

window.addEventListener("scroll",()=>{

    revealElements.forEach(el=>{

        const top=el.getBoundingClientRect().top;

        if(top<window.innerHeight-100){

            el.classList.add("active");

        }

    });

});


/* ====================================================
   SPEECH VIDEO AUTOPLAY
==================================================== */


const speechVideo = document.getElementById("speechVideo");

if (speechVideo) {

    const observer = new IntersectionObserver((entries) => {

        entries.forEach(entry => {

            if (entry.isIntersecting) {

                speechVideo.currentTime = 0;
                speechVideo.play();

            } else {

                speechVideo.pause();

            }

        });

    }, {
        threshold: 0.5
    });

    observer.observe(speechVideo);

}


/* ====================================================
   TRIGON VIDEO AUTOPLAY ON SCROLL
==================================================== */


document.addEventListener("DOMContentLoaded", function () {

    const trigonVideo = document.getElementById("trigonVideo");

    if (!trigonVideo) return;

    const observer = new IntersectionObserver(function (entries) {

        entries.forEach(function (entry) {

            if (entry.isIntersecting) {

                trigonVideo.play().catch(function (error) {
                    console.log("Autoplay blocked:", error);
                });

            } else {

                trigonVideo.pause();
                trigonVideo.currentTime = 0;

            }

        });

    }, {
        threshold: 0.5
    });

    observer.observe(trigonVideo);

});


/* ====================================================
   ACCORDION
==================================================== */


document.querySelectorAll(".accordion").forEach(accordion => {

    const accordionItems = accordion.querySelectorAll(".accordion-item");

    accordionItems.forEach(item => {

        const header = item.querySelector(".accordion-header");
        const content = item.querySelector(".accordion-content");
        const icon = header ? header.querySelector("span") : null;

        if (!header || !content) return;

        header.addEventListener("click", () => {

            const isActive = item.classList.contains("active");

            // Close all accordion items within this section only
            accordionItems.forEach(i => {

                i.classList.remove("active");

                const iContent = i.querySelector(".accordion-content");
                const iIcon = i.querySelector(".accordion-header span");

                if (iContent) iContent.style.display = "none";
                if (iIcon) iIcon.textContent = "+";

            });

            // If clicked tab was already open, just keep all tabs closed
            if (!isActive) {

                item.classList.add("active");
                content.style.display = "block";

                if (icon) icon.textContent = "−";

            }

        });

    });

});


/* ====================================================
   VISION SLIDER
==================================================== */


const slider = document.getElementById("visionSlider");
const cards = document.querySelectorAll(".vision-card");

let cardWidth = cards[0].offsetWidth + 40;
let autoSlide;


// Auto Scroll
function startAutoSlide(){

    autoSlide = setInterval(() => {

        if (
            slider.scrollLeft + slider.clientWidth >=
            slider.scrollWidth - 10
        ) {

            slider.scrollTo({
                left: 0,
                behavior: "smooth"
            });

        } else {

            slider.scrollBy({
                left: cardWidth,
                behavior: "smooth"
            });

        }

    }, 3000);

}


// Stop Auto Scroll
function stopAutoSlide(){

    clearInterval(autoSlide);

}

startAutoSlide();


/* Stop when mouse enters slider */

slider.addEventListener("mouseenter", stopAutoSlide);


/* Resume when mouse leaves */

slider.addEventListener("mouseleave", startAutoSlide);


/* Arrow Buttons */

document.querySelector(".next").addEventListener("click", () => {

    slider.scrollBy({
        left: cardWidth,
        behavior: "smooth"
    });

});


document.querySelector(".prev").addEventListener("click", () => {

    slider.scrollBy({
        left: -cardWidth,
        behavior: "smooth"
    });

});


/* ====================================================
   FINANCIAL RESULTS API
==================================================== */


async function loadFinancialResults(){

    try {

        const response = await fetch("/api/financial-results/");

        if (!response.ok) {
            throw new Error("Failed to load financial results");
        }

        const results = await response.json();

        const tableBody = document.getElementById("fy2026ResultsBody");

        if (!tableBody) {
            return;
        }


        /* FY 2026-27 */

        const fy2026Results = results.filter(
            result => result.financial_year === "2026-27"
        );


        /* FY 2025-26 */

        const fy2025Results = results.filter(
            result => result.financial_year === "2025-26"
        );

        const fy2025TableBody =
            document.getElementById("fy2025ResultsBody");

        if (fy2025TableBody) {

            fy2025TableBody.innerHTML = "";

            fy2025Results.forEach((result, index) => {

                const row = document.createElement("tr");

                row.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${result.quarter}</td>
                    <td>${result.release_date}</td>
                    <td>
                    ${
                        (result.pdf_file || result.external_url)
                        ? `<a href="${result.pdf_file || result.external_url}" target="_blank" rel="noopener noreferrer">
                               View Results
                           </a>`
                        : `<span>Document unavailable</span>`
                    }
                    </td>
                `;

                fy2025TableBody.appendChild(row);

            });

        }


        /* FY 2024-25 */

        const fy2024Results = results.filter(
            result => result.financial_year === "2024-25"
        );

        const fy2024TableBody =
            document.getElementById("fy2024ResultsBody");

        if (fy2024TableBody) {

            fy2024TableBody.innerHTML = "";

            fy2024Results.forEach((result, index) => {

                const row = document.createElement("tr");

                row.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${result.quarter}</td>
                    <td>${result.release_date}</td>
                    <td>
                    ${
                        (result.pdf_file || result.external_url)
                        ? `<a href="${result.pdf_file || result.external_url}" target="_blank" rel="noopener noreferrer">
                               View Results
                           </a>`
                        : `<span>Document unavailable</span>`
                    }
                    </td>
                `;

                fy2024TableBody.appendChild(row);

            });

        }


        /* FY 2023-24 */

        const fy2023Results = results.filter(
            result => result.financial_year === "2023-24"
        );

        const fy2023TableBody =
            document.getElementById("fy2023ResultsBody");

        if (fy2023TableBody) {

            fy2023TableBody.innerHTML = "";

            fy2023Results.forEach((result, index) => {

                const row = document.createElement("tr");

                row.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${result.quarter}</td>
                    <td>${result.release_date}</td>
                    <td>
                    ${
                        (result.pdf_file || result.external_url)
                        ? `<a href="${result.pdf_file || result.external_url}" target="_blank" rel="noopener noreferrer">
                               View Results
                           </a>`
                        : `<span>Document unavailable</span>`
                    }
                    </td>
                `;

                fy2023TableBody.appendChild(row);

            });

        }


        /* FY 2022-23 */

        const fy2022Results = results.filter(
            result => result.financial_year === "2022-23"
        );

        const fy2022TableBody =
            document.getElementById("fy2022ResultsBody");

        if (fy2022TableBody) {

            fy2022TableBody.innerHTML = "";

            fy2022Results.forEach((result, index) => {

                const row = document.createElement("tr");

                row.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${result.quarter}</td>
                    <td>${result.release_date}</td>
                    <td>
                    ${
                        (result.pdf_file || result.external_url)
                        ? `<a href="${result.pdf_file || result.external_url}" target="_blank" rel="noopener noreferrer">
                               View Results
                           </a>`
                        : `<span>Document unavailable</span>`
                    }
                    </td>
                `;

                fy2022TableBody.appendChild(row);

            });

        }


        /* Insert FY 2026-27 results */

        tableBody.innerHTML = "";

        fy2026Results.forEach((result, index) => {

            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${result.quarter}</td>
                <td>${result.release_date}</td>
                <td>
                    ${
                        (result.pdf_file || result.external_url)
                        ? `<a href="${result.pdf_file || result.external_url}" target="_blank" rel="noopener noreferrer">
                               View Results
                           </a>`
                        : `<span>Document unavailable</span>`
                    }
                </td>
            `;

            tableBody.appendChild(row);

        });

    } catch (error) {

        console.error("Error loading financial results:", error);

    }

}


document.addEventListener("DOMContentLoaded", loadFinancialResults);



/* ====================================================
   KYC / INVESTOR FORMS API
==================================================== */

async function loadInvestorForms() {

    try {

        const response = await fetch("/api/investor-forms/");

        if (!response.ok) {
            throw new Error("Failed to load investor forms");
        }

        const forms = await response.json();

        const tableBody = document.getElementById("kycFormsTableBody");

        if (!tableBody) {
            return;
        }

        tableBody.innerHTML = "";

        // Prefer forms that look like KYC / nomination; if none, show all
        let kycForms = forms.filter(f => {
            const cat = (f.category || "").toLowerCase();
            const title = (f.title || "").toLowerCase();
            return cat.includes("kyc") ||
                   cat.includes("nomination") ||
                   title.includes("kyc") ||
                   title.includes("nomination") ||
                   title.includes("isr") ||
                   title.includes("sh-13") ||
                   title.includes("sh-14");
        });

        if (kycForms.length === 0) {
            kycForms = forms;
        }

        kycForms.forEach((form, index) => {

            const documentUrl = form.pdf_file || form.external_url;

            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${form.title || "-"}</td>
                <td>${form.description || "-"}</td>
                <td>
                    ${
                        documentUrl
                        ? `<a href="${documentUrl}"
                              target="_blank"
                              rel="noopener noreferrer">
                              View
                           </a>`
                        : `<span>Document unavailable</span>`
                    }
                </td>
            `;

            tableBody.appendChild(row);

        });

    } catch (error) {

        console.error("Error loading investor forms:", error);

    }

}

document.addEventListener("DOMContentLoaded", loadInvestorForms);


/* ====================================================
   SUBSIDIARY FINANCIALS API
==================================================== */

async function loadSubsidiaryFinancials() {

    try {

        const response = await fetch("/api/subsidiary-financials/");

        if (!response.ok) {
            throw new Error("Failed to load subsidiary financials");
        }

        const financials = await response.json();

        const tableBody = document.getElementById("subsidiaryFinancialsTableBody");

        if (!tableBody) {
            return;
        }

        tableBody.innerHTML = "";

        // Prefer 2024-25; if empty, show all
        let rows = financials.filter(f => f.financial_year === "2024-25");

        if (rows.length === 0) {
            rows = financials;
        }

        rows.forEach((item, index) => {

            const documentUrl = item.pdf_file || item.external_url;

            const companyLabel = item.company_name || item.title || "-";
            const typeLabel = item.financial_type
                ? ` (${item.financial_type})`
                : "";

            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${companyLabel}${typeLabel}</td>
                <td>
                    ${
                        documentUrl
                        ? `<a href="${documentUrl}"
                              target="_blank"
                              rel="noopener noreferrer">
                              View
                           </a>`
                        : `<span>Document unavailable</span>`
                    }
                </td>
            `;

            tableBody.appendChild(row);

        });

        // Update heading if we have a year
        const heading = document.getElementById("sfYearHeading");
        if (heading && rows.length > 0 && rows[0].financial_year) {
            heading.textContent = "Financial Year " + rows[0].financial_year;
        }

    } catch (error) {

        console.error("Error loading subsidiary financials:", error);

    }

}

document.addEventListener("DOMContentLoaded", loadSubsidiaryFinancials);