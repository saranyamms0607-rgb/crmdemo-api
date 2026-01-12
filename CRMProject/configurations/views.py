
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
from Authentication.models import LoginUser,LoginRole
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from crmapp.pagination import LeadPagination


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


def normalize_list(value):
        """
        Converts:
        'a,b'                     -> ['a','b']
        '["a","b"]'               -> ['a','b']
        '["a"]'                   -> ['a']
        'a'                       -> ['a']
        None / ''                 -> []
        """
        if not value:
            return []

        value = value.strip()

        # JSON array string
        if value.startswith("[") and value.endswith("]"):
            try:
                parsed = json.loads(value)
                return [str(v).strip() for v in parsed if str(v).strip()]
            except json.JSONDecodeError:
                pass

        # Comma separated
        return [v.strip() for v in value.split(",") if v.strip()]

class LeadCSVImportView(GenericAPIView):
    """
    POST → Import leads from CSV
    """
    
    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            return Response(
                {"status": "error", "message": "CSV file required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not file.name.endswith(".csv"):
            return Response(
                {"status": "error", "message": "Invalid file format. Upload CSV only"},
                status=status.HTTP_400_BAD_REQUEST
            )

        decoded_file = file.read().decode("utf-8")
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)

        created, skipped = 0, 0

        for row in reader:
            name = row.get("name")
            company = row.get("company")
            region = row.get("region")

            phones_raw = row.get("phone")
            emails_raw = row.get("email")

            phone_list = normalize_list(phones_raw)
            email_list = normalize_list(emails_raw)

            if not phone_list:
                skipped += 1
                continue

            # ---------------- PHONES ----------------
            phones = []
            for phone in phone_list:
                if Lead.objects.filter(lead_phones__contains=[{"phone": phone}]).exists():
                    continue
                phones.append({
                    "type": "mobile",
                    "phone": phone,
                    "connected": False
                })

            if not phones:
                skipped += 1
                continue

            # ---------------- EMAILS ----------------
            emails = [
                {"type": "office", "email": email}
                for email in email_list
            ]

            # ---------------- ADDRESS ----------------
            address_data = row.get("address")
            try:
                address_json = json.loads(address_data) if address_data else None
            except json.JSONDecodeError:
                address_json = None

            Lead.objects.create(
                lead_name=name,
                lead_phones=phones,
                lead_emails=emails,
                lead_company=company,
                lead_region=region,
                lead_address=address_json
            )

            created += 1

        return Response(
            {
                "status": "success",
                "message": "CSV import completed",
                "created": created,
                "skipped": skipped
            },
            status=status.HTTP_201_CREATED
        )

class LoginUserListView(GenericAPIView):
    pagination_class = LeadPagination 

    def get(self, request, pk=None):
        try:
            if pk:
                user = get_object_or_404(LoginUser, pk=pk)

                return Response({
                    "status": "success",
                    "message": "User fetched successfully",
                    "data": {
                        "id": user.id,
                        "email": user.email,
                        "phone_no": user.phone_no,
                        "title": user.title,
                        "initial": user.initial,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "role": user.role.id,   # IMPORTANT for edit
                        "is_active": user.is_active,
                    }
                }, status=status.HTTP_200_OK)

            # ✅ QUERYSET
            users = LoginUser.objects.filter(is_active=True).order_by("-id")

            # ✅ PAGINATE
            page = self.paginate_queryset(users)
            if page is not None:
                data = []
                for user in page:
                    data.append({
                        "id": user.id,
                        "email": user.email,
                        "phone_no": user.phone_no,
                        "title": user.title,
                        "initial": user.initial,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "role": user.role.name,
                        "is_active": user.is_active,
                        "created_at": user.created_at
                    })

                return self.get_paginated_response({
                    "message": "Users fetched successfully",
                    "data": data
                })

            # fallback (usually not hit)
            return Response({
                "status": "success",
                "message": "Users fetched successfully",
                "data": []
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": "error",
                "message": "Failed to fetch users",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

   

    def post(self, request):
        try:
            data = request.data

            required_fields = ["email", "password", "first_name", "title", "role"]
            missing_fields = [field for field in required_fields if not data.get(field)]

            if missing_fields:
                return Response(
                    {
                        "status": "error",
                        "message": f"Missing required fields: {', '.join(missing_fields)}",
                        "data": []
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

       
            role_id = data.get("role")
            role = LoginRole.objects.filter(id=role_id).first()


            if not role:
                return Response(
                    {
                        "status": "error",
                        "message": f"Invalid role: {role_id}",
                        "data": []
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = LoginUser.objects.create(
                email=data.get("email"),
                phone_no=data.get("phone_no"),
                title=data.get("title"),
                initial=data.get("initial"),
                first_name=data.get("first_name"),
                last_name=data.get("last_name", ""),
                password=make_password(data.get("password")),
                role=role,
                is_active=data.get("is_active", True),
                is_staff=data.get("is_staff", False),
            )
            

            return Response(
                {
                    "status": "success",
                    "message": "User created successfully",
                    "data": {
                        "id": user.id,
                        "email": user.email,
                        "role": user.role.name
                    }
                },
                status=status.HTTP_201_CREATED
            )

        except IntegrityError:
            return Response(
                {
                    "status": "error",
                    "message": "User with this email already exists",
                    "data": []
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {
                    "status": "error",
                    "message": "Something went wrong",
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        

    def put(self, request, pk):
        try:
            user = get_object_or_404(LoginUser, pk=pk)
            data = request.data

            user.email = data.get("email", user.email)
            user.phone_no = data.get("phone_no", user.phone_no)
            user.title = data.get("title", user.title)
            user.initial = data.get("initial", user.initial)
            user.first_name = data.get("first_name", user.first_name)
            user.last_name = data.get("last_name", user.last_name)
            user.is_active = data.get("is_active", user.is_active)

            role_id = data.get("role")
            if role_id:
                user.role = get_object_or_404(LoginRole, id=role_id)

            if data.get("password"):
                user.password = make_password(data.get("password"))

            user.save()

            return Response({
                "status": "success",
                "message": "User updated successfully",
                "data": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role.name
                }
            }, status=status.HTTP_200_OK)

        except LoginRole.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Invalid role selected",
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": "error",
                "message": "Failed to update user",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            user = get_object_or_404(LoginUser, pk=pk)
            user.is_active = False
            user.save()

            return Response({
                "status": "success",
                "message": "User deleted successfully",
                "data": []
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": "error",
                "message": "Failed to delete user",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

