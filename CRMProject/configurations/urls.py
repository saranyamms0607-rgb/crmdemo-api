from django.urls import path
from .views import LeadCSVImportView, LeadCSVExportView

urlpatterns = [
    path("leads/import-csv/", LeadCSVImportView.as_view()),
    path("leads/export-csv/", LeadCSVExportView.as_view()),
]
