import json
from urllib import request
from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from .pagination import LeadPagination
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated


from configurations.models import Lead, STATUS_CHOICES

# Create your views here.
class LeadDetailView(GenericAPIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]
    pagination_class = LeadPagination

    def get(self, request):
        status_filter = request.GET.get("status")

        leads = Lead.objects.filter(is_active=True)

        if status_filter:
            leads = leads.filter(status=status_filter)

        paginator = self.pagination_class()
        paginated_leads = paginator.paginate_queryset(leads, request)

        if not paginated_leads:
            return HttpResponse(
                json.dumps({
                    "status": "success",
                    "message": "No leads found",
                    "count": 0,
                    "data": []
                }),
                content_type="application/json",
                status=status.HTTP_200_OK
            )

        data = [
            {
                "id": lead.id,
                "lead_name": lead.lead_name,
                "lead_email": lead.lead_email,
                "lead_phone": lead.lead_phone,
                "lead_company": lead.lead_company,
                "lead_region": lead.lead_region,
                "lead_address": lead.lead_address,
                "status": lead.status,
            }
            for lead in paginated_leads
        ]

        return paginator.get_paginated_response({
            "status": "success",
            "message": "Leads retrieved successfully",
            "data": data
        })
