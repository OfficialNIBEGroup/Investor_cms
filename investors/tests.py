import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import AnnualReport, AuditLog
from .views import describe_document_changes, normalize_audit_action


class AuditLogStatusTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="auditor", password="pass12345")
        self.client.login(username="auditor", password="pass12345")
        self.doc = AnnualReport.objects.create(
            title="FY Report",
            financial_year="2024-25",
            external_url="https://example.com/report.pdf",
        )

    def test_normalize_maps_legacy_action_labels(self):
        self.assertEqual(normalize_audit_action("Deleted"), "deleted")
        self.assertEqual(normalize_audit_action("Updated"), "edited")
        self.assertEqual(normalize_audit_action("Created"), "uploaded")

    def test_describe_document_changes(self):
        details = describe_document_changes(
            {"title": "Old", "financial_year": "2023-24"},
            {"title": "New", "financial_year": "2023-24"},
            pdf_replaced=True,
        )
        self.assertIn("Title changed from 'Old' to 'New'", details)
        self.assertIn("PDF file replaced", details)

    def test_delete_log_uses_deleted_status(self):
        response = self.client.post(
            reverse("delete_investor_document"),
            data=json.dumps({
                "document_id": self.doc.id,
                "section": "annual_report",
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        log = AuditLog.objects.get(action="deleted")
        self.assertEqual(log.document_title, "FY Report")
        self.assertEqual(log.details, "Document deleted")

        api = self.client.get(reverse("audit_log_api"))
        payload = api.json()[0]
        self.assertEqual(payload["action"], "deleted")
        self.assertEqual(payload["details"], "Document deleted")

    def test_update_log_uses_edited_status_and_field_changes(self):
        response = self.client.post(
            reverse("update_investor_document"),
            data={
                "document_id": self.doc.id,
                "section": "annual_report",
                "title": "FY Report Revised",
                "financial_year": "2025-26",
                "external_url": "https://example.com/report.pdf",
            },
        )
        self.assertEqual(response.status_code, 200)

        log = AuditLog.objects.get(action="edited")
        self.assertIn("Title changed from 'FY Report' to 'FY Report Revised'", log.details)
        self.assertIn("Financial Year changed from '2024-25' to '2025-26'", log.details)

        api = self.client.get(reverse("audit_log_api"))
        payload = api.json()[0]
        self.assertEqual(payload["action"], "edited")
        self.assertTrue(payload["details"])
