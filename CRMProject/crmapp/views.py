import json
import re
from django.http import HttpResponse
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .pagination import LeadPagination
from rest_framework_simplejwt.authentication import JWTAuthentication
from Authentication.models import LoginUser
from django.db.models import Q ,Value, CharField, Count,F
from django.utils import timezone
from datetime import timedelta
from django.utils.dateparse import parse_datetime
from django.db.models import Min
from django.db.models.functions import Replace
from configurations.models import Lead
from rest_framework import status
from rest_framework import status as sts
from django.db.models.functions import Cast

class LeadDetailView(GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = LeadPagination
    permission_classes = [AllowAny]

    def get(self, request, pk=None):
        user_email = request.user.email
        user = LoginUser.objects.get(email=user_email)
        role = user.role.name

        

        if pk:
            # GET single lead
            try:
                lead = Lead.objects.select_related("assigned_to").only(
                    "id",
                    "lead_name",
                    "lead_emails",
                    "lead_phones",
                    "lead_company",
                    "lead_region",
                    "lead_address",
                    "status","remarks",
                    "assigned_to__title",
                    "assigned_to__first_name",
                    "assigned_to__last_name",
                ).get(id=pk, is_active=True)
                # get all lead ids of same company (ordered)
                company_lead_ids = list(
                    Lead.objects.filter(
                        is_active=True,
                        lead_company=lead.lead_company,
                        status =lead.status
                    )
                    .order_by("id")
                    .values_list("id", flat=True)
                )

                # remove current lead id
                related_leads = [i for i in company_lead_ids if i != lead.id]

                data = {
                "id": lead.id,
                "lead_name": lead.lead_name,
                "lead_company": lead.lead_company,
                "lead_region": lead.lead_region,
                "lead_address": lead.lead_address,

                "lead_emails": lead.lead_emails or [],
                "lead_phones": lead.lead_phones or [],
                "remarks":lead.remarks,
                "status": lead.status,
                "assigned_to": (
                    f"{lead.assigned_to.title} "
                    f"{lead.assigned_to.first_name} "
                    f"{lead.assigned_to.last_name}"
                    if lead.assigned_to else None
                ),
            }
                CALL_STATUS_FLOW = [
                    ("voicemail", "No Contact"),
                    ("callback", "Callback Requested"),
                    ("interested", "Interested"),
                    ("prospect", "Prospect"),
                    ("not-interested", "Not Interested"),
                    ("dnd", "DND"),
                ]

                tracking_data = []

                stored = lead.status_tracking or {}

                for key, label in CALL_STATUS_FLOW:
                    item = stored.get(key, {})

                    tracking_data.append({
                        "status": key,
                        "label": label,
                        "date": item.get("date"),
                        "remarks": item.get("remarks"),
                    })
                return Response(
                    {"status": "success",  "message": "Lead retrieved successfully",
                     "data": data,"tracking":tracking_data,"related_leads": related_leads},
                    status=status.HTTP_200_OK
                )

            except Lead.DoesNotExist:
                return Response(
                    {"error": "Lead not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        status_filter = request.GET.get("status")
        search = request.GET.get("search")
        name = request.GET.get("name")
        company = request.GET.get("company")
        region = request.GET.get("region")
        today = request.GET.get("today")
        today_date = now().date()

        # Base queryset
        if role == "AGENT":

            leads = Lead.objects.filter(
                assigned_to=user,
                is_active=True
            )
        else:
            leads = Lead.objects.filter(is_active=True)

        if status_filter:
            leads = leads.filter(status=status_filter)
        if search:
            #  normalize search input
            search_normalized = re.sub(r'[^0-9xX]', '', search)

            leads = leads.annotate(
                phones_text=Cast('lead_phones', CharField()),
            ).annotate(
                phones_clean=Replace(
                    Replace(
                        Replace(
                            Replace(
                                Replace(
                                    'phones_text',
                                    Value('-'), Value('')
                                ),
                                Value('('), Value('')
                            ),
                            Value(')'), Value('')
                        ),
                        Value(' '), Value('')
                    ),
                    Value('"'), Value('')
                )
            ).filter(
                Q(lead_name__icontains=search) |
                Q(lead_company__icontains=search) |
                Q(lead_region__icontains=search) |
                Q(phones_clean__icontains=search_normalized)
            )

        if search: 
            leads = leads.filter( 
                Q(lead_name__icontains=search) |
                  # Q(lead_emails__icontains=search) |
                  #  Q(lead_phones__icontains=search) |
                   Q(lead_company__icontains=search) |
                   Q(lead_region__icontains=search) )
        if name:
            leads = leads.filter(lead_name__icontains=name)

        if company:
            leads = leads.filter(lead_company__icontains=company)

        if region:
            leads = leads.filter(lead_region__icontains=region)
        
        if today=="true":
            today_filtered_leads = []

            for lead in leads:
                phones = lead.lead_phones or []
                match_today = False

                for phone in phones:
                    followup_dt = phone.get("followup_date")
                    status_val = phone.get("status")

                    if not followup_dt or status_val not in ("callback", "followup"):
                        continue

                    try:
                        if isinstance(followup_dt, str):
                            dt = parse_datetime(followup_dt)
                        else:
                            dt = followup_dt

                        if dt and dt.date() == today_date:
                            match_today = True
                            break

                    except Exception:
                        continue

                if match_today:
                    today_filtered_leads.append(lead.id)

            today_ids = today_filtered_leads
            leads = leads.filter(id__in=today_ids)


        from django.db.models import OuterRef, Subquery

        # Subquery: get FIRST lead id per company+status
        first_lead_subquery = (
            Lead.objects
            .filter(
                lead_company=OuterRef("lead_company"),
                status=OuterRef("status"),
                is_active=True,
            )
            .order_by("id")
            .values("id")[:1]
        )

        # Apply to already filtered queryset
        leads = (
            leads
            .annotate(first_id=Subquery(first_lead_subquery))
            .filter(id=F("first_id"))
        )

        leads = leads.order_by("lead_company", "id").select_related(
            "assigned_to"
        ).only(
            "id",
            "lead_name",
            "lead_emails",
            "lead_phones",
            "lead_company",
            "lead_region",
            "lead_address",
            "status",
            "remarks",
            "assigned_to__title",
            "assigned_to__first_name",
            "assigned_to__last_name",
        )
        

       

        #  PAGINATION STARTS HERE
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(leads, request)

        data = [
            {
                "id": lead.id,
                "lead_name": lead.lead_name,
                "lead_emails": lead.lead_emails,
                "lead_phones": lead.lead_phones,
                "lead_company": lead.lead_company,
                "lead_region": lead.lead_region,
                "lead_address": lead.lead_address,
                "status": lead.status,
                "remarks": lead.remarks,
                "assigned_to": (
                    f"{lead.assigned_to.title} "
                    f"{lead.assigned_to.first_name} "
                    f"{lead.assigned_to.last_name}"
                    if lead.assigned_to else None
                ),
            }
            for lead in page
        ]

        return paginator.get_paginated_response({
            "message": "Lead fetched successfully",
            "data": data,
            "assigned_to": {
                "user_id": user.id
            }
        })



    def post(self, request):
        lead_id = request.data.get("lead_id")
        lead_ids = request.data.get("lead_ids")  #  NEW
        agent_id = request.data.get("agent_id")

        if not agent_id or (not lead_id and not lead_ids):
            return Response(
                {
                    "status": "Fail",
                    "message": "agent_id and lead_id or lead_ids are required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            agent = LoginUser.objects.get(
                id=agent_id,
                is_active=True,
                role__name="AGENT"
            )

            #  BULK ASSIGN
            if lead_ids:
                leads = Lead.objects.filter(
                    id__in=lead_ids,
                    is_active=True
                )

                if not leads.exists():
                    return Response(
                        {
                            "status": "Fail",
                            "message": "No valid leads found"
                        },
                        status=status.HTTP_404_NOT_FOUND
                    )

                # 🔥 IMPORTANT FIX (evaluate queryset first)
                companies = list(
                    leads.values_list("lead_company", flat=True)
                )

                # 🔥 Now safe to update
                all_company_leads = Lead.objects.filter(
                    lead_company__in=companies,
                    is_active=True
                )

                count = all_company_leads.count()

                all_company_leads.update(
                    assigned_to=agent,
                    status="assigned"
                )

                return Response(
                    {
                        "status": "success",
                        "message": f"{count} leads assigned successfully"
                    },
                    status=status.HTTP_200_OK
                )

            # SINGLE ASSIGN (OLD FLOW)
            lead = Lead.objects.get(id=lead_id, is_active=True)

            company = lead.lead_company  #  evaluate first

            Lead.objects.filter(
                lead_company=company,
                is_active=True
            ).update(
                assigned_to=agent,
                status="assigned"
            )



            return Response(
                {
                    "status": "success",
                    "message": "Lead assigned successfully"
                },
                status=status.HTTP_200_OK
            )

        except Lead.DoesNotExist:
            return Response(
                 {
                    "status": "Fail",
                    "message": "Lead not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        except LoginUser.DoesNotExist:
            return Response(
                {
                    "status": "Fail",
                    "message": "Invalid agent"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
        
    def put(self, request, pk=None):
        try:
            lead = Lead.objects.get(id=pk, is_active=True)
        except Lead.DoesNotExist:
            return Response(
                {"error": "Lead not found"},
                status=sts.HTTP_404_NOT_FOUND
            )
        # ===== STORE OLD PHONE DATA (FOR CALL COUNT) =====
        old_phones = lead.lead_phones or []

        old_phone_map = {
            p.get("phone"): p
            for p in old_phones
            if isinstance(p, dict) and p.get("phone")
    }

        # ================= RAW DATA =================
        raw_emails = request.data.get("lead_emails")
        raw_phones = request.data.get("lead_phones")
        raw_address = request.data.get("lead_address")
        general_remarks = request.data.get("remarks", "")

        # ================= SAVE RAW AS-IS =================
        if raw_emails is not None:
            lead.lead_emails = raw_emails

        if raw_phones is not None:
            lead.lead_phones = raw_phones

        if raw_address is not None:
            lead.lead_address = raw_address

        phones = raw_phones or []

        # ================= VALIDATION =================
        for phone in phones:
            if not isinstance(phone, dict):
                continue
            phone.setdefault("call_count", 0)
            phone_no = phone.get("phone")
            new_status = phone.get("status")
            print(phone["call_count"],"1") 
            if not phone_no or not new_status:
                phone["call_count"] = phone.get("call_count", 0)
                continue

            #  Do NOT increment for voicemail
            if new_status == "voicemail":
                phone["call_count"] = phone.get("call_count", 0)
                continue

            old_phone = old_phone_map.get(phone_no)
            old_status = old_phone.get("status") if isinstance(old_phone, dict) else None

            #  STATUS CHANGED → increment
            if old_status != new_status:
                phone["call_count"] = phone.get("call_count", 0) + 1
            else:
                phone["call_count"] = phone.get("call_count", 0)
            print(phone["call_count"],"2") 
                


        lead.remarks = general_remarks

        # ================= STATUS TRACKING =================
        tracking = lead.status_tracking or {}

        # --------- Voicemail control ---------
        voicemail_tracking = tracking.get("voicemail") or {}

        voicemail_count = voicemail_tracking.get("count", 0)
        voicemail_dt = voicemail_tracking.get("datetime") or voicemail_tracking.get("date")


        if voicemail_dt:
            last_voicemail_time = parse_datetime(voicemail_dt)

            if last_voicemail_time and timezone.is_naive(last_voicemail_time):
                last_voicemail_time = timezone.make_aware(last_voicemail_time)
        else:
            last_voicemail_time = None


        # ================= EXTRACT STATUSES =================
        phone_statuses = []
        for phone in phones:
            if phone.get("status"):
                phone_statuses.append(phone.get("status"))

        # ================= STATUS CALCULATION =================
        new_status = lead.status  # fallback
         
        if phones and all(phone.get("status") == "dnd" for phone in phones):
            new_status = "dnd"

        elif "callback" in phone_statuses:
            new_status = "followup"

        elif "interested" in phone_statuses:
            new_status = "deal-won"

        elif "prospect" in phone_statuses:
            new_status = "prospect"

        elif "not-interested" in phone_statuses:
            new_status = "deal-lost"

        elif phones and all(phone.get("status") == "voicemail" for phone in phones):

            #  Enforce 24 hour rule
            if last_voicemail_time:
                diff = timezone.now() - last_voicemail_time
                if diff < timedelta(hours=24):
                    return Response(
                        {
                            "status": "Fail",
                            "message": "You can mark voicemail again only after 24 hours"
                        },
                        status=sts.HTTP_400_BAD_REQUEST
                    )

            #  Move attempts ONLY when all are voicemail
            if voicemail_count == 0:
                new_status = "second-attempt"
            elif voicemail_count == 1:
                new_status = "third-attempt"
            else:
                new_status = "completed"

            # update voicemail tracking
            tracking["voicemail"] = {
                "datetime": timezone.now().isoformat(),
                "count": voicemail_count + 1
            }

        # ================= TRACK EACH STATUS =================
        for phone in phones:
            status = phone.get("status")
            remarks = phone.get("remarks", "")

            if status and status != "voicemail":
                tracking[status] = {
                    "date": timezone.now().date().isoformat(),
                    "remarks": remarks
                }

        # ensure overall status tracked
        if new_status not in tracking:
            tracking[new_status] = {
                "date": timezone.now().date().isoformat(),
                "remarks": general_remarks
            }

        # ================= SAVE =================
        lead.status = new_status
        lead.status_tracking = tracking
        lead.status_updated_at = timezone.now()
        lead.save()

        return HttpResponse(
            json.dumps({
                "status": "success",
                "message": "Lead updated successfully",
                "lead_status": new_status,
                "tracking": tracking
            }),
            content_type="application/json",
            status=sts.HTTP_200_OK
        )

class LeadGetView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    def post(self, request):
        user = request.user

        # 1 Check if user already has assigned lead
        existing_lead = Lead.objects.filter(
            assigned_to=user,
            status="assigned",
            is_active=True
        ).first()

        if existing_lead:
            return Response({
                "already_assigned": True,
                 "status":"Fail",
                 "message":"You already have an active lead"
            }, status=status.HTTP_200_OK)

        # 2 Get new unassigned lead
        lead = Lead.objects.filter(
            status="unassigned",
            is_active=True
        ).first()

        if not lead:
            return Response(
                {
                    "status":"Fail","message": "No leads available"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 3 Assign lead
        lead.status = "assigned"
        lead.assigned_to = user
        lead.save()
        return Response({
            "already_assigned": False,
            "status":"success",
            "message": "Leads assigned successfully"
            
        }, status=status.HTTP_200_OK)
    

from django.utils.timezone import now
from datetime import datetime

class LeadCountView(GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]

    def get(self, request):
        user = request.user
        today = now().date()
        

        # TOTAL LEADS
        total_leads = Lead.objects.filter(
            assigned_to=user,
            is_active=True
        ).count()
       
        leads = Lead.objects.filter(
            assigned_to=user,
            is_active=True
        )

        # TOTAL CALLS
        total_calls = 0

        for lead in leads:
            for phone in lead.lead_phones or []:
                if not isinstance(phone, dict):
                    continue
                # if phone.get("status"):
                #     total_calls += 1
                total_calls += int(phone.get("call_count", 0))
                
        # TODAY FOLLOWUPS
        
        today_followups = 0

        for lead in leads:
            for item in lead.lead_phones or []:
                followup_dt = item.get("followup_date")
                status_val = item.get("status")

                if status_val not in ("followup", "callback") or not followup_dt:
                    continue

                try:
                    # print("LEAD ID:", lead.id)
                    if isinstance(followup_dt, datetime):
                        dt = followup_dt

                    elif isinstance(followup_dt, str):
                        dt = datetime.fromisoformat(followup_dt.replace(" ", "T"))

                    else:
                        continue


                    # STRICT date comparison
                    if dt.date() == today:
                        today_followups += 1
                        break   # count ONE per lead only

                except Exception as e:
                    print("INVALID FOLLOWUP:", followup_dt, e)
                    continue


        # if user.role.id != "AGENT":
        #     total_leads = Lead.objects.filter(is_active=True).count()
        #     today_followups = Lead.objects.filter(
        #         is_active=True,
        #         followup_date=today
        #     ).count()

        return Response({
            "total_leads": total_leads,
            "total_calls": total_calls,
            "today_followups": today_followups
        }, status=status.HTTP_200_OK)

        