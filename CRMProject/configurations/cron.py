from django.utils import timezone
from django.core.mail import send_mail
from datetime import timedelta
from .models import Lead
from CRMProject.settings import EMAIL_HOST_USER

def send_followup_alerts():
    now = timezone.now()

    leads = Lead.objects.filter(is_active=True)

    for lead in leads:
        phones = lead.lead_phones or []

        for phone in phones:
            followup = phone.get("followup_date")
            status = phone.get("status")
            

            # skip invalid
            if not followup:
                continue

            if status not in ["callback", "interested"]:
                continue

            try:
                followup_dt = timezone.make_aware(
                    timezone.datetime.fromisoformat(followup)
                )
            except Exception:
                continue

            #  15 minutes before follow-up
            alert_time = followup_dt - timedelta(minutes=15)

            if alert_time <= now < followup_dt:
                #  SEND EMAIL
                send_mail(
                    subject="Follow-up Reminder (15 mins)",
                    message=f"""
Reminder: Upcoming Follow-up

Lead Name: {lead.lead_name}
Phone: {phone.get('phone')}
Status: {status}
Remarks: {phone.get('remarks', '')}

Follow-up Time: {followup_dt.strftime('%d %b %Y %I:%M %p')}
""",
                    from_email=EMAIL_HOST_USER,
                    recipient_list=[lead.assigned_to.email],
                    fail_silently=False,
                )

                # Mark sent (VERY IMPORTANT)
                phone["email_sent"] = True

        lead.save()
