
import csv
import re
from django.http import HttpResponse
from rest_framework.generics import GenericAPIView
from .models import Lead
import io
import json
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import AllowAny


class LeadCSVExportView(GenericAPIView):
    """
    GET → Export leads as CSV
    """
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        filename = request.GET.get("filename", "leads")

        # Sanitize filename (important for security)
        filename = re.sub(r'[^a-zA-Z0-9_-]', '', filename)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="{filename}.csv"'
        )

        writer = csv.writer(response)

        # CSV Header
        writer.writerow([
            "id",
            "lead_name",
            "lead_email",
            "lead_phone",
            "lead_company",
            "lead_region",
            "lead_address",
            # "status",
        ])

        for lead in Lead.objects.all():
            writer.writerow([
                lead.id,
                lead.lead_name,
                lead.lead_email,
                lead.lead_phone,
                lead.lead_company,
                lead.lead_region,
                lead.lead_address,
                # lead.status,
            ])

        return response



class LeadCSVImportView(GenericAPIView):
    """
    POST → Import leads from CSV
    """

    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            return HttpResponse(
                json.dumps({
                    "status": "error",
                    "message": "CSV file required"
                }),
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST
            )

        if not file.name.endswith(".csv"):
            return HttpResponse(
                json.dumps({
                    "status": "error",
                    "message": "Invalid file format. Upload CSV only"
                }),
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST
            )

        decoded_file = file.read().decode("utf-8")
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)

        created, skipped = 0, 0

        for row in reader:
            name = row.get("lead_name")
            phone = row.get("lead_phone")
            company = row.get("lead_company")

            if not phone:
                skipped += 1
                continue

            #  Skip if phone number already exists
            if Lead.objects.filter(lead_phone=phone).exists():
                skipped += 1
                continue

            # Skip if name + phone + company already exists
            if Lead.objects.filter(
                lead_name=name,
                lead_phone=phone,
                lead_company=company
            ).exists():
                skipped += 1
                continue

            # Parse JSON address safely
            address_data = row.get("lead_address")
            try:
                address_json = json.loads(address_data) if address_data else None
            except json.JSONDecodeError:
                address_json = None

            Lead.objects.create(
                lead_name=name,
                lead_email=row.get("lead_email"),
                lead_phone=phone,
                lead_company=company,
                lead_region=row.get("lead_region"),
                lead_address=address_json
            )

            created += 1

        return HttpResponse(
            json.dumps({
                "status": "success",
                "message": "CSV import completed",
                "created": created,
                "skipped": skipped
            }),
            content_type="application/json",
            status=status.HTTP_201_CREATED
        )


