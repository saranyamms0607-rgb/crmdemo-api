from django.urls import path
from .views import LeadPerformanceReportView

urlpatterns = [
    path("leads/", LeadPerformanceReportView.as_view(), name="lead-detail"),
    

]
