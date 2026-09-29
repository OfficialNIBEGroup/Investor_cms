import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import AnnualReport, AuditLog
from .views import describe_document_changes, normalize_audit_action


class AuditLogStatusTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="auditor", password="pass12345")
        self.user.profile.role = "ADMIN"
        self.user.profile.save()
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
        self.assertEqual(api.status_code, 200)
        payload = api.json()["results"][0]
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
        self.assertEqual(api.status_code, 200)
        payload = api.json()["results"][0]
        self.assertEqual(payload["action"], "edited")
        self.assertTrue(payload["details"])

    def test_edit_post_persists_document_changes(self):
        response = self.client.post(
            reverse("edit_investor_document", args=[self.doc.id, "annual_report"]),
            data={
                "title": "FY Report Revised",
                "financial_year": "2025-26",
                "external_url": "https://example.com/revised.pdf",
                "published": "false",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        self.doc.refresh_from_db()
        self.assertEqual(self.doc.title, "FY Report Revised")
        self.assertEqual(self.doc.financial_year, "2025-26")
        self.assertEqual(self.doc.external_url, "https://example.com/revised.pdf")
        self.assertFalse(self.doc.published)
        self.assertTrue(
            AuditLog.objects.filter(action="edited", document_id=self.doc.id).exists()
        )

    def test_update_keeps_fields_that_were_not_submitted(self):
        response = self.client.post(
            reverse("update_investor_document"),
            data={
                "document_id": self.doc.id,
                "section": "annual_report",
                "title": "Only Title",
                "external_url": "https://example.com/report.pdf",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.title, "Only Title")
        self.assertEqual(self.doc.financial_year, "2024-25")

    def test_edit_get_includes_published_status(self):
        self.doc.published = False
        self.doc.save(update_fields=["published"])
        response = self.client.get(
            reverse("edit_investor_document", args=[self.doc.id, "annual_report"])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIs(response.json()["document"]["published"], False)

    def test_recent_activity_includes_create_edit_and_delete(self):
        AuditLog.objects.create(
            document_title=self.doc.title,
            section="annual_report",
            action="uploaded",
            details="New document uploaded",
            performed_by="auditor",
            document_id=self.doc.id,
        )
        edited = self.client.post(
            reverse("update_investor_document"),
            data={
                "document_id": self.doc.id,
                "section": "annual_report",
                "title": "FY Report Revised",
                "financial_year": "2024-25",
                "external_url": "https://example.com/report.pdf",
            },
        )
        self.assertEqual(edited.status_code, 200)

        deleted = self.client.post(
            reverse("delete_investor_document"),
            data=json.dumps({
                "document_id": self.doc.id,
                "section": "annual_report",
            }),
            content_type="application/json",
        )
        self.assertEqual(deleted.status_code, 200)
        self.assertFalse(AnnualReport.objects.filter(id=self.doc.id).exists())

        activity = self.client.get(reverse("recent_document_activity_api"))
        self.assertEqual(activity.status_code, 200)
        actions = {item["action"] for item in activity.json()}
        self.assertTrue({"uploaded", "edited", "deleted"}.issubset(actions))

    def test_custom_document_edit_and_delete(self):
        from .models import CustomDocument, Section

        section = Section.objects.create(
            name="Board Policies",
            slug="board-policies",
            is_system=False,
        )
        doc = CustomDocument.objects.create(
            section=section,
            title="Policy A",
            external_url="https://example.com/policy",
        )
        section_key = f"custom_{section.id}"

        updated = self.client.post(
            reverse("update_investor_document"),
            data={
                "document_id": doc.id,
                "section": section_key,
                "title": "Policy B",
                "external_url": "https://example.com/policy",
                "extra_info": "Revised note",
            },
        )
        self.assertEqual(updated.status_code, 200)
        doc.refresh_from_db()
        self.assertEqual(doc.title, "Policy B")
        self.assertEqual(doc.extra_info, "Revised note")

        deleted = self.client.post(
            reverse("delete_investor_document"),
            data=json.dumps({
                "document_id": doc.id,
                "section": section_key,
            }),
            content_type="application/json",
        )
        self.assertEqual(deleted.status_code, 200)
        self.assertFalse(CustomDocument.objects.filter(id=doc.id).exists())
        self.assertTrue(
            AuditLog.objects.filter(action="deleted", document_title="Policy B").exists()
        )

    def test_legacy_delete_url_removes_document_and_writes_log(self):
        response = self.client.post(
            reverse(
                "delete_investor_document_legacy",
                args=[self.doc.id, "annual_report"],
            ),
            data=json.dumps({"id": self.doc.id, "section": "annual_report"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertFalse(AnnualReport.objects.filter(id=self.doc.id).exists())

        activity = self.client.get(reverse("recent_document_activity_api"))
        self.assertEqual(activity.status_code, 200)
        self.assertIn("no-store", activity["Cache-Control"])
        self.assertIn("deleted", {item["action"] for item in activity.json()})

        audit = self.client.get(reverse("audit_log_api"))
        self.assertEqual(audit.status_code, 200)
        self.assertEqual(audit.json()["results"][0]["action"], "deleted")

    def test_empty_pdf_input_still_saves_title(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        response = self.client.post(
            reverse("update_investor_document"),
            data={
                "document_id": self.doc.id,
                "section": "annual_report",
                "title": "Title Kept With Blank File",
                "financial_year": "2024-25",
                "external_url": "https://example.com/report.pdf",
                "published": "true",
                "pdf_file": SimpleUploadedFile("blank.pdf", b"", content_type="application/pdf"),
            },
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.title, "Title Kept With Blank File")
        self.assertFalse(self.doc.pdf_file)

    def test_documents_page_save_and_delete_use_working_urls(self):
        response = self.client.get(reverse("documents"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response["Cache-Control"])
        html = response.content.decode()
        self.assertIn(reverse("update_investor_document"), html)
        self.assertIn(reverse("delete_investor_document"), html)
        self.assertIn("window.deleteDocument", html)
        self.assertIn('name="csrfmiddlewaretoken"', html)


class PublicInvestorPageTests(TestCase):
    def test_page_loads_documents_from_the_admin_panel(self):
        response = self.client.get(reverse("investors"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("investorMenu", html)
        self.assertIn("investors_documents.js", html)
        self.assertIn(reverse("public_investor_documents"), html)
        self.assertNotIn("drive.google.com", html)
        self.assertNotIn("sharepoint.com", html)

    def test_only_published_admin_documents_are_returned(self):
        from datetime import date

        from .models import FinancialResult

        AnnualReport.objects.create(
            title="Public Annual Report",
            financial_year="2024-25",
            external_url="https://example.com/annual.pdf",
            published=True,
        )
        AnnualReport.objects.create(
            title="Hidden Annual Report",
            financial_year="2023-24",
            external_url="https://example.com/hidden.pdf",
            published=False,
        )
        FinancialResult.objects.create(
            title="Quarter One Results",
            financial_year="2024-25",
            quarter="Q1",
            release_date=date(2024, 8, 14),
            external_url="https://example.com/q1.pdf",
            published=True,
        )

        response = self.client.get(reverse("public_investor_documents"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response["Cache-Control"])
        sections = {item["key"]: item for item in response.json()["sections"]}

        annual_titles = [doc["title"] for doc in sections["annual_report"]["documents"]]
        self.assertIn("Public Annual Report", annual_titles)
        self.assertNotIn("Hidden Annual Report", annual_titles)

        results = sections["financial_result"]["documents"]
        self.assertEqual(results[0]["title"], "Quarter One Results")
        self.assertEqual(results[0]["quarter"], "Q1")
        self.assertEqual(results[0]["release_date"], "14-08-2024")

    def test_hidden_system_section_is_omitted_and_custom_section_is_included(self):
        from .models import CustomDocument, Section

        Section.objects.create(
            name="Annual Reports",
            slug="annual-reports",
            model_key="annual_report",
            is_system=True,
            is_active=True,
            show_on_public=False,
        )
        AnnualReport.objects.create(
            title="Should Stay Hidden",
            financial_year="2024-25",
            external_url="https://example.com/annual.pdf",
            published=True,
        )
        custom = Section.objects.create(
            name="Board Notes",
            slug="board-notes",
            is_system=False,
            is_active=True,
            show_on_public=True,
        )
        CustomDocument.objects.create(
            section=custom,
            title="Published Note",
            external_url="https://example.com/note.pdf",
            published=True,
        )
        CustomDocument.objects.create(
            section=custom,
            title="Draft Note",
            external_url="https://example.com/draft.pdf",
            published=False,
        )

        response = self.client.get(reverse("public_investor_documents"))
        sections = response.json()["sections"]
        keys = [item["key"] for item in sections]
        self.assertNotIn("annual_report", keys)

        board = next(item for item in sections if item["key"] == f"custom_{custom.id}")
        self.assertEqual(board["name"], "Board Notes")
        self.assertEqual([doc["title"] for doc in board["documents"]], ["Published Note"])
