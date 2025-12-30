from django.urls import path
from .views import LeadDetailView

urlpatterns = [
    path("leads/", LeadDetailView.as_view(), name="lead-detail"),
]
