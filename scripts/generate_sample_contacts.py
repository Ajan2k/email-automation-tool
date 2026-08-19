"""Generate a sample contacts CSV for testing the import flow.

Usage: python scripts/generate_sample_contacts.py [count] > contacts.csv
"""
import random
import sys

FIRST = ["Sarah", "John", "Mike", "Priya", "Elena", "Tom", "Aisha", "Carlos", "Yuki", "Lena"]
LAST = ["Chen", "Doe", "Patel", "Garcia", "Kim", "Novak", "Okafor", "Silva", "Tanaka", "Weber"]
COMPANIES = ["ABC AI", "XYZ Labs", "Nimbus Data", "QuantumSoft", "Vertex ML", "DeepFlow", "Synthia", "CloudPeak"]
TITLES = ["CTO", "Founder", "Head of AI", "ML Engineer", "VP Engineering", "Product Manager"]
INDUSTRIES = ["Artificial Intelligence", "SaaS", "Fintech", "Healthcare", "E-commerce"]


def main(count: int) -> None:
    print("first_name,last_name,email,company,job_title,website,linkedin,industry")
    seen = set()
    i = 0
    while len(seen) < count:
        first, last = random.choice(FIRST), random.choice(LAST)
        company = random.choice(COMPANIES)
        domain = company.lower().replace(" ", "")
        email = f"{first.lower()}.{last.lower()}{i}@{domain}.example.com"
        if email in seen:
            i += 1
            continue
        seen.add(email)
        i += 1
        print(
            f"{first},{last},{email},{company},{random.choice(TITLES)},"
            f"https://{domain}.example.com,https://linkedin.com/in/{first.lower()}{last.lower()},"
            f"{random.choice(INDUSTRIES)}"
        )


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 100)
