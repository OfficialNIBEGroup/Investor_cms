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

    document.getElementById("sf2025Page").style.display = "none";
    document.getElementById("sf2024Page").style.display = "none";
    document.getElementById("sf2023Page").style.display = "none";
    document.getElementById("sf2022Page").style.display = "none";

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


function InvestorGrievances(){

    document.getElementById("Disclosure46").style.display = "none";
    document.getElementById("showInvestorGrievances").style.display = "block";
}


function backToDisclosure46(){

    document.getElementById("Disclosure46").style.display = "block";

    document.getElementById("showCorporateDocuments").style.display = "none";
    document.getElementById("showBoardOfDirectors").style.display = "none";
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


function UnpaidDividend(){

    document.getElementById("InvestorForms").style.display = "none";
    document.getElementById("showUnpaidDividend").style.display = "block";
}


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
    document.getElementById("sf2025Page").style.display="block";
}


function showSF2024(){

    document.getElementById("SubsidiaryFinancials").style.display="none";
    document.getElementById("sf2024Page").style.display="block";
}


function showSF2023(){

    document.getElementById("SubsidiaryFinancials").style.display="none";
    document.getElementById("sf2023Page").style.display="block";
}


function showSF2022(){

    document.getElementById("SubsidiaryFinancials").style.display="none";
    document.getElementById("sf2022Page").style.display="block";
}


function backToSubsidiaryFinancials(){

    document.getElementById("sf2024Page").style.display="none";
    document.getElementById("SubsidiaryFinancials").style.display="block";
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
                        <a href="${result.external_url}" target="_blank">
                            View Results
                        </a>
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
                        <a href="${result.external_url}" target="_blank">
                            View Results
                        </a>
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
                        <a href="${result.external_url}" target="_blank">
                            View Results
                        </a>
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
                        <a href="${result.external_url}" target="_blank">
                            View Results
                        </a>
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
                    <a href="${result.external_url}" target="_blank">
                        View Results
                    </a>
                </td>
            `;

            tableBody.appendChild(row);

        });

    } catch (error) {

        console.error("Error loading financial results:", error);

    }

}


document.addEventListener("DOMContentLoaded", loadFinancialResults);