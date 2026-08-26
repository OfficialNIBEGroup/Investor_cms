from django.db import models
from django.core.exceptions import ValidationError


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
    performed_by = models.CharField(max_length=150)
    document_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} - {self.document_title} by {self.performed_by}"

    