import csv
import random

first_names = [
    "Arjun", "Priya", "Rahul", "Sneha", "Amit", "Neha", "Karthik",
    "Ananya", "Rohit", "Pooja", "Vikram", "Divya", "Suresh", "Meera"
]

last_names = [
    "Sharma", "Verma", "Iyer", "Reddy", "Gupta", "Patel",
    "Mehta", "Nair", "Kapoor", "Malhotra"
]

companies = [
    "TechNova", "InnoSoft", "MediaMatic", "NextGen Corp",
    "Cloudify", "DataWave", "PixelWorks", "GrowthLabs"
]

regions = ["North", "South", "East", "West"]

used_phones = set()
used_names = set()

def generate_unique_phone():
    while True:
        phone = f"+91{random.randint(6000000000, 9999999999)}"
        if phone not in used_phones:
            used_phones.add(phone)
            return phone

def generate_unique_name():
    while True:
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        if name not in used_names:
            used_names.add(name)
            return name

rows = []

for i in range(1, 101):
    name = generate_unique_name()

    rows.append({
        "id": i,
        "name": name,
        "email": f"{name.lower().replace(' ', '.')}{i}@example.com",
        "phone": generate_unique_phone(),
        "company": random.choice(companies),
        "region": random.choice(regions)
    })

# Write CSV
with open("crm_test_data_clean.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=["id", "name", "email", "phone", "company", "region"]
    )
    writer.writeheader()
    writer.writerows(rows)

print("✅ 100 UNIQUE CRM records generated → crm_test_data_clean.csv")
