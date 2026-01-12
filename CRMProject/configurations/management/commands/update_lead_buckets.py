from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from configurations.models import Lead

class Command(BaseCommand):
    help = "Auto-update lead buckets based on phone status and last contact"

    def handle(self, *args, **kwargs):
        now = timezone.now()
        leads = Lead.objects.filter(is_active=True, status__in=["assigned","second_attempt","third_attempt"])

        for lead in leads:
            if not lead.status_updated_at:
                continue

            elapsed = now - lead.status_updated_at
            phones = lead.lead_phones or []

            statuses = [p.get("status") for p in phones]

            # Priority-based rules
            if "dnd" in statuses:
                lead.status = "dnd"
            elif "not_interested" in statuses:
                lead.status = "deal_lost"
            elif "prospect" in statuses:
                lead.status  = "prospect"    
            elif "interested" in statuses:
                lead.status = "deal_won"
            elif "callback" in statuses:
                lead.status = "followup"
            elif all(s=="not_connected" for s in statuses):
                # Increment attempts based on elapsed time
                if lead.status == "assigned" and elapsed >= timedelta(hours=24):
                    lead.status = "second_attempt"
                elif lead.status == "second_attempt" and elapsed >= timedelta(hours=48):
                    lead.status = "third_attempt"
                elif lead.status == "third_attempt" and elapsed >= timedelta(hours=72):
                    lead.status = "completed"

            lead.save(update_fields=["status"])
            self.stdout.write(f"Lead {lead.id} updated to {lead.status}")
