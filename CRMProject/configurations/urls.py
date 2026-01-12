from django.urls import path
from .views import LeadCSVImportView, LeadCSVExportView,LoginUserListView

urlpatterns = [
    path("leads/import-csv/", LeadCSVImportView.as_view()),
    path("leads/export-csv/", LeadCSVExportView.as_view()),

    path("users/", LoginUserListView.as_view()),
    path("users/<int:pk>/", LoginUserListView.as_view()),
]
