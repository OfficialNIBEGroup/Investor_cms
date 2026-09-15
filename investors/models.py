import os
import threading
from contextlib import contextmanager

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


_upload_user = threading.local()


@contextmanager
def pdf_upload_user(username):
    """Remember who is uploading so PDF registry rows can store uploaded_by."""
    previous = getattr(_upload_user, "username", "")
    _upload_user.username = username or ""
    try:
        yield
    finally:
        _upload_user.username = previous


def _current_upload_user():
    return getattr(_upload_user, "username", "") or ""

class DocumentBase(models.Model):
    """
    Common fields used by most investor documents.
    """

    title = models.CharField(max_length=255)

    pdf_file = models.FileField(
        upload_to="investor_documents/",
        blank=True,
        null=True
    )

    external_url = models.URLField(
        blank=True,
        null=True
    )

    published = models.BooleanField(default=True)

    display_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if not self.pdf_file and not self.external_url:
            raise ValidationError(
                "Please provide either a PDF file or an external URL."
            )

    class Meta:
        abstract = True

    def __str__(self):
        return self.title


class AnnualReport(DocumentBase):
    financial_year = models.CharField(max_length=20)


class FinancialResult(DocumentBase):
    financial_year = models.CharField(max_length=20)

    quarter = models.CharField(
        max_length=20,
        choices=[
            ("Q1", "Q1"),
            ("Q2", "Q2"),
            ("Q3", "Q3"),
            ("Q4", "Q4"),
            ("Annual", "Annual"),
        ]
    )

    release_date = models.DateField()


class AnnualReturn(DocumentBase):
    financial_year = models.CharField(max_length=20)


class CorporateGovernance(DocumentBase):
    financial_year = models.CharField(max_length=20)

    quarter = models.CharField(
        max_length=20,
        choices=[
            ("Q1", "Q1"),
            ("Q2", "Q2"),
            ("Q3", "Q3"),
            ("Q4", "Q4"),
            ("Annual", "Annual"),
        ]
    )


class ShareholdingPattern(DocumentBase):
    financial_year = models.CharField(max_length=20)

    quarter = models.CharField(
        max_length=20,
        choices=[
            ("Q1", "Q1"),
            ("Q2", "Q2"),
            ("Q3", "Q3"),
            ("Q4", "Q4"),
            ("Annual", "Annual"),
        ]
    )


class ShareholderNotice(DocumentBase):
    financial_year = models.CharField(max_length=20)

    notice_type = models.CharField(
        max_length=100,
        blank=True
    )

    disclosure_date = models.DateField(
        blank=True,
        null=True
    )

    meeting_date = models.DateField(
        blank=True,
        null=True
    )


class NewspaperPublication(DocumentBase):
    financial_year = models.CharField(
        max_length=20,
        blank=True
    )

    disclosure_date = models.DateField(
        blank=True,
        null=True
    )


class StockExchangeDisclosure(DocumentBase):
    financial_year = models.CharField(
        max_length=20,
        blank=True
    )

    disclosure_date = models.DateField(
        blank=True,
        null=True
    )


class SEBIDocument(DocumentBase):
    CATEGORY_CHOICES = [
        ("corporate_documents", "Corporate Documents"),
        ("board_of_directors", "Board of Directors"),
        ("board_committees", "Committees of Board of Directors"),
        ("codes_policies", "Codes and Policies"),
        ("investor_grievances", "Investor Grievances"),
    ]

    category = models.CharField(
        max_length=100,
        choices=CATEGORY_CHOICES
    )


class InvestorForm(DocumentBase):
    category = models.CharField(
        max_length=100,
        blank=True
    )

    description = models.TextField(
        blank=True
    )


class TaxDeclaration(DocumentBase):
    applicable_to = models.CharField(
        max_length=255,
        blank=True
    )

    description = models.TextField(
        blank=True
    )


class UnclaimedDividend(DocumentBase):
    financial_year = models.CharField(
        max_length=20
    )

    dividend_declaration_date = models.DateField(
        blank=True,
        null=True
    )

    dividend_type = models.CharField(
        max_length=100,
        blank=True
    )

    iepf_transfer_due_date = models.DateField(
        blank=True,
        null=True
    )


class SubsidiaryFinancial(DocumentBase):
    financial_year = models.CharField(
        max_length=20
    )

    company_name = models.CharField(
        max_length=255
    )

    financial_type = models.CharField(
        max_length=100,
        blank=True
    )

    

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("uploaded", "Uploaded"),
        ("edited", "Edited"),
        ("deleted", "Deleted"),
    ]

    document_title = models.CharField(max_length=255)
    section = models.CharField(max_length=100)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.TextField(blank=True, default="")
    performed_by = models.CharField(max_length=150)
    document_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} - {self.document_title} by {self.performed_by}"

    
# ============================================================
# DYNAMIC SECTIONS + SUB-SECTIONS + CUSTOM DOCUMENTS
# ============================================================
# A) Admin can create completely new sections
# B) Admin can manage existing sections (name, order, show/hide)
# C) Admin can add sub-sections under any section
# Documents under custom sections support: PDF, external URL, published


class Section(models.Model):
    """
    Top-level document section shown in dashboard / public portal.

    System sections (is_system=True) map to existing models via model_key
    e.g. annual_report → AnnualReport model.
    Custom sections (is_system=False) store documents in CustomDocument.
    """

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)
    # Links to hardcoded model when is_system=True
    model_key = models.CharField(
        max_length=80,
        blank=True,
        default="",
        help_text="Internal key for system sections, e.g. annual_report",
    )
    description = models.TextField(blank=True, default="")
    icon = models.CharField(max_length=20, blank=True, default="📁")
    is_system = models.BooleanField(
        default=False,
        help_text="System sections cannot be deleted",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive sections are hidden from upload / public",
    )
    show_on_public = models.BooleanField(
        default=True,
        help_text="Show this section on the public investors page",
    )
    allow_subsections = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        kind = "System" if self.is_system else "Custom"
        return f"{self.name} ({kind})"


class SubSection(models.Model):
    """
    Optional child category under a Section (Option C).
    """

    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="subsections",
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]
        unique_together = [("section", "slug")]

    def __str__(self):
        return f"{self.section.name} → {self.name}"


class CustomDocument(models.Model):
    """
    Documents belonging to custom (non-system) sections.
    Same core behaviour as existing document types:
    title, PDF file, external URL, published, display order.
    """

    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="custom_documents",
    )
    subsection = models.ForeignKey(
        SubSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )
    title = models.CharField(max_length=255)
    pdf_file = models.FileField(
        upload_to="investor_documents/custom/",
        blank=True,
        null=True,
    )
    external_url = models.URLField(blank=True, null=True)
    published = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    # Optional free-text meta (financial year, notes, etc.)
    extra_info = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-display_order", "-created_at"]

    def clean(self):
        if not self.pdf_file and not self.external_url:
            raise ValidationError(
                "Please provide either a PDF file or an external URL."
            )

    def __str__(self):
        return f"{self.title} [{self.section.name}]"


# ============================================================
# UNIFIED PDF REGISTRY (all uploaded PDFs, shown in Django admin)
# ============================================================

class UploadedPDF(models.Model):
    """
    One row for every PDF saved on an investor document.
    The file itself lives under MEDIA_ROOT; this table stores the DB record
    so every upload is visible in Django admin regardless of section.
    """

    title = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255, blank=True, default="")
    pdf_file = models.FileField(
        upload_to="investor_documents/",
        blank=True,
        null=True,
    )
    section = models.CharField(max_length=150)
    uploaded_by = models.CharField(max_length=150, blank=True, default="")
    source_model = models.CharField(max_length=100)
    source_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Uploaded PDF"
        verbose_name_plural = "All Uploaded PDFs"
        ordering = ["-created_at"]
        unique_together = [("source_model", "source_id")]

    def __str__(self):
        return self.title or self.original_filename or "PDF"


PDF_SOURCE_MODELS = (
    AnnualReport,
    FinancialResult,
    AnnualReturn,
    CorporateGovernance,
    ShareholdingPattern,
    ShareholderNotice,
    NewspaperPublication,
    StockExchangeDisclosure,
    SEBIDocument,
    InvestorForm,
    TaxDeclaration,
    UnclaimedDividend,
    SubsidiaryFinancial,
    CustomDocument,
)

PDF_SECTION_LABELS = {
    "AnnualReport": "Annual Report",
    "FinancialResult": "Financial Result",
    "AnnualReturn": "Annual Return",
    "CorporateGovernance": "Corporate Governance",
    "ShareholdingPattern": "Shareholding Pattern",
    "ShareholderNotice": "Shareholder Notice",
    "NewspaperPublication": "Newspaper Publication",
    "StockExchangeDisclosure": "Stock Exchange Disclosure",
    "SEBIDocument": "SEBI Document",
    "InvestorForm": "Investor Form",
    "TaxDeclaration": "Tax Declaration",
    "UnclaimedDividend": "Unclaimed Dividend",
    "SubsidiaryFinancial": "Subsidiary Financial",
    "CustomDocument": "Custom Section",
}


def _pdf_section_label(sender, instance):
    if sender is CustomDocument:
        try:
            return instance.section.name
        except Exception:
            return "Custom Section"
    return PDF_SECTION_LABELS.get(sender.__name__, sender.__name__)


def sync_uploaded_pdf(sender, instance, **kwargs):
    """Keep UploadedPDF in sync whenever a document with a PDF is saved."""
    if not instance.pk:
        return

    pdf = getattr(instance, "pdf_file", None)
    pdf_name = getattr(pdf, "name", "") if pdf else ""
    if not pdf_name:
        UploadedPDF.objects.filter(
            source_model=sender.__name__,
            source_id=instance.pk,
        ).delete()
        return

    username = _current_upload_user()
    record, _created = UploadedPDF.objects.update_or_create(
        source_model=sender.__name__,
        source_id=instance.pk,
        defaults={
            "title": instance.title or os.path.basename(pdf_name),
            "original_filename": os.path.basename(pdf_name),
            "section": _pdf_section_label(sender, instance),
        },
    )

    changed_fields = []
    if record.pdf_file.name != pdf_name:
        record.pdf_file.name = pdf_name
        changed_fields.append("pdf_file")
    if username and record.uploaded_by != username:
        record.uploaded_by = username
        changed_fields.append("uploaded_by")
    if changed_fields:
        record.save(update_fields=changed_fields)


def delete_uploaded_pdf(sender, instance, **kwargs):
    if not instance.pk:
        return
    UploadedPDF.objects.filter(
        source_model=sender.__name__,
        source_id=instance.pk,
    ).delete()


for _pdf_model in PDF_SOURCE_MODELS:
    post_save.connect(sync_uploaded_pdf, sender=_pdf_model)
    post_delete.connect(delete_uploaded_pdf, sender=_pdf_model)


# ============================================================
# USER PROFILE + ROLE BASED ACCESS
# ============================================================
# We keep Django's default User model and attach a Profile
# that stores the role of each user.
# Roles: ADMIN, EMPLOYEE, CLIENT

class Profile(models.Model):
    """
    Extra information for every User.
    Main purpose: store the ROLE of the user.
    """

    # Choices for the role field
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),         # Full power (manage employees + documents)
        ('EMPLOYEE', 'Employee'),   # Can upload / edit / delete documents
        ('CLIENT', 'Client'),       # Outside user (currently no dashboard access)
    )

    # One-to-One link with Django User
    # related_name='profile' → you can do request.user.profile
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    # The actual role
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='EMPLOYEE'          # New users are Employee by default
    )

    # Optional fields you can use later
    phone = models.CharField(max_length=15, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} → {self.get_role_display()}"

    # ---------- Helper properties (very useful in views & templates) ----------
    @property
    def is_admin(self):
        return self.role == 'ADMIN'

    @property
    def is_employee(self):
        return self.role == 'EMPLOYEE'

    @property
    def is_client(self):
        return self.role == 'CLIENT'


# ---------- Auto create Profile when a new User is created ----------
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Whenever a new User is created, automatically create a Profile for him/her.
    """
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Make sure Profile is saved whenever User is saved.
    """
    # This protects against users created before Profile model existed
    if hasattr(instance, 'profile'):
        instance.profile.save()