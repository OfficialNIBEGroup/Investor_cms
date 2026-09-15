from django import forms

from django.contrib import admin
from django.utils.html import format_html
from .models import (
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
    AuditLog,
    UploadedPDF,
    pdf_upload_user,
    # DocumentBase,
)

from .models import Profile
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User


class PdfPreviewMixin:
    """Show a View PDF link in list/change views and record who saved the file."""

    def pdf_link(self, obj):
        pdf = getattr(obj, "pdf_file", None)
        if pdf:
            return format_html(
                '<a href="{}" target="_blank" rel="noopener noreferrer">View PDF</a>',
                pdf.url,
            )
        return "—"

    pdf_link.short_description = "PDF"
    pdf_link.admin_order_field = "pdf_file"

    def get_list_display(self, request):
        display = list(super().get_list_display(request))
        if "pdf_link" not in display:
            if "title" in display:
                display.insert(display.index("title") + 1, "pdf_link")
            else:
                display.append("pdf_link")
        return display

    def save_model(self, request, obj, form, change):
        with pdf_upload_user(request.user.username):
            super().save_model(request, obj, form, change)

@admin.register(AnnualReport)
class AnnualReportAdmin(PdfPreviewMixin, admin.ModelAdmin):
    list_display = (
        "title",
        "financial_year",
        "published",
        "display_order",
        "created_at",
    )

    list_filter = (
        "financial_year",
        "published",
    )

    search_fields = (
        "title",
        "financial_year",
    )

    ordering = (
        "financial_year",
        "display_order",
    )


@admin.register(FinancialResult)
class FinancialResultAdmin(PdfPreviewMixin, admin.ModelAdmin):
    list_display = (
        "title",
        "financial_year",
        "quarter",
        "release_date",
        "published",
        "display_order",
    )

    list_filter = (
        "financial_year",
        "quarter",
        "published",
    )

    search_fields = (
        "title",
        "financial_year",
    )

    ordering = (
        "-release_date",
        "display_order",
    )


@admin.register(AnnualReturn)
class AnnualReturnAdmin(PdfPreviewMixin, admin.ModelAdmin):
    list_display = (
        "title",
        "financial_year",
        "published",
        "display_order",
        "created_at",
    )

    list_filter = (
        "financial_year",
        "published",
    )

    search_fields = (
        "title",
        "financial_year",
    )

    ordering = (
        "-financial_year",
        "display_order",
    )


@admin.register(CorporateGovernance)
class CorporateGovernanceAdmin(PdfPreviewMixin, admin.ModelAdmin):
    list_display = (
        "title",
        "financial_year",
        "quarter",
        "published",
        "display_order",
        "created_at",
    )

    list_filter = (
        "financial_year",
        "quarter",
        "published",
    )

    search_fields = (
        "title",
        "financial_year",
    )

    ordering = (
        "-financial_year",
        "quarter",
        "display_order",
    )


@admin.register(ShareholdingPattern)
class ShareholdingPatternAdmin(PdfPreviewMixin, admin.ModelAdmin):
    list_display = (
        "title",
        "financial_year",
        "quarter",
        "published",
        "display_order",
        "created_at",
    )

    list_filter = (
        "financial_year",
        "quarter",
        "published",
    )

    search_fields = (
        "title",
        "financial_year",
    )

    ordering = (
        "-financial_year",
        "quarter",
        "display_order",
    )


@admin.register(ShareholderNotice)
class ShareholderNoticeAdmin(PdfPreviewMixin, admin.ModelAdmin):
    list_display = (
        "title",
        "financial_year",
        "notice_type",
        "disclosure_date",
        "meeting_date",
        "published",
        "display_order",
        "created_at",
    )

    list_filter = (
        "financial_year",
        "notice_type",
        "published",
    )

    search_fields = (
        "title",
        "financial_year",
        "notice_type",
    )

    ordering = (
        "-disclosure_date",
        "display_order",
    )


@admin.register(NewspaperPublication)
class NewspaperPublicationAdmin(PdfPreviewMixin, admin.ModelAdmin):
    list_display = (
        "title",
        "financial_year",
        "disclosure_date",
        "published",
        "display_order",
        "created_at",
    )

    list_filter = (
        "financial_year",
        "published",
    )

    search_fields = (
        "title",
        "financial_year",
    )

    ordering = (
        "-disclosure_date",
        "display_order",
    )


@admin.register(StockExchangeDisclosure)
class StockExchangeDisclosureAdmin(PdfPreviewMixin, admin.ModelAdmin):
    list_display = (
        "title",
        "financial_year",
        "disclosure_date",
        "published",
        "display_order",
        "created_at",
    )

    list_filter = (
        "financial_year",
        "published",
    )

    search_fields = (
        "title",
        "financial_year",
    )

    ordering = (
        "-disclosure_date",
        "display_order",
    )


@admin.register(SEBIDocument)
class SEBIDocumentAdmin(PdfPreviewMixin, admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "published",
        "display_order",
        "created_at",
    )

    list_filter = (
        "category",
        "published",
    )

    search_fields = (
        "title",
        "category",
    )

    ordering = (
        "category",
        "display_order",
    )


@admin.register(InvestorForm)
class InvestorFormAdmin(PdfPreviewMixin, admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "published",
        "display_order",
        "created_at",
    )

    list_filter = (
        "category",
        "published",
    )

    search_fields = (
        "title",
        "category",
        "description",
    )

    ordering = (
        "category",
        "display_order",
    )


class TaxDeclarationAdminForm(forms.ModelForm):
    class Meta:
        model = TaxDeclaration
        fields = "__all__"
        labels = {
            "description": "Purpose",
        }


@admin.register(TaxDeclaration)
class TaxDeclarationAdmin(PdfPreviewMixin, admin.ModelAdmin):
    form = TaxDeclarationAdminForm

    list_display = (
        "title",
        "applicable_to",
        "published",
        "display_order",
        "created_at",
    )

    list_filter = (
        "published",
    )

    search_fields = (
        "title",
        "applicable_to",
        "description",
    )

    ordering = (
        "display_order",
        "-created_at",
    )


@admin.register(UnclaimedDividend)
class UnclaimedDividendAdmin(PdfPreviewMixin, admin.ModelAdmin):
    list_display = (
        "title",
        "financial_year",
        "dividend_type",
        "dividend_declaration_date",
        "iepf_transfer_due_date",
        "published",
        "display_order",
        "created_at",
    )

    list_filter = (
        "financial_year",
        "dividend_type",
        "published",
    )

    search_fields = (
        "title",
        "financial_year",
        "dividend_type",
    )

    ordering = (
        "-financial_year",
        "display_order",
    )


class SubsidiaryFinancialAdminForm(forms.ModelForm):
    class Meta:
        model = SubsidiaryFinancial
        fields = "__all__"
        exclude = (
            "title",
            "financial_type",
        )


@admin.register(SubsidiaryFinancial)
class SubsidiaryFinancialAdmin(PdfPreviewMixin, admin.ModelAdmin):
    form = SubsidiaryFinancialAdminForm

    list_display = (
        "company_name",
        "financial_year",
        "published",
        "display_order",
        "created_at",
    )

    list_filter = (
        "financial_year",
        "published",
    )

    search_fields = (
        "company_name",
        "financial_year",
    )

    ordering = (
        "-financial_year",
        "display_order",
    )

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "document_title",
        "section",
        "action",
        "details",
        "performed_by",
        "created_at",
    )
    list_filter = (
        "section",
        "action",
    )
    search_fields = (
        "document_title",
        "performed_by",
        "details",
    )
    ordering = (
        "-created_at",
    )




class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile / Role'


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    list_filter = ('is_staff', 'is_active', 'profile__role')

    def get_role(self, obj):
        return obj.profile.get_role_display() if hasattr(obj, 'profile') else '-'
    get_role.short_description = 'Role'


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone', 'department', 'created_at')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'phone')
from .models import Section, SubSection, CustomDocument


class SubSectionInline(admin.TabularInline):
    model = SubSection
    extra = 0


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = (
        "name", "slug", "model_key", "is_system", "is_active",
        "show_on_public", "display_order",
    )
    list_filter = ("is_system", "is_active", "show_on_public")
    search_fields = ("name", "slug", "model_key")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("display_order", "name")
    inlines = [SubSectionInline]


@admin.register(SubSection)
class SubSectionAdmin(admin.ModelAdmin):
    list_display = ("name", "section", "slug", "is_active", "display_order")
    list_filter = ("is_active", "section")
    search_fields = ("name", "slug")
    ordering = ("section", "display_order")


@admin.register(CustomDocument)
class CustomDocumentAdmin(PdfPreviewMixin, admin.ModelAdmin):
    list_display = (
        "title", "section", "subsection", "published",
        "display_order", "created_at",
    )
    list_filter = ("published", "section")
    search_fields = ("title", "extra_info")
    ordering = ("-display_order", "-created_at")


@admin.register(UploadedPDF)
class UploadedPDFAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "pdf_link",
        "section",
        "original_filename",
        "uploaded_by",
        "created_at",
    )
    list_filter = ("section", "created_at")
    search_fields = ("title", "original_filename", "section", "uploaded_by")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    readonly_fields = (
        "title",
        "original_filename",
        "pdf_file",
        "pdf_link",
        "section",
        "uploaded_by",
        "source_model",
        "source_id",
        "created_at",
        "updated_at",
    )

    def pdf_link(self, obj):
        if obj.pdf_file:
            return format_html(
                '<a href="{}" target="_blank" rel="noopener noreferrer">View PDF</a>',
                obj.pdf_file.url,
            )
        return "—"

    pdf_link.short_description = "PDF"

    def has_add_permission(self, request):
        # PDFs are created when a document is uploaded (dashboard or document admin).
        return False

# @admin.register(DocumentBase)
# class DocumentBaseAdmin(admin.ModelAdmin):
#     list_display = (
#             "title", "pdf_file", "external_url", "published",
#         )