from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    annual_reports_api,
    financial_results_api,
    annual_returns_api,
    shareholder_notices_api,
    newspaper_publications_api,
    stock_exchange_disclosures_api,
    corporate_governance_api,
    shareholding_pattern_api,
    sebi_documents_api,
    investor_forms_api,
    tax_declarations_api,
    unclaimed_dividends_api,
    subsidiary_financials_api,
    investors_page,
    upload_dashboard,
    dashboard_login,
    dashboard_documents_api,
    dashboard_statistics_api,
    dashboard_logout,
    upload_investor_document,
    update_investor_document,
    delete_investor_document,
    edit_investor_document,
    download_summary_report,
    employees_list_api,
    create_employee,
    update_employee,
    toggle_employee_status,
    delete_employee,
    audit_log_api,
)


urlpatterns = [
    path(
        "api/annual-reports/",
        annual_reports_api,
        name="annual_reports_api",
    ),

    path(
        "api/financial-results/",
        financial_results_api,
        name="financial_results_api",
    ),

    path("api/annual-returns/", 
         annual_returns_api, 
         name="annual_returns_api"),

    path(
    'api/shareholder-notices/',
    shareholder_notices_api,
    name="shareholder_notices_api"),

    path(
    'api/newspaper-publications/',
    newspaper_publications_api,
    name='newspaper_publications_api'),

    path(
    'api/stock-exchange-disclosures/',
    stock_exchange_disclosures_api,
    name='stock_exchange_disclosures_api'),

    path(
        'api/corporate-governance/',
        corporate_governance_api,
        name='corporate_governance_api'
    ),

    path(
        'api/shareholding-pattern/',
        shareholding_pattern_api,
        name='shareholding_pattern_api'
    ),

    path(
    'api/sebi-documents/',
    sebi_documents_api,
    name='sebi_documents_api'
    ),

    path(
        'api/investor-forms/',
        investor_forms_api,
        name='investor_forms_api'
    ),

    path(
    'api/tax-declarations/',
    tax_declarations_api,
    name='tax_declarations_api'
    ),

    path(
    'api/unclaimed-dividends/',
    unclaimed_dividends_api,
    name='unclaimed_dividends_api'
    ),

    path(
    'api/subsidiary-financials/',
    subsidiary_financials_api,
    name='subsidiary_financials_api'
    ),

    path(
        "investors/",
        investors_page,
        name="investors_page",
    ),

    path(
    "upload-dashboard/",
    upload_dashboard,
    name="upload_dashboard",
    ),

    path(
        "api/dashboard-documents/",
        dashboard_documents_api,
        name="dashboard_documents_api",
    ),

    path(
    "api/dashboard-statistics/",
    dashboard_statistics_api,
    name="dashboard_statistics_api",
    ),
    
    path(
        "dashboard_login/",
        dashboard_login,
        name="dashboard_login",
        ),

    path(
    "dashboard_logout/",
    dashboard_logout,
    name="dashboard_logout",
    ),

    path(
        "api/upload-investor-document/",
        upload_investor_document,
        name="upload_investor_document",
    ),

    path(
    "api/update-investor-document/",
    update_investor_document,
    name="update_investor_document",
    ),

    path("api/delete-investor-document/", 
         delete_investor_document, 
         name="delete_investor_document"),

    path(
    "api/edit-investor-document/<int:document_id>/<str:section>/",
    edit_investor_document,
    name="edit_investor_document",
    ),

    path(
        "api/download-summary-report/",
        download_summary_report,
        name="download_summary_report",
    ),

    # Employee Management
    path("api/employees/", employees_list_api, name="employees_list_api"),
    path("api/employees/create/", create_employee, name="create_employee"),
    path("api/employees/update/", update_employee, name="update_employee"),
    path("api/employees/toggle-status/", toggle_employee_status, name="toggle_employee_status"),
    path("api/employees/delete/", delete_employee, name="delete_employee"),

    # Password Reset
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="Password_Reset.html",
            email_template_name="password_reset_email.html",
            subject_template_name="password_reset_subject.txt",
            success_url="/password-reset/done/"
        ),
        name="password_reset"
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="password_reset_done.html"
        ),
        name="password_reset_done"
    ),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="password_reset_confirm.html",
            success_url="/password-reset-complete/"
        ),
        name="password_reset_confirm"
    ),
    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="password_reset_complete.html"
        ),
        name="password_reset_complete"
    ),

    path("api/audit-logs/", audit_log_api, name="audit_log_api"),
]

