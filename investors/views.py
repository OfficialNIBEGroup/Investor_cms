from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import never_cache
from django.shortcuts import render, redirect
from django.db.models import Max, Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
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
    pdf_upload_user,
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
    "registered": "registered",
    "register": "registered",
    "approved": "approved",
    "approve": "approved",
    "rejected": "rejected",
    "reject": "rejected",
}


# ============================================================
# ROLE BASED ACCESS CONTROL
# ============================================================
# ADMIN    → Full system access
# EMPLOYEE → Only Documents + Upload Document
# CLIENT   → Only public website (www.nibelimited.com)

def role_required(allowed_roles=None):
    if allowed_roles is None:
        allowed_roles = []

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('dashboard_login')

            if not hasattr(request.user, 'profile'):
                Profile.objects.create(user=request.user, role='EMPLOYEE', approval_status='APPROVED')

            profile = request.user.profile
            if not request.user.is_active or profile.approval_status != 'APPROVED':
                logout(request)
                if request.path.startswith('/api/'):
                    return JsonResponse({
                        "success": False,
                        "message": "Your account is not approved or is inactive."
                    }, status=403)

                messages.error(request, "Your account is awaiting Admin approval or is inactive.")
                return redirect('dashboard_login')

            user_role = profile.role
            if user_role not in allowed_roles:
                if request.path.startswith('/api/'):
                    return JsonResponse({
                        "success": False,
                        "message": "You do not have permission to perform this action."
                    }, status=403)

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
    skip = {"id", "created_at", "updated_at", "display_order"}
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


INVESTOR_DOCUMENT_MODELS = {
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


def document_file_links(section, document_id):
    """Return (pdf_url, external_url) for a document that still exists."""
    if not document_id:
        return None, None

    obj = None
    model = INVESTOR_DOCUMENT_MODELS.get(section or "")
    if model:
        obj = model.objects.filter(id=document_id).first()
    elif section and str(section).startswith("custom_"):
        try:
            section_pk = int(str(section).split("_", 1)[1])
        except (TypeError, ValueError):
            section_pk = None
        if section_pk:
            obj = CustomDocument.objects.filter(
                id=document_id,
                section_id=section_pk,
            ).first()
    elif section:
        obj = CustomDocument.objects.filter(
            id=document_id,
            section__slug=section,
        ).first()

    if obj is None:
        return None, None

    pdf = obj.pdf_file.url if getattr(obj, "pdf_file", None) else None
    return pdf, getattr(obj, "external_url", None) or None


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
        "-updated_at", "-created_at", "-id"
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
        "-updated_at", "-created_at", "-id"
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
        "-updated_at", "-created_at", "-id"
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
        "-updated_at", "-created_at", "-id"
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
        "-updated_at", "-created_at", "-id"
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
        "-updated_at", "-created_at", "-id"
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
        "-updated_at", "-created_at", "-id"
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
        "-updated_at", "-created_at", "-id"
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
        "-updated_at", "-created_at", "-id"
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
        "-updated_at", "-created_at", "-id"
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
        "-updated_at", "-created_at", "-id"
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
        "-updated_at", "-created_at", "-id"
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
        "-updated_at", "-created_at", "-id"
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


def _public_date(value):
    if not value:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%d-%m-%Y")
    return str(value)


def _public_file_url(request, obj):
    pdf = getattr(obj, "pdf_file", None)
    if not pdf:
        return None
    try:
        return request.build_absolute_uri(pdf.url)
    except Exception:
        return None


def _public_document(request, obj, bucket=""):
    """One published document, shaped for the public Investors page."""
    return {
        "id": obj.id,
        "title": obj.title or "Untitled",
        "financial_year": getattr(obj, "financial_year", "") or "",
        "quarter": getattr(obj, "quarter", "") or "",
        "category": getattr(obj, "category", "") or "",
        "company_name": getattr(obj, "company_name", "") or "",
        "financial_type": getattr(obj, "financial_type", "") or "",
        "notice_type": getattr(obj, "notice_type", "") or "",
        "extra_info": getattr(obj, "extra_info", "") or "",
        "description": getattr(obj, "description", "") or "",
        "applicable_to": getattr(obj, "applicable_to", "") or "",
        "dividend_type": getattr(obj, "dividend_type", "") or "",
        "dividend_declaration_date": _public_date(getattr(obj, "dividend_declaration_date", None)),
        "iepf_transfer_due_date": _public_date(getattr(obj, "iepf_transfer_due_date", None)),
        "release_date": _public_date(getattr(obj, "release_date", None)),
        "disclosure_date": _public_date(getattr(obj, "disclosure_date", None)),
        "meeting_date": _public_date(getattr(obj, "meeting_date", None)),
        "pdf_file": _public_file_url(request, obj),
        "external_url": getattr(obj, "external_url", None) or None,
        "display_order": getattr(obj, "display_order", 0) or 0,
        "bucket": bucket,
    }


def _published(model):
    return model.objects.filter(published=True).order_by("-updated_at", "-created_at", "-id")


@never_cache
def public_investor_documents(request):
    """
    Published investor documents for the public Investors page.
    Sections hidden in the admin panel are left out. Custom sections
    marked visible on the public site are included.
    """
    ensure_system_sections()

    hidden = set()
    names = {}
    for row in Section.objects.filter(is_system=True):
        if not row.model_key:
            continue
        names[row.model_key] = row.name
        if not row.is_active or not row.show_on_public:
            hidden.add(row.model_key)

    def visible(key):
        return key not in hidden

    def named(key, fallback):
        return names.get(key) or fallback

    sections = []

    def add_section(key, name, icon, layout, documents):
        sections.append({
            "key": key,
            "name": name,
            "icon": icon,
            "layout": layout,
            "documents": documents,
        })

    if visible("annual_report"):
        add_section(
            "annual_report",
            named("annual_report", "Annual Reports"),
            "fa-file-lines",
            "year_table",
            [_public_document(request, obj) for obj in _published(AnnualReport)],
        )

    if visible("financial_result"):
        add_section(
            "financial_result",
            named("financial_result", "Financial Results"),
            "fa-chart-line",
            "financial_results",
            [_public_document(request, obj) for obj in _published(FinancialResult)],
        )

    if visible("annual_return"):
        add_section(
            "annual_return",
            named("annual_return", "Annual Returns"),
            "fa-rotate",
            "year_table",
            [_public_document(request, obj) for obj in _published(AnnualReturn)],
        )

    announcement_docs = []
    if visible("shareholder_notice"):
        announcement_docs.extend(
            _public_document(request, obj, "shareholder_notice")
            for obj in _published(ShareholderNotice)
        )
    if visible("newspaper_publication"):
        announcement_docs.extend(
            _public_document(request, obj, "newspaper_publication")
            for obj in _published(NewspaperPublication)
        )
    if visible("stock_exchange_disclosure"):
        announcement_docs.extend(
            _public_document(request, obj, "stock_exchange_disclosure")
            for obj in _published(StockExchangeDisclosure)
        )
    if any(visible(key) for key in (
        "shareholder_notice",
        "newspaper_publication",
        "stock_exchange_disclosure",
    )):
        add_section(
            "corporate_announcements",
            "Corporate Announcements",
            "fa-bullhorn",
            "announcements",
            announcement_docs,
        )

    if visible("corporate_governance"):
        add_section(
            "corporate_governance",
            named("corporate_governance", "Corporate Governance"),
            "fa-landmark",
            "by_year",
            [_public_document(request, obj) for obj in _published(CorporateGovernance)],
        )

    if visible("shareholding_pattern"):
        add_section(
            "shareholding_pattern",
            named("shareholding_pattern", "Shareholding Pattern"),
            "fa-chart-pie",
            "by_year",
            [_public_document(request, obj) for obj in _published(ShareholdingPattern)],
        )

    if visible("sebi_document"):
        add_section(
            "sebi_document",
            named("sebi_document", "Disclosure under Regulation 46 of SEBI LODR"),
            "fa-shield-halved",
            "sebi",
            [_public_document(request, obj) for obj in _published(SEBIDocument)],
        )

    form_docs = []
    if visible("investor_form"):
        form_docs.extend(
            _public_document(request, obj, obj.category or "kyc_nomination")
            for obj in _published(InvestorForm)
        )
    if visible("tax_declaration"):
        form_docs.extend(
            _public_document(request, obj, "tax_declaration")
            for obj in _published(TaxDeclaration)
        )
    if visible("unclaimed_dividend"):
        form_docs.extend(
            _public_document(request, obj, "unclaimed_dividend")
            for obj in _published(UnclaimedDividend)
        )
    if any(visible(key) for key in ("investor_form", "tax_declaration", "unclaimed_dividend")):
        add_section(
            "investor_form",
            named("investor_form", "Investor Forms & Declarations"),
            "fa-file-signature",
            "investor_forms",
            form_docs,
        )

    if visible("subsidiary_financial"):
        add_section(
            "subsidiary_financial",
            named("subsidiary_financial", "Subsidiary Financials"),
            "fa-sitemap",
            "subsidiary",
            [_public_document(request, obj) for obj in _published(SubsidiaryFinancial)],
        )

    custom_sections = Section.objects.filter(
        is_system=False,
        is_active=True,
        show_on_public=True,
    ).order_by("display_order", "name")
    for section in custom_sections:
        docs = CustomDocument.objects.filter(
            section=section,
            published=True,
        ).order_by("-updated_at", "-created_at", "-id")
        add_section(
            f"custom_{section.id}",
            section.name,
            "fa-folder",
            "custom",
            [_public_document(request, obj) for obj in docs],
        )

    return JsonResponse({"sections": sections})


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

    total_documents = sum(section_counts.values())

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


# ============================================================
# EDIT DOCUMENT - GET DOCUMENT DATA
# ============================================================

@login_required(login_url="dashboard_login")
@role_required(['ADMIN', 'EMPLOYEE'])
def edit_investor_document(request, document_id, section):
    """
    GET  – return the document so the edit form can be filled.
    POST – save the submitted changes. The documents page posts here.
    """

    if request.method == "POST":
        mutable = request.POST.copy()
        if not (mutable.get("document_id") or "").strip():
            mutable["document_id"] = str(document_id)
        if not (mutable.get("section") or "").strip():
            mutable["section"] = section
        request.POST = mutable
        return update_investor_document(request)

    if request.method != "GET":
        return JsonResponse(
            {"success": False, "message": "Invalid request method."},
            status=405,
        )

    try:
        if section == "annual_report":
            obj = AnnualReport.objects.get(id=document_id)
            data = {
                "id": obj.id,
                "section": "annual_report",
                "title": obj.title,
                "financial_year": obj.financial_year,
                "external_url": obj.external_url,
                "pdf_file": request.build_absolute_uri(obj.pdf_file.url) if obj.pdf_file else None,
            }

        elif section == "financial_result":
            obj = FinancialResult.objects.get(id=document_id)
            data = {
                "id": obj.id,
                "section": "financial_result",
                "title": obj.title,
                "financial_year": obj.financial_year,
                "quarter": obj.quarter,
                "release_date": obj.release_date.strftime("%Y-%m-%d") if obj.release_date else None,
                "external_url": obj.external_url,
                "pdf_file": request.build_absolute_uri(obj.pdf_file.url) if obj.pdf_file else None,
            }

        elif section == "annual_return":
            obj = AnnualReturn.objects.get(id=document_id)
            data = {
                "id": obj.id,
                "section": "annual_return",
                "title": obj.title,
                "financial_year": obj.financial_year,
                "external_url": obj.external_url,
                "pdf_file": request.build_absolute_uri(obj.pdf_file.url) if obj.pdf_file else None,
            }

        elif section == "corporate_governance":
            obj = CorporateGovernance.objects.get(id=document_id)
            data = {
                "id": obj.id,
                "section": "corporate_governance",
                "title": obj.title,
                "financial_year": obj.financial_year,
                "quarter": obj.quarter,
                "external_url": obj.external_url,
                "pdf_file": request.build_absolute_uri(obj.pdf_file.url) if obj.pdf_file else None,
            }

        elif section == "shareholding_pattern":
            obj = ShareholdingPattern.objects.get(id=document_id)
            data = {
                "id": obj.id,
                "section": "shareholding_pattern",
                "title": obj.title,
                "financial_year": obj.financial_year,
                "quarter": obj.quarter,
                "external_url": obj.external_url,
                "pdf_file": request.build_absolute_uri(obj.pdf_file.url) if obj.pdf_file else None,
            }

        elif section == "shareholder_notice":
            obj = ShareholderNotice.objects.get(id=document_id)
            data = {
                "id": obj.id,
                "section": "shareholder_notice",
                "title": obj.title,
                "financial_year": obj.financial_year,
                "notice_type": obj.notice_type,
                "disclosure_date": obj.disclosure_date.strftime("%Y-%m-%d") if obj.disclosure_date else None,
                "meeting_date": obj.meeting_date.strftime("%Y-%m-%d") if obj.meeting_date else None,
                "external_url": obj.external_url,
                "pdf_file": request.build_absolute_uri(obj.pdf_file.url) if obj.pdf_file else None,
            }

        elif section == "newspaper_publication":
            obj = NewspaperPublication.objects.get(id=document_id)
            data = {
                "id": obj.id,
                "section": "newspaper_publication",
                "title": obj.title,
                "financial_year": obj.financial_year,
                "disclosure_date": obj.disclosure_date.strftime("%Y-%m-%d") if obj.disclosure_date else None,
                "external_url": obj.external_url,
                "pdf_file": request.build_absolute_uri(obj.pdf_file.url) if obj.pdf_file else None,
            }

        elif section == "stock_exchange_disclosure":
            obj = StockExchangeDisclosure.objects.get(id=document_id)
            data = {
                "id": obj.id,
                "section": "stock_exchange_disclosure",
                "title": obj.title,
                "financial_year": obj.financial_year,
                "disclosure_date": obj.disclosure_date.strftime("%Y-%m-%d") if obj.disclosure_date else None,
                "external_url": obj.external_url,
                "pdf_file": request.build_absolute_uri(obj.pdf_file.url) if obj.pdf_file else None,
            }

        elif section == "sebi_document":
            obj = SEBIDocument.objects.get(id=document_id)
            data = {
                "id": obj.id,
                "section": "sebi_document",
                "title": obj.title,
                "category": obj.category,
                "external_url": obj.external_url,
                "pdf_file": request.build_absolute_uri(obj.pdf_file.url) if obj.pdf_file else None,
            }

        elif section == "investor_form":
            obj = InvestorForm.objects.get(id=document_id)
            data = {
                "id": obj.id,
                "section": "investor_form",
                "title": obj.title,
                "category": obj.category,
                "description": obj.description,
                "external_url": obj.external_url,
                "pdf_file": request.build_absolute_uri(obj.pdf_file.url) if obj.pdf_file else None,
            }

        elif section == "tax_declaration":
            obj = TaxDeclaration.objects.get(id=document_id)
            data = {
                "id": obj.id,
                "section": "tax_declaration",
                "title": obj.title,
                "applicable_to": obj.applicable_to,
                "description": obj.description,
                "external_url": obj.external_url,
                "pdf_file": request.build_absolute_uri(obj.pdf_file.url) if obj.pdf_file else None,
            }

        elif section == "unclaimed_dividend":
            obj = UnclaimedDividend.objects.get(id=document_id)
            data = {
                "id": obj.id,
                "section": "unclaimed_dividend",
                "title": obj.title,
                "financial_year": obj.financial_year,
                "dividend_declaration_date": obj.dividend_declaration_date.strftime("%Y-%m-%d") if obj.dividend_declaration_date else None,
                "dividend_type": obj.dividend_type,
                "iepf_transfer_due_date": obj.iepf_transfer_due_date.strftime("%Y-%m-%d") if obj.iepf_transfer_due_date else None,
                "external_url": obj.external_url,
                "pdf_file": request.build_absolute_uri(obj.pdf_file.url) if obj.pdf_file else None,
            }

        elif section == "subsidiary_financial":
            obj = SubsidiaryFinancial.objects.get(id=document_id)
            data = {
                "id": obj.id,
                "section": "subsidiary_financial",
                "title": obj.title,
                "financial_year": obj.financial_year,
                "company_name": obj.company_name,
                "financial_type": obj.financial_type,
                "external_url": obj.external_url,
                "pdf_file": request.build_absolute_uri(obj.pdf_file.url) if obj.pdf_file else None,
            }

        elif str(section).startswith("custom_"):
            try:
                section_pk = int(str(section).split("_", 1)[1])
            except (TypeError, ValueError):
                return JsonResponse(
                    {"success": False, "message": "Invalid document section."},
                    status=400,
                )

            obj = CustomDocument.objects.select_related("section").get(
                id=document_id,
                section_id=section_pk,
            )
            data = {
                "id": obj.id,
                "section": section,
                "title": obj.title,
                "extra_info": obj.extra_info,
                "external_url": obj.external_url,
                "pdf_file": request.build_absolute_uri(obj.pdf_file.url) if obj.pdf_file else None,
            }

        else:
            return JsonResponse(
                {"success": False, "message": "Invalid document section."},
                status=400,
            )

        data["published"] = bool(obj.published)
        return JsonResponse({"success": True, "document": data})

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
        CustomDocument.DoesNotExist,
    ):
        return JsonResponse({"success": False, "message": "Document not found."}, status=404)


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

    if pdf_file is not None and (
        not (getattr(pdf_file, "name", "") or "").strip() or pdf_file.size == 0
    ):
        pdf_file = None

    if pdf_file:
        file_name = pdf_file.name.lower()
        if not file_name.endswith(".pdf"):
            return JsonResponse(
                {"success": False, "message": "Only PDF files are allowed."},
                status=400,
            )
        content_type = (getattr(pdf_file, "content_type", "") or "").split(";")[0].strip().lower()
        allowed_types = {
            "",
            "application/pdf",
            "application/x-pdf",
            "application/octet-stream",
            "binary/octet-stream",
        }
        if content_type not in allowed_types:
            return JsonResponse(
                {"success": False, "message": "Invalid file type. Please upload a valid PDF."},
                status=400,
            )
        if pdf_file.size > 50 * 1024 * 1024:
            return JsonResponse(
                {"success": False, "message": "File size must be less than 50 MB."},
                status=400,
            )

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
        upload_username = (
            request.user.username if request.user.is_authenticated else ""
        )

        def begin_update(model):
            nonlocal old_snapshot
            document = model.objects.get(id=document_id)
            old_snapshot = snapshot_document(document)
            return document

        def update_common(document):
            document.title = title
            document.external_url = external_url
            if pdf_file:
                document.pdf_file = pdf_file

            published_raw = request.POST.get("published")
            if published_raw is not None:
                document.published = str(published_raw).strip().lower() in ("true", "1", "yes", "on")

            with pdf_upload_user(upload_username):
                document.save()

        def set_text(target, field):
            if field in request.POST:
                setattr(target, field, (request.POST.get(field) or "").strip())

        def set_date(target, field):
            if field in request.POST:
                raw = (request.POST.get(field) or "").strip()
                setattr(target, field, raw or None)

        if section == "annual_report":
            obj = begin_update(AnnualReport)
            set_text(obj, "financial_year")
            update_common(obj)

        elif section == "financial_result":
            obj = begin_update(FinancialResult)
            set_text(obj, "financial_year")
            set_text(obj, "quarter")
            set_date(obj, "release_date")
            if not obj.release_date:
                return JsonResponse(
                    {"success": False, "message": "Release date is required."},
                    status=400,
                )
            if not obj.quarter:
                return JsonResponse(
                    {"success": False, "message": "Quarter is required."},
                    status=400,
                )
            update_common(obj)

        elif section == "annual_return":
            obj = begin_update(AnnualReturn)
            set_text(obj, "financial_year")
            update_common(obj)

        elif section == "corporate_governance":
            obj = begin_update(CorporateGovernance)
            set_text(obj, "financial_year")
            set_text(obj, "quarter")
            update_common(obj)

        elif section == "shareholding_pattern":
            obj = begin_update(ShareholdingPattern)
            set_text(obj, "financial_year")
            set_text(obj, "quarter")
            update_common(obj)

        elif section == "shareholder_notice":
            obj = begin_update(ShareholderNotice)
            set_text(obj, "financial_year")
            set_text(obj, "notice_type")
            set_date(obj, "disclosure_date")
            set_date(obj, "meeting_date")
            update_common(obj)

        elif section == "newspaper_publication":
            obj = begin_update(NewspaperPublication)
            set_text(obj, "financial_year")
            set_date(obj, "disclosure_date")
            update_common(obj)

        elif section == "stock_exchange_disclosure":
            obj = begin_update(StockExchangeDisclosure)
            set_text(obj, "financial_year")
            set_date(obj, "disclosure_date")
            update_common(obj)

        elif section == "sebi_document":
            obj = begin_update(SEBIDocument)
            set_text(obj, "category")
            update_common(obj)

        elif section == "investor_form":
            obj = begin_update(InvestorForm)
            set_text(obj, "category")
            set_text(obj, "description")
            update_common(obj)

        elif section == "tax_declaration":
            obj = begin_update(TaxDeclaration)
            set_text(obj, "applicable_to")
            set_text(obj, "description")
            update_common(obj)

        elif section == "unclaimed_dividend":
            obj = begin_update(UnclaimedDividend)
            set_text(obj, "financial_year")
            set_date(obj, "dividend_declaration_date")
            set_text(obj, "dividend_type")
            set_date(obj, "iepf_transfer_due_date")
            update_common(obj)

        elif section == "subsidiary_financial":
            obj = begin_update(SubsidiaryFinancial)
            set_text(obj, "financial_year")
            set_text(obj, "company_name")
            set_text(obj, "financial_type")
            update_common(obj)

        elif str(section).startswith("custom_"):
            try:
                section_pk = int(str(section).split("_", 1)[1])
            except (TypeError, ValueError):
                return JsonResponse(
                    {"success": False, "message": f"Invalid section: {section}"},
                    status=400,
                )
            try:
                obj = CustomDocument.objects.get(id=document_id, section_id=section_pk)
            except CustomDocument.DoesNotExist:
                return JsonResponse(
                    {"success": False, "message": "Document not found."},
                    status=404,
                )
            old_snapshot = snapshot_document(obj)
            set_text(obj, "extra_info")
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

        obj.refresh_from_db()
        saved = {
            "id": obj.id,
            "section": section,
            "title": obj.title,
            "published": bool(obj.published),
            "external_url": obj.external_url,
            "pdf_file": obj.pdf_file.url if obj.pdf_file else None,
            "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        }
        if hasattr(obj, "financial_year"):
            saved["financial_year"] = obj.financial_year
        if hasattr(obj, "extra_info"):
            saved["extra_info"] = obj.extra_info
            saved["financial_year"] = obj.extra_info

        return JsonResponse({
            "success": True,
            "message": "Document updated successfully.",
            "document": saved,
        })

    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Update failed: {str(e)}"},
            status=500
        )


# ============================================================
# DASHBOARD DOCUMENTS API
# ============================================================

@never_cache
@login_required(login_url="dashboard_login")
@role_required(['ADMIN', 'EMPLOYEE'])
def dashboard_documents_api(request):

    documents = []

    for obj in AnnualReport.objects.all().order_by("-updated_at", "-created_at", "-id"):
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

    for obj in FinancialResult.objects.all().order_by("-updated_at", "-created_at", "-id"):
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

    for obj in AnnualReturn.objects.all().order_by("-updated_at", "-created_at", "-id"):
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

    for obj in ShareholderNotice.objects.all().order_by("-updated_at", "-created_at", "-id"):
        documents.append({
            "id": obj.id,
            "section": "shareholder_notice",
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

    for obj in NewspaperPublication.objects.all().order_by("-updated_at", "-created_at", "-id"):
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

    for obj in StockExchangeDisclosure.objects.all().order_by("-updated_at", "-created_at", "-id"):
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

    for obj in CorporateGovernance.objects.all().order_by("-updated_at", "-created_at", "-id"):
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

    for obj in ShareholdingPattern.objects.all().order_by("-updated_at", "-created_at", "-id"):
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

    for obj in SEBIDocument.objects.all().order_by("-updated_at", "-created_at", "-id"):
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

    for obj in InvestorForm.objects.all().order_by("-updated_at", "-created_at", "-id"):
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

    for obj in TaxDeclaration.objects.all().order_by("-updated_at", "-created_at", "-id"):
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

    for obj in UnclaimedDividend.objects.all().order_by("-updated_at", "-created_at", "-id"):
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

    for obj in SubsidiaryFinancial.objects.all().order_by("-updated_at", "-created_at", "-id"):
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

    for obj in CustomDocument.objects.select_related("section", "subsection").all().order_by("-updated_at", "-created_at", "-id"):
        documents.append({
            "id": obj.id,
            "section": f"custom_{obj.section_id}",
            "section_name": obj.section.name if obj.section else "",
            "subsection_name": obj.subsection.name if obj.subsection else "",
            "title": obj.title,
            "extra_info": obj.extra_info,
            "financial_year": obj.extra_info,
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

    if not hasattr(request.user, 'profile'):
        Profile.objects.create(user=request.user, role='EMPLOYEE', approval_status='APPROVED')

    profile = request.user.profile
    if not request.user.is_active or profile.approval_status != 'APPROVED':
        logout(request)
        messages.error(request, "Your account is awaiting Admin approval or is inactive.")
        return redirect("dashboard_login")

    role = profile.role

    if role == 'CLIENT':
        return redirect('https://www.nibelimited.com')

    full_name = request.user.get_full_name().strip()
    display_name = full_name if full_name else request.user.username
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

        max_size = 50 * 1024 * 1024
        if pdf_file.size > max_size:
            return JsonResponse(
                {"success": False, "message": "File size must be less than 50 MB."},
                status=400
            )

    effective_section = section

    if section == "corporate_announcements":
        if subsection in ("shareholder_notice", "newspaper_publication", "stock_exchange_disclosure"):
            effective_section = subsection
        else:
            return JsonResponse(
                {"success": False, "message": "Please select a Corporate Announcements subsection."},
                status=400
            )

    try:
        with pdf_upload_user(
            request.user.username if request.user.is_authenticated else ""
        ):
            created = _create_investor_document(
                request,
                effective_section=effective_section,
                subsection=subsection,
                title=title,
                pdf_file=pdf_file,
                external_url=external_url,
                is_published=is_published,
            )
            if created is False:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Invalid Investor Forms category."
                    },
                    status=400
                )
            if created is None:
                return JsonResponse(
                    {"success": False, "message": f"Invalid section selected: {section}"},
                    status=400
                )

        log_audit(
            request,
            title=title,
            section=effective_section,
            action="uploaded",
            document_id=getattr(created, "id", None),
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


def _create_investor_document(
    request,
    *,
    effective_section,
    subsection,
    title,
    pdf_file,
    external_url,
    is_published,
):
    """Create the section-specific document row. Returns the object, False, or None."""

    if effective_section == "annual_report":
        return AnnualReport.objects.create(
            title=title,
            pdf_file=pdf_file,
            external_url=external_url,
            published=is_published,
            display_order=get_next_display_order(AnnualReport),
            financial_year=request.POST.get("financial_year", "").strip(),
        )

    if effective_section == "annual_return":
        return AnnualReturn.objects.create(
            title=title,
            pdf_file=pdf_file,
            external_url=external_url,
            published=is_published,
            display_order=get_next_display_order(AnnualReturn),
            financial_year=request.POST.get("financial_year", "").strip(),
        )

    if effective_section == "corporate_governance":
        return CorporateGovernance.objects.create(
            title=title,
            pdf_file=pdf_file,
            external_url=external_url,
            published=is_published,
            display_order=get_next_display_order(CorporateGovernance),
            financial_year=request.POST.get("financial_year", "").strip(),
            quarter=request.POST.get("quarter", "").strip(),
        )

    if effective_section == "financial_result":
        return FinancialResult.objects.create(
            title=title,
            pdf_file=pdf_file,
            external_url=external_url,
            published=is_published,
            display_order=get_next_display_order(FinancialResult),
            financial_year=request.POST.get("financial_year", "").strip(),
            quarter=request.POST.get("quarter", "").strip(),
            release_date=request.POST.get("release_date") or None,
        )

    if effective_section == "shareholder_notice":
        return ShareholderNotice.objects.create(
            title=title,
            pdf_file=pdf_file,
            external_url=external_url,
            published=is_published,
            display_order=get_next_display_order(ShareholderNotice),
            financial_year=request.POST.get("financial_year", "").strip(),
            notice_type=request.POST.get("notice_type", "").strip(),
            disclosure_date=request.POST.get("disclosure_date") or None,
            meeting_date=request.POST.get("meeting_date") or None,
        )

    if effective_section == "newspaper_publication":
        return NewspaperPublication.objects.create(
            title=title,
            pdf_file=pdf_file,
            external_url=external_url,
            published=is_published,
            display_order=get_next_display_order(NewspaperPublication),
            financial_year=request.POST.get("financial_year", "").strip(),
            disclosure_date=request.POST.get("disclosure_date") or None,
        )

    if effective_section == "stock_exchange_disclosure":
        return StockExchangeDisclosure.objects.create(
            title=title,
            pdf_file=pdf_file,
            external_url=external_url,
            published=is_published,
            display_order=get_next_display_order(StockExchangeDisclosure),
            financial_year=request.POST.get("financial_year", "").strip(),
            disclosure_date=request.POST.get("disclosure_date") or None,
        )

    if effective_section == "shareholding_pattern":
        return ShareholdingPattern.objects.create(
            title=title,
            pdf_file=pdf_file,
            external_url=external_url,
            published=is_published,
            display_order=get_next_display_order(ShareholdingPattern),
            financial_year=request.POST.get("financial_year", "").strip(),
            quarter=request.POST.get("quarter", "").strip(),
        )

    if effective_section == "sebi_document":
        return SEBIDocument.objects.create(
            title=title,
            pdf_file=pdf_file,
            external_url=external_url,
            published=is_published,
            display_order=get_next_display_order(SEBIDocument),
            category=request.POST.get("category", "").strip(),
        )

    if effective_section == "investor_form":
        category = (
            request.POST.get("category", "").strip()
            or subsection
            or ""
        )

        if category == "kyc_nomination":
            return InvestorForm.objects.create(
                title=title,
                pdf_file=pdf_file,
                external_url=external_url,
                published=is_published,
                display_order=get_next_display_order(InvestorForm),
                category="kyc_nomination",
                description=request.POST.get("description", "").strip(),
            )

        if category == "tax_declaration":
            return TaxDeclaration.objects.create(
                title=title,
                pdf_file=pdf_file,
                external_url=external_url,
                published=is_published,
                display_order=get_next_display_order(TaxDeclaration),
                applicable_to=request.POST.get("applicable_to", "").strip(),
                description=request.POST.get("description", "").strip(),
            )

        if category == "unclaimed_dividend":
            return UnclaimedDividend.objects.create(
                title=title,
                pdf_file=pdf_file,
                external_url=external_url,
                published=is_published,
                display_order=get_next_display_order(UnclaimedDividend),
                financial_year=request.POST.get("financial_year", "").strip(),
                dividend_declaration_date=(
                    request.POST.get("dividend_declaration_date") or None
                ),
                dividend_type=request.POST.get("dividend_type", "").strip(),
                iepf_transfer_due_date=(
                    request.POST.get("iepf_transfer_due_date") or None
                ),
            )

        return False

    if effective_section == "tax_declaration":
        return TaxDeclaration.objects.create(
            title=title,
            pdf_file=pdf_file,
            external_url=external_url,
            published=is_published,
            display_order=get_next_display_order(TaxDeclaration),
            applicable_to=request.POST.get("applicable_to", "").strip(),
            description=request.POST.get("description", "").strip(),
        )

    if effective_section == "unclaimed_dividend":
        return UnclaimedDividend.objects.create(
            title=title,
            pdf_file=pdf_file,
            external_url=external_url,
            published=is_published,
            display_order=get_next_display_order(UnclaimedDividend),
            financial_year=request.POST.get("financial_year", "").strip(),
            dividend_declaration_date=(
                request.POST.get("dividend_declaration_date") or None
            ),
            dividend_type=request.POST.get("dividend_type", "").strip(),
            iepf_transfer_due_date=(
                request.POST.get("iepf_transfer_due_date") or None
            ),
        )

    if effective_section == "subsidiary_financial":
        return SubsidiaryFinancial.objects.create(
            title=title,
            pdf_file=pdf_file,
            external_url=external_url,
            published=is_published,
            display_order=get_next_display_order(SubsidiaryFinancial),
            financial_year=request.POST.get("financial_year", "").strip(),
            company_name=request.POST.get("company_name", "").strip(),
            financial_type=request.POST.get("financial_type", "").strip(),
        )

    return None


# ============================================================
# DASHBOARD LOGIN & REGISTRATION
# ============================================================

@never_cache
def dashboard_login(request):
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if not request.user.is_active or (profile and profile.approval_status != 'APPROVED'):
            logout(request)
        else:
            return redirect_based_on_role(request.user)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        remember_me = request.POST.get("remember_me")

        existing_user = User.objects.filter(
            Q(username__iexact=username) | Q(profile__employee_id__iexact=username)
        ).first()

        if existing_user and existing_user.check_password(password):
            profile = getattr(existing_user, 'profile', None)
            if profile is None:
                profile = Profile.objects.create(user=existing_user, role='EMPLOYEE', approval_status='APPROVED')

            if profile.approval_status == 'PENDING':
                return render(request, "Investor_Login.html", {
                    "error": "Your registration request is pending Admin approval. You will be able to log in once approved.",
                    "remembered_username": username,
                })

            if profile.approval_status == 'REJECTED':
                return render(request, "Investor_Login.html", {
                    "error": "Your account registration request was rejected. Please contact the administrator.",
                    "remembered_username": username,
                })

            if not existing_user.is_active:
                return render(request, "Investor_Login.html", {
                    "error": "Your account is currently inactive. Please contact the administrator.",
                    "remembered_username": username,
                })

        user = authenticate(request, username=username, password=password)
        if user is None and existing_user and existing_user.is_active and existing_user.check_password(password):
            user = authenticate(request, username=existing_user.username, password=password)

        if user is not None:
            if not hasattr(user, 'profile'):
                Profile.objects.create(user=user, role='EMPLOYEE', approval_status='APPROVED')

            if user.profile.role == 'CLIENT':
                login(request, user)
                return redirect('https://www.nibelimited.com')

            login(request, user)

            if remember_me:
                request.session.set_expiry(60 * 60 * 24 * 30)
                request.session["remembered_username"] = username
            else:
                request.session.set_expiry(0)
                request.session.pop("remembered_username", None)

            return redirect_based_on_role(user)

        return render(request, "Investor_Login.html", {
            "error": "Invalid Employee ID or Password.",
            "remembered_username": username,
        })

    remembered_username = request.session.get("remembered_username", "")
    return render(request, "Investor_Login.html", {
        "remembered_username": remembered_username,
    })


@never_cache
def dashboard_register(request):
    if request.user.is_authenticated:
        return redirect_based_on_role(request.user)

    form_data = {
        "username": "",
        "first_name": "",
        "last_name": "",
        "email": "",
    }

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        first_name = (request.POST.get("first_name") or "").strip()
        last_name = (request.POST.get("last_name") or "").strip()
        email = (request.POST.get("email") or "").strip()
        password = request.POST.get("password") or ""

        form_data = {
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
        }

        errors = []
        if not username:
            errors.append("Employee ID is required.")
        if not password:
            errors.append("Password is required.")
        elif len(password) < 6:
            errors.append("Password must be at least 6 characters.")

        if username and (
            User.objects.filter(username__iexact=username).exists()
            or Profile.objects.filter(employee_id__iexact=username).exists()
        ):
            errors.append("An account with this Employee ID already exists.")

        if email and User.objects.filter(email__iexact=email).exists():
            errors.append("An account with this Email already exists.")

        candidate_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )

        if password and not errors:
            try:
                validate_password(password, user=candidate_user)
            except DjangoValidationError as exc:
                errors.extend(exc.messages)

        if not errors:
            candidate_user.set_password(password)
            candidate_user.is_active = False
            candidate_user.is_staff = True
            candidate_user.save()

            profile = candidate_user.profile
            profile.employee_id = username
            profile.role = 'EMPLOYEE'
            profile.approval_status = 'PENDING'
            profile.save()

            full_name = f"{first_name} {last_name}".strip() or username
            AuditLog.objects.create(
                document_title=f"{full_name} ({username})",
                section="user_registration",
                action="registered",
                details=f"New employee account registered (Employee ID: {username}, Email: {email or '—'}, Status: Pending Approval)",
                performed_by=candidate_user.username,
                document_id=candidate_user.id,
            )

            return render(request, "Investor_Register.html", {
                "submitted_success": True,
                "success_message": "Your registration request has been submitted successfully and is awaiting Admin approval.",
                "form_data": {},
            })

        return render(request, "Investor_Register.html", {
            "errors": errors,
            "form_data": form_data,
        })

    return render(request, "Investor_Register.html", {"form_data": form_data})

def redirect_based_on_role(user):
    if not hasattr(user, 'profile'):
        Profile.objects.create(user=user, role='EMPLOYEE', approval_status='APPROVED')

    role = user.profile.role

    if role in ['ADMIN', 'EMPLOYEE']:
        return redirect('documents')

    return redirect('https://www.nibelimited.com')


# ============================================================
# DELETE INVESTOR DOCUMENT
# ============================================================

@login_required(login_url="dashboard_login")
@role_required(['ADMIN', 'EMPLOYEE'])
def delete_investor_document(request, document_id=None, section=None):

    if request.method != "POST":
        return JsonResponse(
            {"success": False, "message": "Invalid method"},
            status=405
        )

    try:
        content_type = request.content_type or ""
        if "application/json" in content_type:
            try:
                body = json.loads(request.body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                return JsonResponse(
                    {"success": False, "message": "Invalid JSON body."},
                    status=400,
                )
        else:
            body = request.POST

        if hasattr(body, "get"):
            if document_id in (None, ""):
                document_id = body.get("document_id") or body.get("id")
            if not (section or "").strip():
                section = body.get("section")
        section = str(section or "").strip()

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

        obj = None

        if str(section).startswith("custom_"):
            try:
                section_pk = int(str(section).split("_", 1)[1])
            except (TypeError, ValueError):
                return JsonResponse(
                    {"success": False, "message": f"Invalid section: {section}"},
                    status=400,
                )
            try:
                obj = CustomDocument.objects.get(id=document_id, section_id=section_pk)
            except CustomDocument.DoesNotExist:
                obj = None
        else:
            model = INVESTOR_DOCUMENT_MODELS.get(section)
            if not model:
                return JsonResponse(
                    {"success": False, "message": f"Invalid section: {section}"},
                    status=400
                )
            try:
                obj = model.objects.get(id=document_id)
            except model.DoesNotExist:
                obj = None

        if obj is None:
            return JsonResponse(
                {
                    "success": False,
                    "message": f"Document not found (id={document_id}, section={section})."
                },
                status=404
            )

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
# SUMMARY REPORT DOWNLOAD (PDF)
# ============================================================

@login_required(login_url="dashboard_login")
@role_required(['ADMIN', 'EMPLOYEE'])
def download_summary_report(request):
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
        traceback.print_exc()
        return JsonResponse(
            {"success": False, "message": f"Failed to generate PDF: {str(e)}"},
            status=500
        )


# ============================================================
# EMPLOYEE MANAGEMENT & APPROVAL (Only ADMIN can access)
# ============================================================

@login_required(login_url="dashboard_login")
@role_required(['ADMIN'])
def employees_list_api(request):
    users = User.objects.select_related('profile').all().order_by("-date_joined")

    data = []
    for user in users:
        profile = user.profile if hasattr(user, 'profile') else None
        role = profile.role if profile else 'EMPLOYEE'
        approval_status = profile.approval_status if profile else ('APPROVED' if user.is_active else 'PENDING')
        emp_id = (profile.employee_id if profile and profile.employee_id else user.username)
        full_name = user.get_full_name().strip() or user.username

        data.append({
            "id": user.id,
            "employee_id": emp_id,
            "full_name": full_name,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "is_active": user.is_active,
            "is_staff": user.is_staff,
            "role": role,
            "approval_status": approval_status,
            "date_joined": user.date_joined.strftime("%d-%m-%Y"),
            "last_login": user.last_login.strftime("%d-%m-%Y %H:%M") if user.last_login else "Never",
        })

    return JsonResponse(data, safe=False)


@login_required(login_url="dashboard_login")
@role_required(['ADMIN'])
def approve_employee(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=405)

    try:
        body = json.loads(request.body)
        user_id = body.get("id")
        if not user_id:
            return JsonResponse({"success": False, "message": "User ID is required."}, status=400)

        target_user = User.objects.select_related('profile').get(id=user_id)
        if target_user.id == request.user.id:
            return JsonResponse({"success": False, "message": "You cannot modify your own approval status."}, status=400)

        profile = target_user.profile
        profile.approval_status = 'APPROVED'
        if not profile.employee_id:
            profile.employee_id = target_user.username
        profile.save(update_fields=["approval_status", "employee_id"])

        target_user.is_active = True
        target_user.is_staff = True
        target_user.save(update_fields=["is_active", "is_staff"])

        emp_label = f"{target_user.get_full_name().strip() or target_user.username} ({profile.employee_id})"
        log_audit(
            request,
            title=emp_label,
            section="user_management",
            action="approved",
            document_id=target_user.id,
            details=f"Approved registration for '{target_user.username}' ({profile.employee_id})",
        )

        return JsonResponse({
            "success": True,
            "message": f"Account '{target_user.username}' approved and activated.",
            "approval_status": "APPROVED",
        })
    except User.DoesNotExist:
        return JsonResponse({"success": False, "message": "User not found."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@login_required(login_url="dashboard_login")
@role_required(['ADMIN'])
def reject_employee(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=405)

    try:
        body = json.loads(request.body)
        user_id = body.get("id")
        if not user_id:
            return JsonResponse({"success": False, "message": "User ID is required."}, status=400)

        target_user = User.objects.select_related('profile').get(id=user_id)
        if target_user.id == request.user.id:
            return JsonResponse({"success": False, "message": "You cannot modify your own approval status."}, status=400)

        profile = target_user.profile
        profile.approval_status = 'REJECTED'
        profile.save(update_fields=["approval_status"])

        target_user.is_active = False
        target_user.save(update_fields=["is_active"])

        emp_label = f"{target_user.get_full_name().strip() or target_user.username} ({profile.employee_id or target_user.username})"
        log_audit(
            request,
            title=emp_label,
            section="user_management",
            action="rejected",
            document_id=target_user.id,
            details=f"Rejected registration for '{target_user.username}'",
        )

        return JsonResponse({
            "success": True,
            "message": f"Account '{target_user.username}' has been rejected.",
            "approval_status": "REJECTED",
        })
    except User.DoesNotExist:
        return JsonResponse({"success": False, "message": "User not found."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


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

        user.profile.role = role
        user.profile.employee_id = username
        user.profile.approval_status = 'APPROVED'
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


@never_cache
@login_required(login_url="dashboard_login")
@role_required(['ADMIN', 'EMPLOYEE'])
def recent_document_activity_api(request):
    """
    Latest 5 document actions for the dashboard Recent Documents card.
    Includes creation (uploaded), editing, and deletion.
    """

    logs = AuditLog.objects.all().order_by("-created_at")[:5]

    data = []

    for log in logs:
        action = normalize_audit_action(log.action)

        pdf_file, external_url = document_file_links(
            log.section,
            log.document_id
        )

        data.append({
            "id": log.id,
            "document_id": log.document_id,
            "title": log.document_title,
            "document_title": log.document_title,
            "section": log.section,
            "action": action,
            "activity": action,
            "details": log.details or "",
            "performed_by": log.performed_by,
            "created_at": log.created_at.strftime("%d-%m-%Y %H:%M"),
            "date": log.created_at.strftime("%d-%m-%Y %H:%M"),
            "pdf_file": pdf_file,
            "external_url": external_url,
        })

    return JsonResponse(data, safe=False)


@never_cache
@login_required(login_url="dashboard_login")
@role_required(['ADMIN', 'EMPLOYEE'])
def audit_log_api(request):
    """Admin sees all audit logs with employee name & ID; Employee sees only their own logs."""
    try:
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 10))
    except (TypeError, ValueError):
        page = 1
        page_size = 10

    page = max(1, page)
    page_size = min(50, max(1, page_size))

    profile = getattr(request.user, "profile", None)
    is_admin = bool(profile and profile.role == "ADMIN")

    if is_admin:
        qs = AuditLog.objects.all().order_by("-created_at")
    else:
        qs = AuditLog.objects.filter(performed_by=request.user.username).order_by("-created_at")

    total = qs.count()
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, total_pages)

    start = (page - 1) * page_size
    end = start + page_size
    logs = qs[start:end]

    usernames = {log.performed_by for log in logs if log.performed_by}
    user_map = {
        u.username: u
        for u in User.objects.select_related("profile").filter(username__in=usernames)
    }

    data = []
    for log in logs:
        actor_user = user_map.get(log.performed_by)
        actor_profile = getattr(actor_user, "profile", None) if actor_user else None

        emp_name = (
            actor_user.get_full_name().strip()
            if actor_user and actor_user.get_full_name().strip()
            else (log.performed_by or "System")
        )
        emp_id = (
            getattr(actor_profile, "employee_id", None)
            or (actor_user.username if actor_user else (log.performed_by or "—"))
        )

        entry = {
            "id": log.id,
            "document_title": log.document_title,
            "section": log.section,
            "action": normalize_audit_action(log.action),
            "details": log.details or "",
            "performed_by": log.performed_by,
            "created_at": log.created_at.strftime("%d-%m-%Y %H:%M"),
        }
        if is_admin:
            entry["employee_name"] = emp_name
            entry["employee_id"] = emp_id

        data.append(entry)

    return JsonResponse({
        "results": data,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "scope": "all" if is_admin else "self",
    })


# ============================================================
# SECTION MANAGEMENT (Admin only)
# ============================================================

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
            model_key="",
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

        with pdf_upload_user(
            request.user.username if request.user.is_authenticated else ""
        ):
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


def get_dashboard_context(request, active_tab):
    user = request.user

    if not hasattr(user, 'profile'):
        Profile.objects.create(user=user, role='EMPLOYEE', approval_status='APPROVED')

    profile = user.profile
    if not user.is_active or profile.approval_status != 'APPROVED':
        return None

    role = profile.role
    is_admin = role == "ADMIN"

    if active_tab in ["dashboard", "employees", "sections"] and not is_admin:
        return None

    display_name = user.get_full_name() or user.username
    initials = "".join([n[0] for n in display_name.split()[:2]]).upper() or "U"

    return {
        "active_tab": active_tab,
        "is_admin": is_admin,
        "user_role": role,
        "display_name": display_name,
        "username": user.username,
        "user_initials": initials,
    }


@never_cache
@login_required
def dashboard_view(request):
    context = get_dashboard_context(request, "dashboard")
    if context is None:
        return redirect("documents")
    return render(request, "dashboard/dashboard.html", context)


@never_cache
@login_required
def documents_view(request):
    context = get_dashboard_context(request, "documents")
    if context is None:
        logout(request)
        return redirect("dashboard_login")
    return render(request, "dashboard/documents.html", context)


@login_required
def upload_view(request):
    context = get_dashboard_context(request, "upload")
    if context is None:
        logout(request)
        return redirect("dashboard_login")
    return render(request, "dashboard/upload.html", context)


@never_cache
@login_required
def audit_log_view(request):
    context = get_dashboard_context(request, "audit_log")
    if context is None:
        logout(request)
        return redirect("dashboard_login")
    return render(request, "dashboard/audit_log.html", context)


@login_required
def employees_view(request):
    context = get_dashboard_context(request, "employees")
    if context is None:
        return redirect("documents")
    return render(request, "dashboard/employees.html", context)


@login_required
def sections_view(request):
    context = get_dashboard_context(request, "sections")
    if context is None:
        return redirect("documents")
    return render(request, "dashboard/sections.html", context)


# ============================================================
# PUBLIC WEBSITE PAGES
# ============================================================

def home(request):
    return render(request, "index.html")


def about(request):
    return render(request, "about.html")


def contact(request):
    return render(request, "contact.html")


def electronics(request):
    return render(request, "electronics.html")


def land_systems(request):
    return render(request, "land_systems.html")


def naval_systems(request):
    return render(request, "naval_systems.html")


def airforce_systems(request):
    return render(request, "airforce_systems.html")


def bbgpl(request):
    return render(request, "bbgpl.html")


def investors_page(request):
    return render(request, "Investors.html")