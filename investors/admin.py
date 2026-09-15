from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html

from .models import (
    AuditLog,
    Profile,
    Section,
    SubSection,
    UploadedPDF,
)


# ============================================================
# SINGLE PDF TABLE
# Every uploaded PDF (all sections) appears here — not in
# separate Annual Report / Financial Result / etc. tables.
# ============================================================

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
    list_display_links = ("title",)
    list_filter = ("section", "created_at")
    search_fields = ("title", "original_filename", "section", "uploaded_by")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_per_page = 50
    readonly_fields = (
        "title",
        "pdf_link",
        "pdf_file",
        "original_filename",
        "section",
        "uploaded_by",
        "created_at",
        "updated_at",
    )
    fields = (
        "title",
        "section",
        "pdf_link",
        "pdf_file",
        "original_filename",
        "uploaded_by",
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
        # Rows are created automatically when a PDF is uploaded
        # from the dashboard. This table is the single admin view.
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


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
    verbose_name_plural = "Profile / Role"


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "get_role")
    list_filter = ("is_staff", "is_active", "profile__role")

    def get_role(self, obj):
        return obj.profile.get_role_display() if hasattr(obj, "profile") else "-"
    get_role.short_description = "Role"


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "phone", "department", "created_at")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email", "phone")


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


def _investors_app_list(request, app_label=None):
    """Put All Uploaded PDFs first in the Investors admin group."""
    app_list = AdminSite.get_app_list(admin.site, request, app_label)
    for app in app_list:
        if app.get("app_label") != "investors":
            continue
        app["models"].sort(
            key=lambda m: (
                0 if m.get("object_name") == "UploadedPDF" else 1,
                m.get("name", ""),
            )
        )
    return app_list


admin.site.get_app_list = _investors_app_list
