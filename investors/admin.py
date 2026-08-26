from django import forms

from django.contrib import admin
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
)


@admin.register(AnnualReport)
class AnnualReportAdmin(admin.ModelAdmin):
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
class FinancialResultAdmin(admin.ModelAdmin):
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
class AnnualReturnAdmin(admin.ModelAdmin):
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
class CorporateGovernanceAdmin(admin.ModelAdmin):
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
class ShareholdingPatternAdmin(admin.ModelAdmin):
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
class ShareholderNoticeAdmin(admin.ModelAdmin):
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
class NewspaperPublicationAdmin(admin.ModelAdmin):
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
class StockExchangeDisclosureAdmin(admin.ModelAdmin):
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
class SEBIDocumentAdmin(admin.ModelAdmin):
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
class InvestorFormAdmin(admin.ModelAdmin):
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
class TaxDeclarationAdmin(admin.ModelAdmin):
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
class UnclaimedDividendAdmin(admin.ModelAdmin):
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
class SubsidiaryFinancialAdmin(admin.ModelAdmin):
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