# Generated for UploadedPDF registry + backfill of existing PDFs

import os

from django.db import migrations, models


PDF_SOURCE_MODELS = (
    ("AnnualReport", "Annual Report"),
    ("FinancialResult", "Financial Result"),
    ("AnnualReturn", "Annual Return"),
    ("CorporateGovernance", "Corporate Governance"),
    ("ShareholdingPattern", "Shareholding Pattern"),
    ("ShareholderNotice", "Shareholder Notice"),
    ("NewspaperPublication", "Newspaper Publication"),
    ("StockExchangeDisclosure", "Stock Exchange Disclosure"),
    ("SEBIDocument", "SEBI Document"),
    ("InvestorForm", "Investor Form"),
    ("TaxDeclaration", "Tax Declaration"),
    ("UnclaimedDividend", "Unclaimed Dividend"),
    ("SubsidiaryFinancial", "Subsidiary Financial"),
    ("CustomDocument", "Custom Section"),
)


def backfill_uploaded_pdfs(apps, schema_editor):
    UploadedPDF = apps.get_model("investors", "UploadedPDF")

    for model_name, label in PDF_SOURCE_MODELS:
        Model = apps.get_model("investors", model_name)
        for obj in Model.objects.all().iterator():
            pdf = getattr(obj, "pdf_file", None)
            pdf_name = getattr(pdf, "name", "") if pdf else ""
            if not pdf_name:
                continue

            if model_name == "CustomDocument":
                try:
                    section = obj.section.name
                except Exception:
                    section = label
            else:
                section = label

            UploadedPDF.objects.update_or_create(
                source_model=model_name,
                source_id=obj.id,
                defaults={
                    "title": obj.title or os.path.basename(pdf_name),
                    "original_filename": os.path.basename(pdf_name),
                    "pdf_file": pdf_name,
                    "section": section,
                },
            )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("investors", "0005_section_subsection_customdocument"),
    ]

    operations = [
        migrations.CreateModel(
            name="UploadedPDF",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                (
                    "original_filename",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                (
                    "pdf_file",
                    models.FileField(
                        blank=True, null=True, upload_to="investor_documents/"
                    ),
                ),
                ("section", models.CharField(max_length=150)),
                (
                    "uploaded_by",
                    models.CharField(blank=True, default="", max_length=150),
                ),
                ("source_model", models.CharField(max_length=100)),
                ("source_id", models.IntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Uploaded PDF",
                "verbose_name_plural": "Uploaded PDFs",
                "ordering": ["-created_at"],
                "unique_together": {("source_model", "source_id")},
            },
        ),
        migrations.RunPython(backfill_uploaded_pdfs, noop_reverse),
    ]
