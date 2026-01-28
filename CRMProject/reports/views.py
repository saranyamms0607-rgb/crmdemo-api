from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from collections import defaultdict
from configurations.models import Lead

class LeadPerformanceReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        report_type = request.GET.get("type")

        qs = Lead.objects.select_related(
            "assigned_to",
            "assigned_to__created_by",
            "assigned_to__role"
        ).filter(is_active=True)

        # ================= DATE FILTERS ================= #
        if report_type == "daily":
            date = request.GET.get("date")
            if date:
                qs = qs.filter(status_updated_at__date=date)

        elif report_type == "weekly":
            week = request.GET.get("week")
            if week:
                year, wk = week.split("-W")
                qs = qs.filter(
                    status_updated_at__year=year,
                    status_updated_at__week=wk
                )

        elif report_type == "monthly":
            month = request.GET.get("month")
            if month:
                year, mon = month.split("-")
                qs = qs.filter(
                    status_updated_at__year=year,
                    status_updated_at__month=mon
                )

        elif report_type == "custom-date":
            qs = qs.filter(
                status_updated_at__date__range=[
                    request.GET.get("from_date"),
                    request.GET.get("to_date")
                ]
            )

        elif report_type == "custom-week":
            fy, fw = request.GET.get("from_week").split("-W")
            ty, tw = request.GET.get("to_week").split("-W")

            qs = qs.filter(
                Q(status_updated_at__year__gt=fy) |
                Q(status_updated_at__year=fy, status_updated_at__week__gte=fw),
                Q(status_updated_at__year__lt=ty) |
                Q(status_updated_at__year=ty, status_updated_at__week__lte=tw)
            )

        elif report_type == "custom-month":
            fy, fm = request.GET.get("from_month").split("-")
            ty, tm = request.GET.get("to_month").split("-")

            qs = qs.filter(
                Q(status_updated_at__year__gt=fy) |
                Q(status_updated_at__year=fy, status_updated_at__month__gte=fm),
                Q(status_updated_at__year__lt=ty) |
                Q(status_updated_at__year=ty, status_updated_at__month__lte=tm)
            )

        qs = qs.order_by("status_updated_at")

        # ================= AGENT REPORT ================= #
        report = defaultdict(lambda: {
            "agent_name": "",
            "email": "",
            "location": "",
            "team_leader": "",
            "new_leads": 0,
            "existing_leads": 0,
            "followup_calls": 0,
            "total_calls": 0,
            "connects": 0,
            "non_connects": 0,
            "followups_today": 0,
            "sales": 0,
            "revenue": 0,
        })

        for lead in qs:
            agent = lead.assigned_to
            if not agent:
                continue

            key = agent.id
            phone_count = len(lead.lead_phones or [])

            report[key]["agent_name"] = agent.get_full_name()
            report[key]["email"] = agent.email
            report[key]["location"] = agent.branch

            if agent.role.name == "AGENT" and agent.created_by:
                report[key]["team_leader"] = agent.created_by.get_full_name()

            report[key]["total_calls"] += phone_count

            if lead.status not in ["unassigned", "assigned"]:
                report[key]["connects"] += phone_count

            if lead.status == "followup":
                report[key]["followup_calls"] += phone_count
                report[key]["followups_today"] += 1

            if lead.status == "assigned":
                report[key]["new_leads"] += 1
            else:
                report[key]["existing_leads"] += 1

            if lead.status == "deal-won":
                report[key]["sales"] += 1
                report[key]["revenue"] += 1  # replace if amount exists

        # ================= FINAL CALC ================= #
        data = []
        for row in report.values():
            tc = row["total_calls"]
            cn = row["connects"]

            row["non_connects"] = tc - cn
            row["connectivity_percent"] = round((cn / tc) * 100, 2) if tc else 0

            total_leads = row["new_leads"] + row["existing_leads"]
            row["productivity_per_head"] = round(cn / total_leads, 2) if total_leads else 0

            data.append(row)

        return Response({
            "status": "success",
            "message": "Lead performance report fetched successfully",
            "data": data
            
        })
