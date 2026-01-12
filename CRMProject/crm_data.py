import csv
import json
import random
from faker import Faker

fake = Faker()

STATUS_CHOICES = [
    "unassigned",
    "assigned",
    "second-attempt",
    "third-attempt",
    "completed",
    "followup",
    "deal-won",
    "deal-lost",
    "dnd",
    "prospect",
]

COUNT = 1000
OUTPUT_FILE = "dummy_leads.csv"

fieldnames = [
    "name",
    "email",
    "phone",
    "company",
    "region",
    "address",
    "status",
    "is_active",
]

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for _ in range(COUNT):
        emails = [
            fake.email(),
            fake.company_email(),
        ]

        phones = [
            fake.phone_number(),
            fake.phone_number(),
        ]

        address = {
            "street": fake.street_address(),
            "city": fake.city(),
            "state": fake.state(),
            "country": fake.country(),
            "pincode": fake.postcode(),
        }

        writer.writerow({
            "name": fake.name(),
            "email": json.dumps(emails),
            "phone": json.dumps(phones),
            "company": fake.company(),
            "region": fake.state(),
            "address": json.dumps(address),
            "status": random.choice(STATUS_CHOICES),
            "is_active": random.choice([True, False]),
        })

print(f"✅ Successfully generated {COUNT} records in {OUTPUT_FILE}")
