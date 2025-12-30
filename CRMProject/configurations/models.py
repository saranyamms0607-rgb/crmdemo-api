
from django.db import models
STATUS_CHOICES = [
        ("unassigned", "Unassigned"),
        ("assigned", "Assigned"),
        ("second-attempt", "Second Attempt"),
        ("third-attempt", "Third Attempt"),
        ("completed", "Completed"),
        ("followup", "Follow Up"),
        ("deal-won", "Deal Won"),
        ("deal-lost", "Deal Lost"),
        ("dnd", "Do Not Disturb"),
        ("prospect", "Prospect"),
    ]
class Lead(models.Model):
    lead_name = models.CharField( max_length=150)

    lead_email = models.EmailField( max_length=255, blank=True, null=True)

    lead_phone = models.CharField(max_length=15,unique=True)

    lead_company = models.CharField(max_length=150,blank=True, null=True)

    lead_region = models.CharField(max_length=100,blank=True, null=True)

    lead_address = models.JSONField( blank=True, null=True)


    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="unassigned"
    )

    is_active = models.BooleanField(default=True)


    def __str__(self):
        return f"{self.lead_name} - {self.lead_company}- {self.lead_region}"
