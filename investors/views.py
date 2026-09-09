from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import never_cache
from django.shortcuts import render, redirect
from django.db.models import Max
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.contrib import messages
from .models import Profile   # make sure Profile is imported

from .models import (
    AnnualReport,
    FinancialResult,
    AnnualReturn,
    ShareholderNotice,
    NewspaperPublication,
    StockExchangeDisclosure,
    CorporateGovernance,
    ShareholdingPattern,
    SEBIDocument,
    InvestorForm,
    TaxDeclaration,
    UnclaimedDividend,
    SubsidiaryFinancial,
    AuditLog,
    Section,
    SubSection,
    CustomDocument,
)
from django.utils.text import slugify

AUDIT_ACTION_MAP = {
    "created": "uploaded",
    "create": "uploaded",
    "upload": "uploaded",
    "uploaded": "uploaded",
    "updated": "edited",
    "update": "edited",
    "edit": "edited",
    "edited": "edited",
    "deleted": "deleted",
    "delete": "deleted",
}


# ============================================================
# ROLE BASED ACCESS CONTROL
# ============================================================
# ADMIN    → Full system access
# EMPLOYEE → Only Documents + Upload Document
# CLIENT   → Only public website (www.nibelimited.com)

def role_required(allowed_roles=None):
    """
    Restrict a view to specific roles only.

    Example:
        @role_required(['ADMIN'])
        def employees_list_api(...):

        @role_required(['ADMIN', 'EMPLOYEE'])
        def upload_investor_document(...):
    """
    if allowed_roles is None:
        allowed_roles = []

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            # User must be logged in
            if not request.user.is_authenticated:
                return redirect('dashboard_login')

            # Safety: create profile if it does not exist
            if not hasattr(request.user, 'profile'):
                Profile.objects.create(user=request.user, role='EMPLOYEE')

            user_role = request.user.profile.role

            # Role not allowed → block access
            if user_role not in allowed_roles:
                # For API calls return JSON error
                if request.path.startswith('/api/'):
                    return JsonResponse({
                        "success": False,
                        "message": "You do not have permission to perform this action."
                    }, status=403)

                # For normal pages → redirect with message
                messages.error(request, "You do not have permission to access this page.")
                return redirect('upload_dashboard')

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def normalize_audit_action(action):
    """Map free-form action labels to AuditLog choices."""
    key = (action or "").strip().lower()
    return AUDIT_ACTION_MAP.get(key, key or "uploaded")


def snapshot_document(obj):
    """Capture a comparable dict of document field values."""
    skip = {"id", "created_at", "updated_at", "display_order", "published"}
    data = {}
    for field in obj._meta.fields:
        name = field.name
        if name in skip:
            continue
        value = getattr(obj, name)
        if name == "pdf_file":
            data[name] = getattr(value, "name", "") if value else ""
            continue
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        elif value is None:
            value = ""
        else:
            value = str(value).strip()
        data[name] = value
    return data


def describe_document_changes(old, new, pdf_replaced=False):
    """Build a short human-readable summary of what changed."""
    changes = []
    keys = list(old.keys())
    for key in new.keys():
        if key not in keys:
            keys.append(key)

    for key in keys:
        if key == "pdf_file":
            continue
        before = old.get(key, "")
        after = new.get(key, "")
        if before == after:
            continue
        label = key.replace("_", " ").title()
        if before in ("", None) and after:
            changes.append(f"{label} set to '{after}'")
        elif after in ("", None) and before:
            changes.append(f"{label} cleared (was '{before}')")
        else:
            changes.append(f"{label} changed from '{before}' to '{after}'")

    if pdf_replaced:
        changes.append("PDF file replaced")

    return "; ".join(changes) if changes else "Document details updated"


def log_audit(request, title, section, action, document_id=None, details=""):
    """Save an audit log entry with a normalized action."""
    try:
        AuditLog.objects.create(
            document_title=title or "Untitled",
            section=section or "",
            action=normalize_audit_action(action),
            details=details or "",
            performed_by=request.user.username if request.user.is_authenticated else "System",
            document_id=document_id,
        )
    except Exception:
        pass  # Never break main action if logging fails


# ============================================================
# HELPER - AUTO GENERATE NEXT DISPLAY ORDER
# ============================================================

def get_next_display_order(model):
    """
    Automatically returns the next display order number.

    Existing:
        1, 2, 3

    New document:
        4

    If there are no documents:
        1

    Higher display_order = newer document.
    """

    last_order = model.objects.aggregate(
        max_order=Max("display_order")
    )["max_order"]

    return (last_order or 0) + 1


# ============================================================
# ANNUAL REPORTS API
# ============================================================

def annual_reports_api(request):

    reports = AnnualReport.objects.filter(
        published=True
    ).order_by(
        "-display_order"
    )

    data = []

    for report in reports:
        data.append({
            "id": report.id,
            "section": "annual_report",
            "title": report.title,
            "financial_year": report.financial_year,
            "pdf_file": (
                request.build_absolute_uri(report.pdf_file.url)
                if report.pdf_file
                else None
            ),
            "external_url": report.external_url,
            "published": report.published,
            "display_order": report.display_order,
        })

    return JsonResponse(data, safe=False)

# ============================================================
# FINANCIAL RESULTS API
# ============================================================

def financial_results_api(request):

    results = FinancialResult.objects.filter(
        published=True
    ).order_by(
        "-display_order"
    )

    data = []

    for result in results:
        data.append({
            "id": result.id,
            "section": "financial_result",
            "title": result.title,
            "financial_year": result.financial_year,
            "quarter": result.quarter,
            "release_date": result.release_date,
            "pdf_file": (
                request.build_absolute_uri(result.pdf_file.url)
                if result.pdf_file
                else None
            ),
            "external_url": result.external_url,
            "published": result.published,
            "display_order": result.display_order,
        })

    return JsonResponse(data, safe=False)


# ============================================================
# ANNUAL RETURNS API
# ============================================================

def annual_returns_api(request):

    returns = AnnualReturn.objects.filter(
        published=True
    ).order_by(
        "-display_order"
    )

    data = []

    for annual_return in returns:
        data.append({
            "id": annual_return.id,
            "section": "annual_return",
            "title": annual_return.title,
            "financial_year": annual_return.financial_year,
            "pdf_file": (
                request.build_absolute_uri(
                    annual_return.pdf_file.url
                )
                if annual_return.pdf_file
                else None
            ),
            "external_url": annual_return.external_url,
            "published": annual_return.published,
            "display_order": annual_return.display_order,
        })

    return JsonResponse(data, safe=False)


# ============================================================
# SHAREHOLDER NOTICES API
# ============================================================

def shareholder_notices_api(request):

    notices = ShareholderNotice.objects.filter(
        published=True
    ).order_by(
        "-display_order"
    )

    data = []

    for notice in notices:
        data.append({
            "id": notice.id,
            "title": notice.title,
            "financial_year": notice.financial_year,
            "notice_type": notice.notice_type,
            "disclosure_date": (
                notice.disclosure_date.strftime("%d-%m-%Y")
                if notice.disclosure_date
                else None
            ),
            "meeting_date": (
                notice.meeting_date.strftime("%d-%m-%Y")
                if notice.meeting_date
                else None
            ),
            "pdf_file": (
                request.build_absolute_uri(
                    notice.pdf_file.url
                )
                if notice.pdf_file
                else None
            ),
            "external_url": notice.external_url,
            "published": notice.published,
            "display_order": notice.display_order,
        })

    return JsonResponse(data, safe=False)


# ============================================================
# NEWSPAPER PUBLICATIONS API
# ============================================================

def newspaper_publications_api(request):

    publications = NewspaperPublication.objects.filter(
        published=True
    ).order_by(
        "-display_order"
    )

    data = []

    for publication in publications:
        data.append({
            "id": publication.id,
            "title": publication.title,
            "financial_year": publication.financial_year,
            "disclosure_date": (
                publication.disclosure_date.strftime("%d-%m-%Y")
                if publication.disclosure_date
                else None
            ),
            "pdf_file": (
                request.build_absolute_uri(
                    publication.pdf_file.url
                )
                if publication.pdf_file
                else None
            ),
            "external_url": publication.external_url,
            "published": publication.published,
            "display_order": publication.display_order,
        })

    return JsonResponse(data, safe=False)


# ============================================================
# STOCK EXCHANGE DISCLOSURES API
# ============================================================

def stock_exchange_disclosures_api(request):

    disclosures = StockExchangeDisclosure.objects.filter(
        published=True
    ).order_by(
        "-display_order"
    )

    data = []

    for disclosure in disclosures:
        data.append({
            "id": disclosure.id,
            "title": disclosure.title,
            "financial_year": disclosure.financial_year,
            "disclosure_date": (
                disclosure.disclosure_date.strftime("%d-%m-%Y")
                if disclosure.disclosure_date
                else None
            ),
            "pdf_file": (
                request.build_absolute_uri(
                    disclosure.pdf_file.url
                )
                if disclosure.pdf_file
                else None
            ),
            "external_url": disclosure.external_url,
            "published": disclosure.published,
            "display_order": disclosure.display_order,
        })

    return JsonResponse(data, safe=False)


# ============================================================
# CORPORATE GOVERNANCE API
# ============================================================

def corporate_governance_api(request):

    documents = CorporateGovernance.objects.filter(
        published=True
    ).order_by(
        "-display_order"
    )

    data = []

    for document in documents:
        data.append({
            "id": document.id,
            "title": document.title,
            "financial_year": document.financial_year,
            "quarter": document.quarter,
            "pdf_file": (
                request.build_absolute_uri(
                    document.pdf_file.url
                )
                if document.pdf_file
                else None
            ),
            "external_url": document.external_url,
            "published": document.published,
            "display_order": document.display_order,
        })

    return JsonResponse(data, safe=False)


# ============================================================
# SHAREHOLDING PATTERN API
# ============================================================

def shareholding_pattern_api(request):

    documents = ShareholdingPattern.objects.filter(
        published=True
    ).order_by(
        "-display_order"
    )

    data = []

    for document in documents:
        data.append({
            "id": document.id,
            "title": document.title,
            "financial_year": document.financial_year,
            "quarter": document.quarter,
            "pdf_file": (
                request.build_absolute_uri(
                    document.pdf_file.url
                )
                if document.pdf_file
                else None
            ),
            "external_url": document.external_url,
            "published": document.published,
            "display_order": document.display_order,
        })

    return JsonResponse(data, safe=False)


# ============================================================
# SEBI DOCUMENTS API
# ============================================================

def sebi_documents_api(request):

    documents = SEBIDocument.objects.filter(
        published=True
    ).order_by(
        "-display_order"
    )

    data = []

    for document in documents:
        data.append({
            "id": document.id,
            "title": document.title,
            "category": document.category,
            "pdf_file": (
                request.build_absolute_uri(
                    document.pdf_file.url
                )
                if document.pdf_file
                else None
            ),
            "external_url": document.external_url,
            "published": document.published,
            "display_order": document.display_order,
        })

    return JsonResponse(data, safe=False)


# ============================================================
# INVESTOR FORMS API
# ============================================================

def investor_forms_api(request):

    forms = InvestorForm.objects.filter(
        published=True
    ).order_by(
        "-display_order"
    )

    data = []

    for form in forms:
        data.append({
            "id": form.id,
            "title": form.title,
            "category": form.category,
            "description": form.description,
            "pdf_file": (
                request.build_absolute_uri(
                    form.pdf_file.url
                )
                if form.pdf_file
                else None
            ),
            "external_url": form.external_url,
            "published": form.published,
            "display_order": form.display_order,
        })

    return JsonResponse(data, safe=False)


# ============================================================
# TAX DECLARATIONS API
# ============================================================

def tax_declarations_api(request):

    declarations = TaxDeclaration.objects.filter(
        published=True
    ).order_by(
        "-display_order"
    )

    data = []

    for declaration in declarations:
        data.append({
            "id": declaration.id,
            "title": declaration.title,
            "applicable_to": declaration.applicable_to,
            "description": declaration.description,
            "pdf_file": (
                request.build_absolute_uri(
                    declaration.pdf_file.url
                )
                if declaration.pdf_file
                else None
            ),
            "external_url": declaration.external_url,
            "published": declaration.published,
            "display_order": declaration.display_order,
        })

    return JsonResponse(data, safe=False)


# ============================================================
# UNCLAIMED DIVIDENDS API
# ============================================================

def unclaimed_dividends_api(request):

    dividends = UnclaimedDividend.objects.filter(
        published=True
    ).order_by(
        "-display_order"
    )

    data = []

    for dividend in dividends:
        data.append({
            "id": dividend.id,
            "title": dividend.title,
            "financial_year": dividend.financial_year,
            "dividend_declaration_date": (
                dividend.dividend_declaration_date.strftime(
                    "%d-%m-%Y"
                )
                if dividend.dividend_declaration_date
                else None
            ),
            "dividend_type": dividend.dividend_type,
            "iepf_transfer_due_date": (
                dividend.iepf_transfer_due_date.strftime(
                    "%d-%m-%Y"
                )
                if dividend.iepf_transfer_due_date
                else None
            ),
            "pdf_file": (
                request.build_absolute_uri(
                    dividend.pdf_file.url
                )
                if dividend.pdf_file
                else None
            ),
            "external_url": dividend.external_url,
            "published": dividend.published,
            "display_order": dividend.display_order,
        })

    return JsonResponse(data, safe=False)


# ============================================================
# SUBSIDIARY FINANCIALS API
# ============================================================

def subsidiary_financials_api(request):

    financials = SubsidiaryFinancial.objects.filter(
        published=True
    ).order_by(
        "-display_order"
    )

    data = []

    for financial in financials:
        data.append({
            "id": financial.id,
            "title": financial.title,
            "financial_year": financial.financial_year,
            "company_name": financial.company_name,
            "financial_type": financial.financial_type,
            "pdf_file": (
                request.build_absolute_uri(
                    financial.pdf_file.url
                )
                if financial.pdf_file
                else None
            ),
            "external_url": financial.external_url,
            "published": financial.published,
            "display_order": financial.display_order,
        })

    return JsonResponse(data, safe=False)


# ============================================================
# DASHBOARD STATISTICS API
# ============================================================

@login_required(login_url="dashboard_login")
@role_required(['ADMIN', 'EMPLOYEE'])
def dashboard_statistics_api(request):

    # --------------------------------------------------------
    # 1. Annual Report
    # --------------------------------------------------------
    annual_report = AnnualReport.objects.count()

    # --------------------------------------------------------
    # 2. Financial Results
    # --------------------------------------------------------
    financial_result = FinancialResult.objects.count()

    # --------------------------------------------------------
    # 3. Annual Returns
    # --------------------------------------------------------
    annual_return = AnnualReturn.objects.count()

    # --------------------------------------------------------
    # 4. Corporate Announcements
    # --------------------------------------------------------
    shareholder_notice = ShareholderNotice.objects.count()
    newspaper_publication = NewspaperPublication.objects.count()
    stock_exchange_disclosure = StockExchangeDisclosure.objects.count()

    corporate_announcements = (
        shareholder_notice
        + newspaper_publication
        + stock_exchange_disclosure
    )

    # --------------------------------------------------------
    # 5. Corporate Governance
    # --------------------------------------------------------
    corporate_governance = CorporateGovernance.objects.count()

    # --------------------------------------------------------
    # 6. Shareholding Pattern
    # --------------------------------------------------------
    shareholding_pattern = ShareholdingPattern.objects.count()

    # --------------------------------------------------------
    # 7. SEBI LODR Documents
    # --------------------------------------------------------
    sebi_document = SEBIDocument.objects.count()

    # --------------------------------------------------------
    # 8. Investor Forms & Declaration
    #
    # Parent section contains:
    #   - KYC / Nomination
    #   - Tax Declaration
    #   - Unclaimed Dividend
    # --------------------------------------------------------
    investor_form = InvestorForm.objects.count()
    tax_declaration = TaxDeclaration.objects.count()
    unclaimed_dividend = UnclaimedDividend.objects.count()

    # KYC is stored inside InvestorForm using the category field.
    kyc_nomination = InvestorForm.objects.filter(
        category__icontains="kyc"
    ).count()

    # Also support existing records where the category contains
    # "nomination" instead of "kyc".
    if kyc_nomination == 0:
        kyc_nomination = InvestorForm.objects.filter(
            category__icontains="nomination"
        ).count()

    investor_forms_declaration = (
        investor_form
        + tax_declaration
        + unclaimed_dividend
    )

    # --------------------------------------------------------
    # 9. Subsidiary Financial
    # --------------------------------------------------------
    subsidiary_financial = SubsidiaryFinancial.objects.count()

    # --------------------------------------------------------
    # TOP-LEVEL DASHBOARD COUNTS
    #
    # These are the ONLY counts used for:
    #   - Dashboard cards
    #   - Total Documents
    #   - Summary
    #   - Donut chart
    # --------------------------------------------------------
    section_counts = {
        "annual_report": annual_report,

        "financial_result": financial_result,

        "annual_return": annual_return,

        "corporate_announcements": corporate_announcements,

        "corporate_governance": corporate_governance,

        "shareholding_pattern": shareholding_pattern,

        "sebi_document": sebi_document,

        "investor_form": investor_forms_declaration,

        "subsidiary_financial": subsidiary_financial,
    }

    # Dynamic custom sections (created via Sections CRUD)
    ensure_system_sections()
    custom_sections_payload = []
    for sec in Section.objects.filter(is_system=False, is_active=True).order_by("display_order", "name"):
        count = sec.custom_documents.count()
        key = f"custom_{sec.id}"
        section_counts[key] = count
        custom_sections_payload.append({
            "id": sec.id,
            "key": key,
            "name": sec.name,
            "slug": sec.slug,
            "icon": sec.icon or "📁",
            "count": count,
            "is_system": False,
        })

    # --------------------------------------------------------
    # TOTAL DOCUMENTS
    # --------------------------------------------------------
    total_documents = sum(section_counts.values())

    # --------------------------------------------------------
    # RETURN RESPONSE
    #
    # section_counts = system + custom section counts
    # custom_sections = list for frontend dynamic cards
    # child_counts   = individual child/subsection counts
    # --------------------------------------------------------
    return JsonResponse({
        "total_documents": total_documents,

        "section_counts": section_counts,

        "custom_sections": custom_sections_payload,

        "child_counts": {
            "shareholder_notice": shareholder_notice,
            "newspaper_publication": newspaper_publication,
            "stock_exchange_disclosure": stock_exchange_disclosure,

            "kyc_nomination": kyc_nomination,
            "tax_declaration": tax_declaration,
            "unclaimed_dividend": unclaimed_dividend,
        }
    })

    # Raw counts from each model
    annual_report          = AnnualReport.objects.count()
    financial_result       = FinancialResult.objects.count()
    annual_return          = AnnualReturn.objects.count()
    corporate_governance   = CorporateGovernance.objects.count()
    shareholding_pattern   = ShareholdingPattern.objects.count()
    sebi_document          = SEBIDocument.objects.count()
    subsidiary_financial   = SubsidiaryFinancial.objects.count()

    # Corporate Announcements = 3 child models
    corporate_announcements = (
        ShareholderNotice.objects.count() +
        NewspaperPublication.objects.count() +
        StockExchangeDisclosure.objects.count()
    )

    # Investor Forms & Declaration = InvestorForm + TaxDeclaration + UnclaimedDividend
    investor_form = (
        InvestorForm.objects.count() +
        TaxDeclaration.objects.count() +
        UnclaimedDividend.objects.count()
    )

    section_counts = {
        "annual_report":            annual_report,
        "financial_result":         financial_result,
        "annual_return":            annual_return,
        "corporate_announcements":  corporate_announcements,
        "corporate_governance":     corporate_governance,
        "shareholding_pattern":     shareholding_pattern,
        "sebi_document":            sebi_document,
        "investor_form":            investor_form,
        "subsidiary_financial":     subsidiary_financial,
    }

    total_documents = sum(section_counts.values())

    return JsonResponse({
        "total_documents": total_documents,
        "section_counts": section_counts,
    })

# ============================================================
# EDIT DOCUMENT - GET DOCUMENT DATA
# ============================================================

@login_required(login_url="dashboard_login")
@role_required(['ADMIN', 'EMPLOYEE'])
def edit_investor_document(request, document_id, section):

    try:

        # ====================================================
        # ANNUAL REPORT
        # ====================================================

        if section == "annual_report":

            obj = AnnualReport.objects.get(
                id=document_id
            )

            data = {
                "id": obj.id,
                "section": "annual_report",
                "title": obj.title,
                "financial_year": obj.financial_year,
                "external_url": obj.external_url,
                "pdf_file": (
                    request.build_absolute_uri(
                        obj.pdf_file.url
                    )
                    if obj.pdf_file
                    else None
                ),
            }


        # ====================================================
        # FINANCIAL RESULTS
        # ====================================================

        elif section == "financial_result":

            obj = FinancialResult.objects.get(
                id=document_id
            )

            data = {
                "id": obj.id,
                "section": "financial_result",
                "title": obj.title,
                "financial_year": obj.financial_year,
                "quarter": obj.quarter,
                "release_date": (
                    obj.release_date.strftime("%Y-%m-%d")
                    if obj.release_date
                    else None
                ),
                "external_url": obj.external_url,
                "pdf_file": (
                    request.build_absolute_uri(
                        obj.pdf_file.url
                    )
                    if obj.pdf_file
                    else None
                ),
            }


        # ====================================================
        # ANNUAL RETURNS
        # ====================================================

        elif section == "annual_return":

            obj = AnnualReturn.objects.get(
                id=document_id
            )

            data = {
                "id": obj.id,
                "section": "annual_return",
                "title": obj.title,
                "financial_year": obj.financial_year,
                "external_url": obj.external_url,
                "pdf_file": (
                    request.build_absolute_uri(
                        obj.pdf_file.url
                    )
                    if obj.pdf_file
                    else None
                ),
            }


        # ====================================================
        # CORPORATE GOVERNANCE
        # ====================================================

        elif section == "corporate_governance":

            obj = CorporateGovernance.objects.get(
                id=document_id
            )

            data = {
                "id": obj.id,
                "section": "corporate_governance",
                "title": obj.title,
                "financial_year": obj.financial_year,
                "quarter": obj.quarter,
                "external_url": obj.external_url,
                "pdf_file": (
                    request.build_absolute_uri(
                        obj.pdf_file.url
                    )
                    if obj.pdf_file
                    else None
                ),
            }


        # ====================================================
        # SHAREHOLDING PATTERN
        # ====================================================

        elif section == "shareholding_pattern":

            obj = ShareholdingPattern.objects.get(
                id=document_id
            )

            data = {
                "id": obj.id,
                "section": "shareholding_pattern",
                "title": obj.title,
                "financial_year": obj.financial_year,
                "quarter": obj.quarter,
                "external_url": obj.external_url,
                "pdf_file": (
                    request.build_absolute_uri(
                        obj.pdf_file.url
                    )
                    if obj.pdf_file
                    else None
                ),
            }


        # ====================================================
        # SHAREHOLDER NOTICE
        # ====================================================

        elif section == "shareholder_notice":

            obj = ShareholderNotice.objects.get(
                id=document_id
            )

            data = {
                "id": obj.id,
                "section": "shareholder_notice",
                "title": obj.title,
                "financial_year": obj.financial_year,
                "notice_type": obj.notice_type,
                "disclosure_date": (
                    obj.disclosure_date.strftime("%Y-%m-%d")
                    if obj.disclosure_date
                    else None
                ),
                "meeting_date": (
                    obj.meeting_date.strftime("%Y-%m-%d")
                    if obj.meeting_date
                    else None
                ),
                "external_url": obj.external_url,
                "pdf_file": (
                    request.build_absolute_uri(
                        obj.pdf_file.url
                    )
                    if obj.pdf_file
                    else None
                ),
            }


        # ====================================================
        # NEWSPAPER PUBLICATION
        # ====================================================

        elif section == "newspaper_publication":

            obj = NewspaperPublication.objects.get(
                id=document_id
            )

            data = {
                "id": obj.id,
                "section": "newspaper_publication",
                "title": obj.title,
                "financial_year": obj.financial_year,
                "disclosure_date": (
                    obj.disclosure_date.strftime("%Y-%m-%d")
                    if obj.disclosure_date
                    else None
                ),
                "external_url": obj.external_url,
                "pdf_file": (
                    request.build_absolute_uri(
                        obj.pdf_file.url
                    )
                    if obj.pdf_file
                    else None
                ),
            }


        # ====================================================
        # STOCK EXCHANGE DISCLOSURE
        # ====================================================

        elif section == "stock_exchange_disclosure":

            obj = StockExchangeDisclosure.objects.get(
                id=document_id
            )

            data = {
                "id": obj.id,
                "section": "stock_exchange_disclosure",
                "title": obj.title,
                "financial_year": obj.financial_year,
                "disclosure_date": (
                    obj.disclosure_date.strftime("%Y-%m-%d")
                    if obj.disclosure_date
                    else None
                ),
                "external_url": obj.external_url,
                "pdf_file": (
                    request.build_absolute_uri(
                        obj.pdf_file.url
                    )
                    if obj.pdf_file
                    else None
                ),
            }


        # ====================================================
        # SEBI DOCUMENT
        # ====================================================

        elif section == "sebi_document":

            obj = SEBIDocument.objects.get(
                id=document_id
            )

            data = {
                "id": obj.id,
                "section": "sebi_document",
                "title": obj.title,
                "category": obj.category,
                "external_url": obj.external_url,
                "pdf_file": (
                    request.build_absolute_uri(
                        obj.pdf_file.url
                    )
                    if obj.pdf_file
                    else None
                ),
            }


        # ====================================================
        # INVESTOR FORM
        # ====================================================

        elif section == "investor_form":

            obj = InvestorForm.objects.get(
                id=document_id
            )

            data = {
                "id": obj.id,
                "section": "investor_form",
                "title": obj.title,
                "category": obj.category,
                "description": obj.description,
                "external_url": obj.external_url,
                "pdf_file": (
                    request.build_absolute_uri(
                        obj.pdf_file.url
                    )
                    if obj.pdf_file
                    else None
                ),
            }


        # ====================================================
        # TAX DECLARATION
        # ====================================================

        elif section == "tax_declaration":

            obj = TaxDeclaration.objects.get(
                id=document_id
            )

            data = {
                "id": obj.id,
                "section": "tax_declaration",
                "title": obj.title,
                "applicable_to": obj.applicable_to,
                "description": obj.description,
                "external_url": obj.external_url,
                "pdf_file": (
                    request.build_absolute_uri(
                        obj.pdf_file.url
                    )
                    if obj.pdf_file
                    else None
                ),
            }


        # ====================================================
        # UNCLAIMED DIVIDEND
        # ====================================================

        elif section == "unclaimed_dividend":

            obj = UnclaimedDividend.objects.get(
                id=document_id
            )

            data = {
                "id": obj.id,
                "section": "unclaimed_dividend",
                "title": obj.title,
                "financial_year": obj.financial_year,
                "dividend_declaration_date": (
                    obj.dividend_declaration_date.strftime("%Y-%m-%d")
                    if obj.dividend_declaration_date
                    else None
                ),
                "dividend_type": obj.dividend_type,
                "iepf_transfer_due_date": (
                    obj.iepf_transfer_due_date.strftime("%Y-%m-%d")
                    if obj.iepf_transfer_due_date
                    else None
                ),
                "external_url": obj.external_url,
                "pdf_file": (
                    request.build_absolute_uri(
                        obj.pdf_file.url
                    )
                    if obj.pdf_file
                    else None
                ),
            }


        # ====================================================
        # SUBSIDIARY FINANCIAL
        # ====================================================

        elif section == "subsidiary_financial":

            obj = SubsidiaryFinancial.objects.get(
                id=document_id
            )

            data = {
                "id": obj.id,
                "section": "subsidiary_financial",
                "title": obj.title,
                "financial_year": obj.financial_year,
                "company_name": obj.company_name,
                "financial_type": obj.financial_type,
                "external_url": obj.external_url,
                "pdf_file": (
                    request.build_absolute_uri(
                        obj.pdf_file.url
                    )
                    if obj.pdf_file
                    else None
                ),
            }


        else:

            return JsonResponse(
                {
                    "success": False,
                    "message": "Invalid document section."
                },
                status=400
            )


        return JsonResponse({
            "success": True,
            "document": data
        })


    except (
        AnnualReport.DoesNotExist,
        FinancialResult.DoesNotExist,
        AnnualReturn.DoesNotExist,
        CorporateGovernance.DoesNotExist,
        ShareholdingPattern.DoesNotExist,
        ShareholderNotice.DoesNotExist,
        NewspaperPublication.DoesNotExist,
        StockExchangeDisclosure.DoesNotExist,
        SEBIDocument.DoesNotExist,
        InvestorForm.DoesNotExist,
        TaxDeclaration.DoesNotExist,
        UnclaimedDividend.DoesNotExist,
        SubsidiaryFinancial.DoesNotExist,
    ):

        return JsonResponse(
            {
                "success": False,
                "message": "Document not found."
            },
            status=404
        )



@login_required(login_url="dashboard_login")
@role_required(['ADMIN', 'EMPLOYEE'])
def update_investor_document(request):
    """
    POST – Update an existing investor document.
    Expects: document_id, section, and the same fields as upload.
    """

    if request.method != "POST":
        return JsonResponse(
            {"success": False, "message": "Invalid request method."},
            status=405
        )

    document_id = request.POST.get("document_id", "").strip()
    section     = request.POST.get("section", "").strip()
    title       = request.POST.get("title", "").strip()
    pdf_file    = request.FILES.get("pdf_file")
    external_url = request.POST.get("external_url", "").strip() or None

    if not document_id or not section:
        return JsonResponse(
            {"success": False, "message": "Document ID and section are required."},
            status=400
        )

    if not title:
        return JsonResponse(
            {"success": False, "message": "Document title is required."},
            status=400
        )

    try:
        document_id = int(document_id)
        obj = None
        old_snapshot = {}

        def begin_update(model):
            nonlocal old_snapshot
            document = model.objects.get(id=document_id)
            old_snapshot = snapshot_document(document)
            return document

        # -------------------------------------------------------
        # Helper to update common fields
        # -------------------------------------------------------
        def update_common(document):
            document.title = title
            document.external_url = external_url
            if pdf_file:
                document.pdf_file = pdf_file

            # Update publish status if sent
            published_raw = request.POST.get("published")
            if published_raw is not None:
                document.published = str(published_raw).strip().lower() in ("true", "1", "yes", "on")

            document.save()

        # -------------------------------------------------------
        # ANNUAL REPORT
        # -------------------------------------------------------
        if section == "annual_report":
            obj = begin_update(AnnualReport)
            obj.financial_year = request.POST.get("financial_year", "").strip()
            update_common(obj)

        # -------------------------------------------------------
        # FINANCIAL RESULT
        # -------------------------------------------------------
        elif section == "financial_result":
            obj = begin_update(FinancialResult)
            obj.financial_year = request.POST.get("financial_year", "").strip()
            obj.quarter = request.POST.get("quarter", "").strip()
            release = request.POST.get("release_date") or None
            obj.release_date = release
            update_common(obj)

        # -------------------------------------------------------
        # ANNUAL RETURN
        # -------------------------------------------------------
        elif section == "annual_return":
            obj = begin_update(AnnualReturn)
            obj.financial_year = request.POST.get("financial_year", "").strip()
            update_common(obj)

        # -------------------------------------------------------
        # CORPORATE GOVERNANCE
        # -------------------------------------------------------
        elif section == "corporate_governance":
            obj = begin_update(CorporateGovernance)
            obj.financial_year = request.POST.get("financial_year", "").strip()
            obj.quarter = request.POST.get("quarter", "").strip()
            update_common(obj)

        # -------------------------------------------------------
        # SHAREHOLDING PATTERN
        # -------------------------------------------------------
        elif section == "shareholding_pattern":
            obj = begin_update(ShareholdingPattern)
            obj.financial_year = request.POST.get("financial_year", "").strip()
            obj.quarter = request.POST.get("quarter", "").strip()
            update_common(obj)

        # -------------------------------------------------------
        # SHAREHOLDER NOTICE
        # -------------------------------------------------------
        elif section == "shareholder_notice":
            obj = begin_update(ShareholderNotice)
            obj.financial_year = request.POST.get("financial_year", "").strip()
            obj.notice_type = request.POST.get("notice_type", "").strip()
            obj.disclosure_date = request.POST.get("disclosure_date") or None
            obj.meeting_date = request.POST.get("meeting_date") or None
            update_common(obj)

        # -------------------------------------------------------
        # NEWSPAPER PUBLICATION
        # -------------------------------------------------------
        elif section == "newspaper_publication":
            obj = begin_update(NewspaperPublication)
            obj.financial_year = request.POST.get("financial_year", "").strip()
            obj.disclosure_date = request.POST.get("disclosure_date") or None
            update_common(obj)

        # -------------------------------------------------------
        # STOCK EXCHANGE DISCLOSURE
        # -------------------------------------------------------
        elif section == "stock_exchange_disclosure":
            obj = begin_update(StockExchangeDisclosure)
            obj.financial_year = request.POST.get("financial_year", "").strip()
            obj.disclosure_date = request.POST.get("disclosure_date") or None
            update_common(obj)

        # -------------------------------------------------------
        # SEBI DOCUMENT
        # -------------------------------------------------------
        elif section == "sebi_document":
            obj = begin_update(SEBIDocument)
            obj.category = request.POST.get("category", "").strip()
            update_common(obj)

        # -------------------------------------------------------
        # INVESTOR FORM
        # -------------------------------------------------------
        elif section == "investor_form":
            obj = begin_update(InvestorForm)
            obj.category = request.POST.get("category", "").strip()
            obj.description = request.POST.get("description", "").strip()
            update_common(obj)

        # -------------------------------------------------------
        # TAX DECLARATION
        # -------------------------------------------------------
        elif section == "tax_declaration":
            obj = begin_update(TaxDeclaration)
            obj.applicable_to = request.POST.get("applicable_to", "").strip()
            obj.description = request.POST.get("description", "").strip()
            update_common(obj)

        # -------------------------------------------------------
        # UNCLAIMED DIVIDEND
        # -------------------------------------------------------
        elif section == "unclaimed_dividend":
            obj = begin_update(UnclaimedDividend)
            obj.financial_year = request.POST.get("financial_year", "").strip()
            obj.dividend_declaration_date = request.POST.get("dividend_declaration_date") or None
            obj.dividend_type = request.POST.get("dividend_type", "").strip()
            obj.iepf_transfer_due_date = request.POST.get("iepf_transfer_due_date") or None
            update_common(obj)

        # -------------------------------------------------------
        # SUBSIDIARY FINANCIAL
        # -------------------------------------------------------
        elif section == "subsidiary_financial":
            obj = begin_update(SubsidiaryFinancial)
            obj.financial_year = request.POST.get("financial_year", "").strip()
            obj.company_name = request.POST.get("company_name", "").strip()
            obj.financial_type = request.POST.get("financial_type", "").strip()
            update_common(obj)

        else:
            return JsonResponse(
                {"success": False, "message": f"Invalid section: {section}"},
                status=400
            )

        details = describe_document_changes(
            old_snapshot,
            snapshot_document(obj) if obj else {},
            pdf_replaced=bool(pdf_file),
        )
        log_audit(
            request,
            title=title,
            section=section,
            action="edited",
            document_id=document_id,
            details=details,
        )

        return JsonResponse({
            "success": True,
            "message": "Document updated successfully."
        })

    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Update failed: {str(e)}"},
            status=500
        )
    
# ============================================================
# DASHBOARD DOCUMENTS API
# ============================================================

@login_required(login_url="dashboard_login")
@role_required(['ADMIN', 'EMPLOYEE'])
def dashboard_documents_api(request):

    documents = []

    # --------------------------------------------------------
    # 1. Annual Report
    # --------------------------------------------------------
    for obj in AnnualReport.objects.all().order_by("-display_order"):
        documents.append({
            "id": obj.id,
            "section": "annual_report",
            "title": obj.title,
            "financial_year": obj.financial_year,
            "date": obj.created_at.strftime("%d-%m-%Y"),
            "created_at": obj.created_at.isoformat(),
            "updated_at": obj.updated_at.isoformat(),
            "published": obj.published,
            "display_order": obj.display_order,
            "pdf_file": obj.pdf_file.url if obj.pdf_file else None,
            "external_url": obj.external_url,
        })

    # --------------------------------------------------------
    # 2. Financial Results
    # --------------------------------------------------------
    for obj in FinancialResult.objects.all().order_by("-display_order"):
        documents.append({
            "id": obj.id,
            "section": "financial_result",
            "title": obj.title,
            "financial_year": obj.financial_year,
            "quarter": obj.quarter,
            "release_date": obj.release_date.strftime("%d-%m-%Y") if obj.release_date else None,
            "date": obj.created_at.strftime("%d-%m-%Y"),
            "created_at": obj.created_at.isoformat(),
            "updated_at": obj.updated_at.isoformat(),
            "published": obj.published,
            "display_order": obj.display_order,
            "pdf_file": obj.pdf_file.url if obj.pdf_file else None,
            "external_url": obj.external_url,
        })

    # --------------------------------------------------------
    # 3. Annual Returns
    # --------------------------------------------------------
    for obj in AnnualReturn.objects.all().order_by("-display_order"):
        documents.append({
            "id": obj.id,
            "section": "annual_return",
            "title": obj.title,
            "financial_year": obj.financial_year,
            "date": obj.created_at.strftime("%d-%m-%Y"),
            "created_at": obj.created_at.isoformat(),
            "updated_at": obj.updated_at.isoformat(),
            "published": obj.published,
            "display_order": obj.display_order,
            "pdf_file": obj.pdf_file.url if obj.pdf_file else None,
            "external_url": obj.external_url,
        })

    # --------------------------------------------------------
    # 4a. Corporate Announcements → Shareholder Notice
    # --------------------------------------------------------
    for obj in ShareholderNotice.objects.all().order_by("-display_order"):
        documents.append({
            "id": obj.id,
            "section": "shareholder_notice",          # child key
            "parent_section": "corporate_announcements",
            "title": obj.title,
            "financial_year": obj.financial_year,
            "notice_type": obj.notice_type,
            "disclosure_date": obj.disclosure_date.strftime("%d-%m-%Y") if obj.disclosure_date else None,
            "meeting_date": obj.meeting_date.strftime("%d-%m-%Y") if obj.meeting_date else None,
            "date": obj.created_at.strftime("%d-%m-%Y"),
            "created_at": obj.created_at.isoformat(),
            "updated_at": obj.updated_at.isoformat(),
            "published": obj.published,
            "display_order": obj.display_order,
            "pdf_file": obj.pdf_file.url if obj.pdf_file else None,
            "external_url": obj.external_url,
        })

    # --------------------------------------------------------
    # 4b. Corporate Announcements → Newspaper Publication
    # --------------------------------------------------------
    for obj in NewspaperPublication.objects.all().order_by("-display_order"):
        documents.append({
            "id": obj.id,
            "section": "newspaper_publication",
            "parent_section": "corporate_announcements",
            "title": obj.title,
            "financial_year": obj.financial_year,
            "disclosure_date": obj.disclosure_date.strftime("%d-%m-%Y") if obj.disclosure_date else None,
            "date": obj.created_at.strftime("%d-%m-%Y"),
            "created_at": obj.created_at.isoformat(),
            "updated_at": obj.updated_at.isoformat(),
            "published": obj.published,
            "display_order": obj.display_order,
            "pdf_file": obj.pdf_file.url if obj.pdf_file else None,
            "external_url": obj.external_url,
        })

    # --------------------------------------------------------
    # 4c. Corporate Announcements → Stock Exchange Disclosure
    # --------------------------------------------------------
    for obj in StockExchangeDisclosure.objects.all().order_by("-display_order"):
        documents.append({
            "id": obj.id,
            "section": "stock_exchange_disclosure",
            "parent_section": "corporate_announcements",
            "title": obj.title,
            "financial_year": obj.financial_year,
            "disclosure_date": obj.disclosure_date.strftime("%d-%m-%Y") if obj.disclosure_date else None,
            "date": obj.created_at.strftime("%d-%m-%Y"),
            "created_at": obj.created_at.isoformat(),
            "updated_at": obj.updated_at.isoformat(),
            "published": obj.published,
            "display_order": obj.display_order,
            "pdf_file": obj.pdf_file.url if obj.pdf_file else None,
            "external_url": obj.external_url,
        })

    # --------------------------------------------------------
    # 5. Corporate Governance
    # --------------------------------------------------------
    for obj in CorporateGovernance.objects.all().order_by("-display_order"):
        documents.append({
            "id": obj.id,
            "section": "corporate_governance",
            "title": obj.title,
            "financial_year": obj.financial_year,
            "quarter": obj.quarter,
            "date": obj.created_at.strftime("%d-%m-%Y"),
            "created_at": obj.created_at.isoformat(),
            "updated_at": obj.updated_at.isoformat(),
            "published": obj.published,
            "display_order": obj.display_order,
            "pdf_file": obj.pdf_file.url if obj.pdf_file else None,
            "external_url": obj.external_url,
        })

    # --------------------------------------------------------
    # 6. Shareholding Pattern
    # --------------------------------------------------------
    for obj in ShareholdingPattern.objects.all().order_by("-display_order"):
        documents.append({
            "id": obj.id,
            "section": "shareholding_pattern",
            "title": obj.title,
            "financial_year": obj.financial_year,
            "quarter": obj.quarter,
            "date": obj.created_at.strftime("%d-%m-%Y"),
            "created_at": obj.created_at.isoformat(),
            "updated_at": obj.updated_at.isoformat(),
            "published": obj.published,
            "display_order": obj.display_order,
            "pdf_file": obj.pdf_file.url if obj.pdf_file else None,
            "external_url": obj.external_url,
        })

    # --------------------------------------------------------
    # 7. SEBI Documents
    # --------------------------------------------------------
    for obj in SEBIDocument.objects.all().order_by("-display_order"):
        documents.append({
            "id": obj.id,
            "section": "sebi_document",
            "title": obj.title,
            "category": obj.category,
            "date": obj.created_at.strftime("%d-%m-%Y"),
            "created_at": obj.created_at.isoformat(),
            "updated_at": obj.updated_at.isoformat(),
            "published": obj.published,
            "display_order": obj.display_order,
            "pdf_file": obj.pdf_file.url if obj.pdf_file else None,
            "external_url": obj.external_url,
        })

    # --------------------------------------------------------
    # 8a. Investor Forms
    # --------------------------------------------------------
    for obj in InvestorForm.objects.all().order_by("-display_order"):
        documents.append({
            "id": obj.id,
            "section": "investor_form",
            "title": obj.title,
            "category": obj.category,
            "description": obj.description,
            "date": obj.created_at.strftime("%d-%m-%Y"),
            "created_at": obj.created_at.isoformat(),
            "updated_at": obj.updated_at.isoformat(),
            "published": obj.published,
            "display_order": obj.display_order,
            "pdf_file": obj.pdf_file.url if obj.pdf_file else None,
            "external_url": obj.external_url,
        })

    # --------------------------------------------------------
    # 8b. Tax Declarations (still under Investor Forms group)
    # --------------------------------------------------------
    for obj in TaxDeclaration.objects.all().order_by("-display_order"):
        documents.append({
            "id": obj.id,
            "section": "tax_declaration",
            "parent_section": "investor_form",
            "title": obj.title,
            "applicable_to": obj.applicable_to,
            "description": obj.description,
            "date": obj.created_at.strftime("%d-%m-%Y"),
            "created_at": obj.created_at.isoformat(),
            "updated_at": obj.updated_at.isoformat(),
            "published": obj.published,
            "display_order": obj.display_order,
            "pdf_file": obj.pdf_file.url if obj.pdf_file else None,
            "external_url": obj.external_url,
        })

    # --------------------------------------------------------
    # 8c. Unclaimed Dividends (still under Investor Forms group)
    # --------------------------------------------------------
    for obj in UnclaimedDividend.objects.all().order_by("-display_order"):
        documents.append({
            "id": obj.id,
            "section": "unclaimed_dividend",
            "parent_section": "investor_form",
            "title": obj.title,
            "financial_year": obj.financial_year,
            "dividend_declaration_date": obj.dividend_declaration_date.strftime("%d-%m-%Y") if obj.dividend_declaration_date else None,
            "dividend_type": obj.dividend_type,
            "iepf_transfer_due_date": obj.iepf_transfer_due_date.strftime("%d-%m-%Y") if obj.iepf_transfer_due_date else None,
            "date": obj.created_at.strftime("%d-%m-%Y"),
            "created_at": obj.created_at.isoformat(),
            "updated_at": obj.updated_at.isoformat(),
            "published": obj.published,
            "display_order": obj.display_order,
            "pdf_file": obj.pdf_file.url if obj.pdf_file else None,
            "external_url": obj.external_url,
        })

    # --------------------------------------------------------
    # 9. Subsidiary Financial
    # --------------------------------------------------------
    for obj in SubsidiaryFinancial.objects.all().order_by("-display_order"):
        documents.append({
            "id": obj.id,
            "section": "subsidiary_financial",
            "title": obj.title,
            "financial_year": obj.financial_year,
            "company_name": obj.company_name,
            "financial_type": obj.financial_type,
            "date": obj.created_at.strftime("%d-%m-%Y"),
            "created_at": obj.created_at.isoformat(),
            "updated_at": obj.updated_at.isoformat(),
            "published": obj.published,
            "display_order": obj.display_order,
            "pdf_file": obj.pdf_file.url if obj.pdf_file else None,
            "external_url": obj.external_url,
        })

    # --------------------------------------------------------
    # Custom sections (created via Sections CRUD)
    # --------------------------------------------------------
    for obj in CustomDocument.objects.select_related("section", "subsection").all().order_by("-display_order"):
        documents.append({
            "id": obj.id,
            "section": f"custom_{obj.section_id}",
            "section_name": obj.section.name if obj.section else "",
            "subsection_name": obj.subsection.name if obj.subsection else "",
            "title": obj.title,
            "extra_info": obj.extra_info,
            "date": obj.created_at.strftime("%d-%m-%Y"),
            "created_at": obj.created_at.isoformat(),
            "updated_at": obj.updated_at.isoformat(),
            "published": obj.published,
            "display_order": obj.display_order,
            "pdf_file": obj.pdf_file.url if obj.pdf_file else None,
            "external_url": obj.external_url,
            "is_custom": True,
        })

    return JsonResponse(documents, safe=False)

# ============================================================
# INVESTORS PAGE (public)
# ============================================================

def investors_page(request):
    return render(request, "Investors.html")


# ============================================================
# UPLOAD DASHBOARD
# ============================================================

@never_cache
@login_required(login_url="dashboard_login")
def upload_dashboard(request):
    """
    Main dashboard page.
    Passes role + display name so template can show correct menus
    and the logged-in user name in the header.
    """

    # Safety: ensure profile exists
    if not hasattr(request.user, 'profile'):
        Profile.objects.create(user=request.user, role='EMPLOYEE')

    role = request.user.profile.role

    # Client must not access dashboard
    if role == 'CLIENT':
        return redirect('https://www.nibelimited.com')

    # Display name for header
    full_name = request.user.get_full_name().strip()
    display_name = full_name if full_name else request.user.username
    # Avatar initials (max 2 chars)
    if full_name:
        parts = full_name.split()
        initials = (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()
    else:
        initials = (request.user.username[:2] if request.user.username else "U").upper()

    return render(request, "Investor_Dashboard.html", {
        "user_role": role,
        "is_admin": role == "ADMIN",
        "is_employee": role == "EMPLOYEE",
        "display_name": display_name,
        "user_initials": initials,
        "username": request.user.username,
    })

# ============================================================
# DASHBOARD LOGOUT
# ============================================================

@login_required(login_url="dashboard_login")
def dashboard_logout(request):

    logout(request)

    return redirect("dashboard_login")


# ============================================================
# UPLOAD INVESTOR DOCUMENT
# ============================================================

@login_required(login_url="dashboard_login")
@role_required(['ADMIN', 'EMPLOYEE'])
def upload_investor_document(request):

    if request.method != "POST":
        return JsonResponse(
            {"success": False, "message": "Invalid request method."},
            status=405
        )

    section      = request.POST.get("section", "").strip()
    subsection   = request.POST.get("subsection", "").strip() or None
    title        = request.POST.get("title", "").strip()
    pdf_file     = request.FILES.get("pdf_file")
    external_url = request.POST.get("external_url", "").strip() or None

    # Publish status from radio button (default = Published)
    published_raw = request.POST.get("published", "true").strip().lower()
    is_published = published_raw in ("true", "1", "yes", "on")

    if not section:
        return JsonResponse(
            {"success": False, "message": "Please select a section."},
            status=400
        )

    if not title:
        return JsonResponse(
            {"success": False, "message": "Document title is required."},
            status=400
        )

    if not pdf_file and not external_url:
        return JsonResponse(
            {"success": False, "message": "Please provide either a PDF file or an external URL."},
            status=400
        )

    # ========================================================
    # FILE VALIDATION + DUPLICATE PREVENTION
    # ========================================================

    # 1. File type validation (only PDF)
    if pdf_file:
        file_name = pdf_file.name.lower()
        if not file_name.endswith(".pdf"):
            return JsonResponse(
                {"success": False, "message": "Only PDF files are allowed."},
                status=400
            )

        content_type = getattr(pdf_file, "content_type", "") or ""
        if content_type and content_type not in ("application/pdf", "application/x-pdf"):
            return JsonResponse(
                {"success": False, "message": "Invalid file type. Please upload a valid PDF."},
                status=400
            )

        # 2. File size validation (max 50 MB)
        max_size = 50 * 1024 * 1024  # 50 MB
        if pdf_file.size > max_size:
            return JsonResponse(
                {"success": False, "message": "File size must be less than 50 MB."},
                status=400
            )

    # 3. Duplicate title prevention (same title in same section)
    model_map = {
        "annual_report": AnnualReport,
        "financial_result": FinancialResult,
        "annual_return": AnnualReturn,
        "corporate_governance": CorporateGovernance,
        "shareholding_pattern": ShareholdingPattern,
        "shareholder_notice": ShareholderNotice,
        "newspaper_publication": NewspaperPublication,
        "stock_exchange_disclosure": StockExchangeDisclosure,
        "sebi_document": SEBIDocument,
        "investor_form": InvestorForm,
        "tax_declaration": TaxDeclaration,
        "unclaimed_dividend": UnclaimedDividend,
        "subsidiary_financial": SubsidiaryFinancial,
    }

    check_section = section
    if section == "corporate_announcements" and subsection:
        check_section = subsection

    model = model_map.get(check_section)
    if model and model.objects.filter(title__iexact=title).exists():
        return JsonResponse(
            {
                "success": False,
                "message": f'A document with the title "{title}" already exists in this section. Please use a different title.'
            },
            status=400
        )

    # -------------------------------------------------------
    # Map the new hierarchy (section + subsection) back to
    # the concrete model that should be used
    # -------------------------------------------------------
    effective_section = section

    if section == "corporate_announcements":
        if subsection in ("shareholder_notice", "newspaper_publication", "stock_exchange_disclosure"):
            effective_section = subsection
        else:
            return JsonResponse(
                {"success": False, "message": "Please select a Corporate Announcements subsection."},
                status=400
            )

    # For investor_form the frontend sometimes sends category
    # as the subcategory. We keep the same model.
    if section == "investor_form" and subsection:
        # still use InvestorForm model, just store the category
        pass

    try:
        # ====================================================
        # ANNUAL REPORT
        # ====================================================
        if effective_section == "annual_report":
            display_order = get_next_display_order(AnnualReport)
            AnnualReport.objects.create(
                title=title,
                pdf_file=pdf_file,
                external_url=external_url,
                published=is_published,
                display_order=display_order,
                financial_year=request.POST.get("financial_year", "").strip(),
            )

        # ====================================================
        # ANNUAL RETURN
        # ====================================================
        elif effective_section == "annual_return":
            display_order = get_next_display_order(AnnualReturn)
            AnnualReturn.objects.create(
                title=title,
                pdf_file=pdf_file,
                external_url=external_url,
                published=is_published,
                display_order=display_order,
                financial_year=request.POST.get("financial_year", "").strip(),
            )

        # ====================================================
        # CORPORATE GOVERNANCE
        # ====================================================
        elif effective_section == "corporate_governance":
            display_order = get_next_display_order(CorporateGovernance)
            CorporateGovernance.objects.create(
                title=title,
                pdf_file=pdf_file,
                external_url=external_url,
                published=is_published,
                display_order=display_order,
                financial_year=request.POST.get("financial_year", "").strip(),
                quarter=request.POST.get("quarter", "").strip(),
            )

        # ====================================================
        # FINANCIAL RESULT
        # ====================================================
        elif effective_section == "financial_result":
            display_order = get_next_display_order(FinancialResult)
            FinancialResult.objects.create(
                title=title,
                pdf_file=pdf_file,
                external_url=external_url,
                published=is_published,
                display_order=display_order,
                financial_year=request.POST.get("financial_year", "").strip(),
                quarter=request.POST.get("quarter", "").strip(),
                release_date=request.POST.get("release_date") or None,
            )

        # ====================================================
        # SHAREHOLDER NOTICE  (child of Corporate Announcements)
        # ====================================================
        elif effective_section == "shareholder_notice":
            display_order = get_next_display_order(ShareholderNotice)
            ShareholderNotice.objects.create(
                title=title,
                pdf_file=pdf_file,
                external_url=external_url,
                published=is_published,
                display_order=display_order,
                financial_year=request.POST.get("financial_year", "").strip(),
                notice_type=request.POST.get("notice_type", "").strip(),
                disclosure_date=request.POST.get("disclosure_date") or None,
                meeting_date=request.POST.get("meeting_date") or None,
            )

        # ====================================================
        # NEWSPAPER PUBLICATION  (child of Corporate Announcements)
        # ====================================================
        elif effective_section == "newspaper_publication":
            display_order = get_next_display_order(NewspaperPublication)
            NewspaperPublication.objects.create(
                title=title,
                pdf_file=pdf_file,
                external_url=external_url,
                published=is_published,
                display_order=display_order,
                financial_year=request.POST.get("financial_year", "").strip(),
                disclosure_date=request.POST.get("disclosure_date") or None,
            )

        # ====================================================
        # STOCK EXCHANGE DISCLOSURE  (child of Corporate Announcements)
        # ====================================================
        elif effective_section == "stock_exchange_disclosure":
            display_order = get_next_display_order(StockExchangeDisclosure)
            StockExchangeDisclosure.objects.create(
                title=title,
                pdf_file=pdf_file,
                external_url=external_url,
                published=is_published,
                display_order=display_order,
                financial_year=request.POST.get("financial_year", "").strip(),
                disclosure_date=request.POST.get("disclosure_date") or None,
            )

        # ====================================================
        # SHAREHOLDING PATTERN
        # ====================================================
        elif effective_section == "shareholding_pattern":
            display_order = get_next_display_order(ShareholdingPattern)
            ShareholdingPattern.objects.create(
                title=title,
                pdf_file=pdf_file,
                external_url=external_url,
                published=is_published,
                display_order=display_order,
                financial_year=request.POST.get("financial_year", "").strip(),
                quarter=request.POST.get("quarter", "").strip(),
            )

        # ====================================================
        # SEBI DOCUMENT
        # ====================================================
        elif effective_section == "sebi_document":
            display_order = get_next_display_order(SEBIDocument)
            SEBIDocument.objects.create(
                title=title,
                pdf_file=pdf_file,
                external_url=external_url,
                published=is_published,
                display_order=display_order,
                category=request.POST.get("category", "").strip(),
            )

        # ====================================================
        # INVESTOR FORMS & DECLARATION
        # ====================================================
        elif effective_section == "investor_form":

            category = (
                request.POST.get("category", "").strip()
                or subsection
                or ""
            )

            # ------------------------------------------------
            # KYC & NOMINATION
            # Stored in InvestorForm
            # ------------------------------------------------
            if category == "kyc_nomination":

                display_order = get_next_display_order(
                    InvestorForm
                )

                InvestorForm.objects.create(
                    title=title,
                    pdf_file=pdf_file,
                    external_url=external_url,
                    published=is_published,
                    display_order=display_order,
                    category="kyc_nomination",
                    description=request.POST.get(
                        "description",
                        ""
                    ).strip(),
                )

            # ------------------------------------------------
            # TAX DECLARATION
            # Stored in TaxDeclaration
            # ------------------------------------------------
            elif category == "tax_declaration":

                display_order = get_next_display_order(
                    TaxDeclaration
                )

                TaxDeclaration.objects.create(
                    title=title,
                    pdf_file=pdf_file,
                    external_url=external_url,
                    published=is_published,
                    display_order=display_order,
                    applicable_to=request.POST.get(
                        "applicable_to",
                        ""
                    ).strip(),
                    description=request.POST.get(
                        "description",
                        ""
                    ).strip(),
                )

            # ------------------------------------------------
            # UNCLAIMED DIVIDEND
            # Stored in UnclaimedDividend
            # ------------------------------------------------
            elif category == "unclaimed_dividend":

                display_order = get_next_display_order(
                    UnclaimedDividend
                )

                UnclaimedDividend.objects.create(
                    title=title,
                    pdf_file=pdf_file,
                    external_url=external_url,
                    published=is_published,
                    display_order=display_order,
                    financial_year=request.POST.get(
                        "financial_year",
                        ""
                    ).strip(),
                    dividend_declaration_date=(
                        request.POST.get(
                            "dividend_declaration_date"
                        ) or None
                    ),
                    dividend_type=request.POST.get(
                        "dividend_type",
                        ""
                    ).strip(),
                    iepf_transfer_due_date=(
                        request.POST.get(
                            "iepf_transfer_due_date"
                        ) or None
                    ),
                )

            else:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Invalid Investor Forms category."
                    },
                    status=400
                )

        # ====================================================
        # TAX DECLARATION
        # Direct section support
        # ====================================================
        elif effective_section == "tax_declaration":

            display_order = get_next_display_order(
                TaxDeclaration
            )

            TaxDeclaration.objects.create(
                title=title,
                pdf_file=pdf_file,
                external_url=external_url,
                published=is_published,
                display_order=display_order,
                applicable_to=request.POST.get(
                    "applicable_to",
                    ""
                ).strip(),
                description=request.POST.get(
                    "description",
                    ""
                ).strip(),
            )

        # ====================================================
        # UNCLAIMED DIVIDEND
        # Direct section support
        # ====================================================
        elif effective_section == "unclaimed_dividend":

            display_order = get_next_display_order(
                UnclaimedDividend
            )

            UnclaimedDividend.objects.create(
                title=title,
                pdf_file=pdf_file,
                external_url=external_url,
                published=is_published,
                display_order=display_order,
                financial_year=request.POST.get(
                    "financial_year",
                    ""
                ).strip(),
                dividend_declaration_date=(
                    request.POST.get(
                        "dividend_declaration_date"
                    ) or None
                ),
                dividend_type=request.POST.get(
                    "dividend_type",
                    ""
                ).strip(),
                iepf_transfer_due_date=(
                    request.POST.get(
                        "iepf_transfer_due_date"
                    ) or None
                ),
            )

        # ====================================================
        # SUBSIDIARY FINANCIAL
        # ====================================================
        elif effective_section == "subsidiary_financial":
            display_order = get_next_display_order(SubsidiaryFinancial)
            SubsidiaryFinancial.objects.create(
                title=title,
                pdf_file=pdf_file,
                external_url=external_url,
                published=is_published,
                display_order=display_order,
                financial_year=request.POST.get("financial_year", "").strip(),
                company_name=request.POST.get("company_name", "").strip(),
                financial_type=request.POST.get("financial_type", "").strip(),
            )

        else:
            return JsonResponse(
                {"success": False, "message": f"Invalid section selected: {section}"},
                status=400
            )

        log_audit(
            request,
            title=title,
            section=effective_section,
            action="uploaded",
            document_id=None,
            details="New document uploaded",
        )

        return JsonResponse(
            {"success": True, "message": "Document uploaded successfully."}
        )

    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Upload failed: {str(e)}"},
            status=500
        )


# ============================================================
# DASHBOARD LOGIN
# ============================================================

@never_cache
def dashboard_login(request):
    """
    Login for Admin & Employee only.
    Client role is redirected to the public website.
    """
    # Already logged in → go to correct place
    if request.user.is_authenticated:
        return redirect_based_on_role(request.user)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        remember_me = request.POST.get("remember_me")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Create profile if missing
            if not hasattr(user, 'profile'):
                Profile.objects.create(user=user, role='EMPLOYEE')

            # CLIENT should not enter the dashboard
            if user.profile.role == 'CLIENT':
                login(request, user)
                return redirect('https://www.nibelimited.com')

            # Admin or Employee
            login(request, user)

            if remember_me:
                request.session.set_expiry(60 * 60 * 24 * 30)  # 30 days
                request.session["remembered_username"] = username
            else:
                request.session.set_expiry(0)
                request.session.pop("remembered_username", None)

            return redirect_based_on_role(user)

        # Wrong credentials
        return render(request, "Investor_Login.html", {
            "error": "Invalid Employee ID or Password.",
            "remembered_username": username,
        })

    # GET request
    remembered_username = request.session.get("remembered_username", "")
    return render(request, "Investor_Login.html", {
        "remembered_username": remembered_username,
    })


def redirect_based_on_role(user):
    """
    After login, send user to the correct place according to role.
    ADMIN / EMPLOYEE → Dashboard
    CLIENT           → Public website
    """
    if not hasattr(user, 'profile'):
        Profile.objects.create(user=user, role='EMPLOYEE')

    role = user.profile.role

    if role in ['ADMIN', 'EMPLOYEE']:
        return redirect('upload_dashboard')

    # CLIENT (or any other role)
    return redirect('https://www.nibelimited.com')

# ============================================================
# DELETE INVESTOR DOCUMENT
# ============================================================

@login_required(login_url="dashboard_login")
@role_required(['ADMIN', 'EMPLOYEE'])
def delete_investor_document(request):

    if request.method != "POST":
        return JsonResponse(
            {"success": False, "message": "Invalid method"},
            status=405
        )

    try:
        import json
        body = json.loads(request.body)

        document_id = body.get("document_id")
        section = (body.get("section") or "").strip()

        if not document_id or not section:
            return JsonResponse(
                {"success": False, "message": "document_id and section are required."},
                status=400
            )

        try:
            document_id = int(document_id)
        except (TypeError, ValueError):
            return JsonResponse(
                {"success": False, "message": "Invalid document_id."},
                status=400
            )

        model_map = {
            "annual_report": AnnualReport,
            "financial_result": FinancialResult,
            "annual_return": AnnualReturn,
            "corporate_governance": CorporateGovernance,
            "shareholding_pattern": ShareholdingPattern,
            "shareholder_notice": ShareholderNotice,
            "newspaper_publication": NewspaperPublication,
            "stock_exchange_disclosure": StockExchangeDisclosure,
            "sebi_document": SEBIDocument,
            "investor_form": InvestorForm,
            "tax_declaration": TaxDeclaration,
            "unclaimed_dividend": UnclaimedDividend,
            "subsidiary_financial": SubsidiaryFinancial,
        }

        model = model_map.get(section)

        if not model:
            return JsonResponse(
                {"success": False, "message": f"Invalid section: {section}"},
                status=400
            )

        try:
            obj = model.objects.get(id=document_id)
        except model.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "message": f"Document not found (id={document_id}, section={section})."
                },
                status=404
            )

        # Capture title before deleting
        doc_title = getattr(obj, "title", "Untitled")

        log_audit(
            request,
            title=doc_title,
            section=section,
            action="deleted",
            document_id=document_id,
            details="Document deleted",
        )

        obj.delete()

        return JsonResponse(
            {"success": True, "message": "Document deleted successfully."}
        )

    except Exception as e:
        return JsonResponse(
            {"success": False, "message": str(e)},
            status=500
        )
 # ============================================================
# SUMMARY REPORT DOWNLOAD
# ============================================================

# ============================================================
# SUMMARY REPORT DOWNLOAD (PDF)
# ============================================================

@login_required(login_url="dashboard_login")
@role_required(['ADMIN', 'EMPLOYEE'])
def download_summary_report(request):
    """
    Generate and download a professional PDF Summary Report
    of all investor documents.
    """
    try:
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import (
                SimpleDocTemplate, Table, TableStyle,
                Paragraph, Spacer, HRFlowable
            )
            from reportlab.lib.enums import TA_CENTER
        except ImportError:
            return JsonResponse(
                {
                    "success": False,
                    "message": "The 'reportlab' package is not installed in this "
                                "Python environment. Activate your venv and run: "
                                "pip install reportlab"
                },
                status=500
            )

        from datetime import datetime
        import io

        sections = [
            ("Annual Reports", AnnualReport),
            ("Financial Results", FinancialResult),
            ("Annual Returns", AnnualReturn),
            ("Corporate Governance", CorporateGovernance),
            ("Shareholding Pattern", ShareholdingPattern),
            ("Shareholder Notices", ShareholderNotice),
            ("Newspaper Publications", NewspaperPublication),
            ("Stock Exchange Disclosures", StockExchangeDisclosure),
            ("SEBI Documents", SEBIDocument),
            ("Investor Forms", InvestorForm),
            ("Tax Declarations", TaxDeclaration),
            ("Unclaimed Dividends", UnclaimedDividend),
            ("Subsidiary Financials", SubsidiaryFinancial),
        ]

        data_rows = []
        total_all = published_all = unpublished_all = 0

        for name, model in sections:
            total = model.objects.count()
            published = model.objects.filter(published=True).count()
            unpublished = total - published
            data_rows.append([name, str(total), str(published), str(unpublished)])
            total_all += total
            published_all += published
            unpublished_all += unpublished

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Heading1"],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=6,
            textColor=colors.HexColor("#0f172a")
        )

        subtitle_style = ParagraphStyle(
            "SubtitleStyle",
            parent=styles["Normal"],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=16
        )

        note_style = ParagraphStyle(
            "NoteStyle",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#475569"),
            spaceBefore=12
        )

        elements = []

        elements.append(Paragraph("NIBE Limited", title_style))
        elements.append(Paragraph("Investor Relations - Summary Report", title_style))
        elements.append(Paragraph(
            f"Generated on: {datetime.now().strftime('%d %B %Y, %H:%M')}",
            subtitle_style
        ))
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor("#cbd5e1"),
            spaceAfter=16
        ))

        table_data = [
            ["Section", "Total", "Published", "Unpublished"]
        ] + data_rows + [
            ["TOTAL", str(total_all), str(published_all), str(unpublished_all)]
        ]

        table = Table(table_data, colWidths=[260, 70, 80, 90])

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("ALIGN", (1, 0), (-1, 0), "CENTER"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("TOPPADDING", (0, 0), (-1, 0), 10),
            ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 1), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8fafc")]),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e0f2fe")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, -1), (-1, -1), colors.HexColor("#0c4a6e")),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 16))
        elements.append(Paragraph(
            "<b>Note:</b> Only documents marked as <b>Published</b> are visible on the public Investor Relations page.",
            note_style
        ))
        elements.append(Paragraph(
            "This report was generated from the NIBE Investor CMS Dashboard.",
            note_style
        ))

        doc.build(elements)
        buffer.seek(0)

        filename = f"NIBE_Investor_Summary_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        import traceback
        traceback.print_exc()  # prints the full error to your runserver terminal
        return JsonResponse(
            {"success": False, "message": f"Failed to generate PDF: {str(e)}"},
            status=500
        )

# ============================================================
# EMPLOYEE MANAGEMENT  (Only ADMIN can access)
# ============================================================


@login_required(login_url="dashboard_login")
@role_required(['ADMIN'])
def employees_list_api(request):
    """Only Admin can see the list of employees."""
    users = User.objects.all().order_by("-date_joined")

    data = []
    for user in users:
        role = user.profile.role if hasattr(user, 'profile') else 'EMPLOYEE'

        data.append({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "is_active": user.is_active,
            "is_staff": user.is_staff,
            "role": role,
            "date_joined": user.date_joined.strftime("%d-%m-%Y"),
            "last_login": user.last_login.strftime("%d-%m-%Y %H:%M") if user.last_login else "Never",
        })

    return JsonResponse(data, safe=False)


@login_required(login_url="dashboard_login")
@role_required(['ADMIN'])
def create_employee(request):
    """Only Admin can create new users."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=405)

    try:
        body = json.loads(request.body)

        username   = body.get("username", "").strip()
        password   = body.get("password", "").strip()
        first_name = body.get("first_name", "").strip()
        last_name  = body.get("last_name", "").strip()
        email      = body.get("email", "").strip()
        is_active  = body.get("is_active", True)
        role       = body.get("role", "EMPLOYEE").strip().upper()

        if role not in ['ADMIN', 'EMPLOYEE', 'CLIENT']:
            role = 'EMPLOYEE'

        if not username:
            return JsonResponse({"success": False, "message": "Employee ID is required."}, status=400)
        if not password:
            return JsonResponse({"success": False, "message": "Password is required."}, status=400)
        if len(password) < 6:
            return JsonResponse({"success": False, "message": "Password must be at least 6 characters."}, status=400)
        if User.objects.filter(username=username).exists():
            return JsonResponse({"success": False, "message": "Employee ID already exists."}, status=400)

        user = User.objects.create(
            username=username,
            password=make_password(password),
            first_name=first_name,
            last_name=last_name,
            email=email,
            is_active=is_active,
            is_staff=True,
        )

        # Set role
        user.profile.role = role
        user.profile.save()

        return JsonResponse({
            "success": True,
            "message": f"User '{username}' created as {role}.",
            "id": user.id
        })

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@login_required(login_url="dashboard_login")
@role_required(['ADMIN'])
def update_employee(request):
    """Only Admin can update users."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=405)

    try:
        body = json.loads(request.body)

        user_id    = body.get("id")
        first_name = body.get("first_name", "").strip()
        last_name  = body.get("last_name", "").strip()
        email      = body.get("email", "").strip()
        is_active  = body.get("is_active", True)
        password   = body.get("password", "").strip()
        role       = body.get("role", "").strip().upper()

        if not user_id:
            return JsonResponse({"success": False, "message": "User ID is required."}, status=400)

        user = User.objects.get(id=user_id)

        if user.id == request.user.id and not is_active:
            return JsonResponse({"success": False, "message": "You cannot deactivate your own account."}, status=400)

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.is_active = is_active

        if password:
            if len(password) < 6:
                return JsonResponse({"success": False, "message": "Password must be at least 6 characters."}, status=400)
            user.password = make_password(password)

        user.save()

        if role in ['ADMIN', 'EMPLOYEE', 'CLIENT']:
            user.profile.role = role
            user.profile.save()

        return JsonResponse({"success": True, "message": "User updated successfully."})

    except User.DoesNotExist:
        return JsonResponse({"success": False, "message": "User not found."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@login_required(login_url="dashboard_login")
@role_required(['ADMIN'])
def toggle_employee_status(request):
    """Only Admin can activate/deactivate users."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=405)

    try:
        body = json.loads(request.body)
        user_id = body.get("id")

        user = User.objects.get(id=user_id)

        if user.id == request.user.id:
            return JsonResponse({"success": False, "message": "You cannot change your own status."}, status=400)

        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])

        status = "activated" if user.is_active else "deactivated"
        return JsonResponse({
            "success": True,
            "is_active": user.is_active,
            "message": f"User has been {status}."
        })

    except User.DoesNotExist:
        return JsonResponse({"success": False, "message": "User not found."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@login_required(login_url="dashboard_login")
@role_required(['ADMIN'])
def delete_employee(request):
    """Only Admin can delete users."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=405)

    try:
        body = json.loads(request.body)
        user_id = body.get("id")

        user = User.objects.get(id=user_id)

        if user.id == request.user.id:
            return JsonResponse({"success": False, "message": "You cannot delete your own account."}, status=400)

        username = user.username
        user.delete()

        return JsonResponse({
            "success": True,
            "message": f"User '{username}' deleted successfully."
        })

    except User.DoesNotExist:
        return JsonResponse({"success": False, "message": "User not found."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@login_required(login_url="dashboard_login")
@role_required(['ADMIN'])
def audit_log_api(request):
    """Only Admin can see audit logs."""
    # ... keep your existing code inside this function ...
    """Return paginated audit logs."""
    try:
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 10))
    except (TypeError, ValueError):
        page = 1
        page_size = 10

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 10
    if page_size > 50:
        page_size = 50

    qs = AuditLog.objects.all().order_by("-created_at")
    total = qs.count()
    total_pages = max(1, (total + page_size - 1) // page_size)

    if page > total_pages:
        page = total_pages

    start = (page - 1) * page_size
    end = start + page_size
    logs = qs[start:end]

    data = []
    for log in logs:
        data.append({
            "id": log.id,
            "document_title": log.document_title,
            "section": log.section,
            "action": normalize_audit_action(log.action),
            "details": log.details or "",
            "performed_by": log.performed_by,
            "created_at": log.created_at.strftime("%d-%m-%Y %H:%M"),
        })

    return JsonResponse({
        "results": data,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
    })
     
# ============================================================
# SECTION MANAGEMENT (Admin only)
# A) Create new custom sections
# B) Manage name / order / show-hide for all sections
# C) Sub-sections under any section
# ============================================================

# Built-in sections that map to existing document models
SYSTEM_SECTIONS_SEED = [
    {"name": "Annual Reports", "slug": "annual-reports", "model_key": "annual_report", "icon": "📊", "display_order": 1},
    {"name": "Financial Results", "slug": "financial-results", "model_key": "financial_result", "icon": "📈", "display_order": 2},
    {"name": "Annual Returns", "slug": "annual-returns", "model_key": "annual_return", "icon": "📋", "display_order": 3},
    {"name": "Corporate Governance", "slug": "corporate-governance", "model_key": "corporate_governance", "icon": "🏛️", "display_order": 4},
    {"name": "Shareholding Pattern", "slug": "shareholding-pattern", "model_key": "shareholding_pattern", "icon": "🥧", "display_order": 5},
    {"name": "Shareholder Notices", "slug": "shareholder-notices", "model_key": "shareholder_notice", "icon": "📢", "display_order": 6},
    {"name": "Newspaper Publications", "slug": "newspaper-publications", "model_key": "newspaper_publication", "icon": "📰", "display_order": 7},
    {"name": "Stock Exchange Disclosures", "slug": "stock-exchange-disclosures", "model_key": "stock_exchange_disclosure", "icon": "📉", "display_order": 8},
    {"name": "SEBI Documents", "slug": "sebi-documents", "model_key": "sebi_document", "icon": "📑", "display_order": 9},
    {"name": "Investor Forms", "slug": "investor-forms", "model_key": "investor_form", "icon": "📝", "display_order": 10},
    {"name": "Tax Declarations", "slug": "tax-declarations", "model_key": "tax_declaration", "icon": "🧾", "display_order": 11},
    {"name": "Unclaimed Dividends", "slug": "unclaimed-dividends", "model_key": "unclaimed_dividend", "icon": "💰", "display_order": 12},
    {"name": "Subsidiary Financials", "slug": "subsidiary-financials", "model_key": "subsidiary_financial", "icon": "🏢", "display_order": 13},
]


def ensure_system_sections():
    """Create system Section rows once if they do not exist yet."""
    for item in SYSTEM_SECTIONS_SEED:
        Section.objects.get_or_create(
            slug=item["slug"],
            defaults={
                "name": item["name"],
                "model_key": item["model_key"],
                "icon": item["icon"],
                "display_order": item["display_order"],
                "is_system": True,
                "is_active": True,
                "show_on_public": True,
                "allow_subsections": True,
            },
        )


def unique_section_slug(base_slug, exclude_id=None):
    slug = slugify(base_slug) or "section"
    candidate = slug
    n = 2
    while True:
        qs = Section.objects.filter(slug=candidate)
        if exclude_id:
            qs = qs.exclude(id=exclude_id)
        if not qs.exists():
            return candidate
        candidate = f"{slug}-{n}"
        n += 1


def unique_subsection_slug(section, base_slug, exclude_id=None):
    slug = slugify(base_slug) or "subsection"
    candidate = slug
    n = 2
    while True:
        qs = SubSection.objects.filter(section=section, slug=candidate)
        if exclude_id:
            qs = qs.exclude(id=exclude_id)
        if not qs.exists():
            return candidate
        candidate = f"{slug}-{n}"
        n += 1


@login_required(login_url="dashboard_login")
@role_required(["ADMIN", "EMPLOYEE"])
def sections_list_api(request):
    """
    List all sections (for upload dropdowns + manage page).
    Query: ?active_only=1  → only active sections
    """
    ensure_system_sections()

    qs = Section.objects.all().prefetch_related("subsections")
    if request.GET.get("active_only") in ("1", "true", "yes"):
        qs = qs.filter(is_active=True)

    data = []
    for s in qs:
        subs = s.subsections.all()
        if request.GET.get("active_only") in ("1", "true", "yes"):
            subs = subs.filter(is_active=True)

        data.append({
            "id": s.id,
            "name": s.name,
            "slug": s.slug,
            "model_key": s.model_key,
            "description": s.description,
            "icon": s.icon or "📁",
            "is_system": s.is_system,
            "is_active": s.is_active,
            "show_on_public": s.show_on_public,
            "allow_subsections": s.allow_subsections,
            "display_order": s.display_order,
            "document_count": (
                s.custom_documents.count()
                if not s.is_system
                else None
            ),
            "subsections": [
                {
                    "id": sub.id,
                    "name": sub.name,
                    "slug": sub.slug,
                    "is_active": sub.is_active,
                    "display_order": sub.display_order,
                }
                for sub in subs
            ],
        })

    return JsonResponse(data, safe=False)


@login_required(login_url="dashboard_login")
@role_required(["ADMIN"])
def create_section(request):
    """Create a new custom section (Option A). Admin only."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=405)

    try:
        body = json.loads(request.body)
        name = (body.get("name") or "").strip()
        description = (body.get("description") or "").strip()
        icon = (body.get("icon") or "📁").strip() or "📁"
        is_active = body.get("is_active", True)
        show_on_public = body.get("show_on_public", True)
        allow_subsections = body.get("allow_subsections", True)
        display_order = body.get("display_order")

        if not name:
            return JsonResponse({"success": False, "message": "Section name is required."}, status=400)

        slug = unique_section_slug(body.get("slug") or name)

        if display_order is None or display_order == "":
            last = Section.objects.aggregate(m=Max("display_order"))["m"]
            display_order = (last or 0) + 1
        else:
            display_order = int(display_order)

        section = Section.objects.create(
            name=name,
            slug=slug,
            model_key="",  # custom → no system model
            description=description,
            icon=icon,
            is_system=False,
            is_active=bool(is_active),
            show_on_public=bool(show_on_public),
            allow_subsections=bool(allow_subsections),
            display_order=display_order,
        )

        return JsonResponse({
            "success": True,
            "message": f"Section '{section.name}' created.",
            "id": section.id,
            "slug": section.slug,
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@login_required(login_url="dashboard_login")
@role_required(["ADMIN"])
def update_section(request):
    """Update section name / order / visibility (Option B). Admin only."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=405)

    try:
        body = json.loads(request.body)
        section_id = body.get("id")
        if not section_id:
            return JsonResponse({"success": False, "message": "Section id is required."}, status=400)

        section = Section.objects.get(id=section_id)

        if "name" in body and (body.get("name") or "").strip():
            section.name = body["name"].strip()

        if "description" in body:
            section.description = (body.get("description") or "").strip()

        if "icon" in body:
            section.icon = (body.get("icon") or "📁").strip() or "📁"

        if "is_active" in body:
            section.is_active = bool(body["is_active"])

        if "show_on_public" in body:
            section.show_on_public = bool(body["show_on_public"])

        if "allow_subsections" in body:
            section.allow_subsections = bool(body["allow_subsections"])

        if "display_order" in body and body["display_order"] is not None and body["display_order"] != "":
            section.display_order = int(body["display_order"])

        # Optional slug change for custom sections only
        if not section.is_system and body.get("slug"):
            section.slug = unique_section_slug(body["slug"], exclude_id=section.id)

        section.save()

        return JsonResponse({
            "success": True,
            "message": f"Section '{section.name}' updated.",
        })
    except Section.DoesNotExist:
        return JsonResponse({"success": False, "message": "Section not found."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@login_required(login_url="dashboard_login")
@role_required(["ADMIN"])
def delete_section(request):
    """Delete a custom section only (system sections cannot be deleted)."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=405)

    try:
        body = json.loads(request.body)
        section_id = body.get("id")
        section = Section.objects.get(id=section_id)

        if section.is_system:
            return JsonResponse({
                "success": False,
                "message": "System sections cannot be deleted. You can hide them instead.",
            }, status=400)

        name = section.name
        # Custom documents cascade-delete with section
        section.delete()

        return JsonResponse({
            "success": True,
            "message": f"Section '{name}' deleted.",
        })
    except Section.DoesNotExist:
        return JsonResponse({"success": False, "message": "Section not found."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@login_required(login_url="dashboard_login")
@role_required(["ADMIN"])
def toggle_section_status(request):
    """Show / hide a section (is_active)."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=405)

    try:
        body = json.loads(request.body)
        section = Section.objects.get(id=body.get("id"))
        section.is_active = not section.is_active
        section.save(update_fields=["is_active"])
        status = "shown" if section.is_active else "hidden"
        return JsonResponse({
            "success": True,
            "is_active": section.is_active,
            "message": f"Section is now {status}.",
        })
    except Section.DoesNotExist:
        return JsonResponse({"success": False, "message": "Section not found."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


# ---------- Sub-sections (Option C) ----------

@login_required(login_url="dashboard_login")
@role_required(["ADMIN"])
def create_subsection(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=405)

    try:
        body = json.loads(request.body)
        section_id = body.get("section_id")
        name = (body.get("name") or "").strip()

        if not section_id or not name:
            return JsonResponse({"success": False, "message": "section_id and name are required."}, status=400)

        section = Section.objects.get(id=section_id)
        if not section.allow_subsections:
            return JsonResponse({"success": False, "message": "This section does not allow sub-sections."}, status=400)

        slug = unique_subsection_slug(section, body.get("slug") or name)
        last = section.subsections.aggregate(m=Max("display_order"))["m"]
        display_order = int(body["display_order"]) if body.get("display_order") not in (None, "") else (last or 0) + 1

        sub = SubSection.objects.create(
            section=section,
            name=name,
            slug=slug,
            is_active=bool(body.get("is_active", True)),
            display_order=display_order,
        )

        return JsonResponse({
            "success": True,
            "message": f"Sub-section '{sub.name}' created.",
            "id": sub.id,
        })
    except Section.DoesNotExist:
        return JsonResponse({"success": False, "message": "Parent section not found."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@login_required(login_url="dashboard_login")
@role_required(["ADMIN"])
def update_subsection(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=405)

    try:
        body = json.loads(request.body)
        sub = SubSection.objects.get(id=body.get("id"))

        if "name" in body and (body.get("name") or "").strip():
            sub.name = body["name"].strip()
        if "is_active" in body:
            sub.is_active = bool(body["is_active"])
        if "display_order" in body and body["display_order"] not in (None, ""):
            sub.display_order = int(body["display_order"])
        if body.get("slug"):
            sub.slug = unique_subsection_slug(sub.section, body["slug"], exclude_id=sub.id)

        sub.save()
        return JsonResponse({"success": True, "message": "Sub-section updated."})
    except SubSection.DoesNotExist:
        return JsonResponse({"success": False, "message": "Sub-section not found."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@login_required(login_url="dashboard_login")
@role_required(["ADMIN"])
def delete_subsection(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=405)

    try:
        body = json.loads(request.body)
        sub = SubSection.objects.get(id=body.get("id"))
        name = sub.name
        sub.delete()
        return JsonResponse({"success": True, "message": f"Sub-section '{name}' deleted."})
    except SubSection.DoesNotExist:
        return JsonResponse({"success": False, "message": "Sub-section not found."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


# ---------- Custom documents under custom sections ----------

@login_required(login_url="dashboard_login")
@role_required(["ADMIN", "EMPLOYEE"])
def custom_documents_api(request):
    """List documents for a custom section (?section_id= or ?slug=)."""
    section_id = request.GET.get("section_id")
    slug = request.GET.get("slug")

    try:
        if section_id:
            section = Section.objects.get(id=section_id, is_system=False)
        elif slug:
            section = Section.objects.get(slug=slug, is_system=False)
        else:
            return JsonResponse({"success": False, "message": "section_id or slug required."}, status=400)
    except Section.DoesNotExist:
        return JsonResponse({"success": False, "message": "Custom section not found."}, status=404)

    docs = CustomDocument.objects.filter(section=section).select_related("subsection")
    if request.GET.get("published_only") in ("1", "true"):
        docs = docs.filter(published=True)

    data = []
    for d in docs:
        data.append({
            "id": d.id,
            "section": section.slug,
            "section_id": section.id,
            "subsection_id": d.subsection_id,
            "subsection_name": d.subsection.name if d.subsection else "",
            "title": d.title,
            "pdf_file": request.build_absolute_uri(d.pdf_file.url) if d.pdf_file else None,
            "external_url": d.external_url,
            "published": d.published,
            "display_order": d.display_order,
            "extra_info": d.extra_info,
            "created_at": d.created_at.strftime("%d-%m-%Y"),
        })

    return JsonResponse(data, safe=False)


@login_required(login_url="dashboard_login")
@role_required(["ADMIN", "EMPLOYEE"])
def upload_custom_document(request):
    """Upload a document into a custom section (PDF / URL / published)."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=405)

    try:
        section_id = request.POST.get("section_id")
        subsection_id = request.POST.get("subsection_id") or None
        title = (request.POST.get("title") or "").strip()
        external_url = (request.POST.get("external_url") or "").strip() or None
        extra_info = (request.POST.get("extra_info") or "").strip()
        published = request.POST.get("published", "true") in ("true", "1", "on", "True")
        pdf_file = request.FILES.get("pdf_file")

        if not section_id or not title:
            return JsonResponse({"success": False, "message": "section_id and title are required."}, status=400)
        if not pdf_file and not external_url:
            return JsonResponse({"success": False, "message": "Provide a PDF file or external URL."}, status=400)

        section = Section.objects.get(id=section_id, is_system=False, is_active=True)

        subsection = None
        if subsection_id:
            subsection = SubSection.objects.get(id=subsection_id, section=section)

        last = CustomDocument.objects.filter(section=section).aggregate(m=Max("display_order"))["m"]
        display_order = (last or 0) + 1

        doc = CustomDocument.objects.create(
            section=section,
            subsection=subsection,
            title=title,
            pdf_file=pdf_file,
            external_url=external_url,
            published=published,
            display_order=display_order,
            extra_info=extra_info,
        )

        log_audit(
            request,
            title=doc.title,
            section=section.slug,
            action="uploaded",
            document_id=doc.id,
            details=f"Custom section document uploaded under {section.name}",
        )

        return JsonResponse({
            "success": True,
            "message": "Document uploaded successfully.",
            "id": doc.id,
        })
    except Section.DoesNotExist:
        return JsonResponse({"success": False, "message": "Custom section not found or inactive."}, status=404)
    except SubSection.DoesNotExist:
        return JsonResponse({"success": False, "message": "Sub-section not found."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@login_required(login_url="dashboard_login")
@role_required(["ADMIN", "EMPLOYEE"])
def delete_custom_document(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=405)

    try:
        body = json.loads(request.body)
        doc = CustomDocument.objects.select_related("section").get(id=body.get("id"))
        title = doc.title
        section_slug = doc.section.slug
        doc_id = doc.id
        doc.delete()

        log_audit(
            request,
            title=title,
            section=section_slug,
            action="deleted",
            document_id=doc_id,
            details="Custom section document deleted",
        )

        return JsonResponse({"success": True, "message": "Document deleted."})
    except CustomDocument.DoesNotExist:
        return JsonResponse({"success": False, "message": "Document not found."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)
