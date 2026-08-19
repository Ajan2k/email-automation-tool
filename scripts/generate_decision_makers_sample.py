"""Generate a Decision_Makers-style sample .xlsx for testing the import flow.

Reproduces the real file's quirks: all-lowercase names, work_email missing in
~44% of rows, `emails` as semicolon lists, mobile_phone as float, sparse
phones/skills, semicolon-separated countries.

Usage: python scripts/generate_decision_makers_sample.py [count] [outfile]
"""
import random
import sys

try:
    from openpyxl import Workbook
except ImportError:
    sys.exit("openpyxl required: pip install openpyxl (or use backend/.venv)")

COLUMNS = [
    "emails", "countries", "first_name", "full_name", "gender", "industry",
    "job_company_name", "job_company_size", "job_company_website", "job_title",
    "linkedin_connections", "linkedin_url", "linkedin_username",
    "location_country", "mobile_phone", "phone_numbers", "skills", "work_email",
]

FIRST = ["magued", "sarah", "john", "priya", "elena", "tom", "aisha", "carlos", "yuki", "lena"]
LAST = ["rayes", "chen", "doe", "patel", "garcia", "kim", "novak", "okafor", "silva", "tanaka"]
COMPANIES = ["moneris", "cibc", "scotiabank", "telus", "rbc", "manulife", "shopify", "university of toronto"]
TITLES = ["vice president", "director", "partner", "chief technology officer", "head of ai", "svp engineering"]
INDUSTRIES = ["financial services", "banking", "higher education", "telecommunications", "insurance"]
SIZES = ["1001-5000", "5001-10000", "10001+"]
COUNTRIES = ["canada", "united states", "canada", "canada", "united kingdom"]
SKILLS = ["finance", "portfolio management", "mergers and acquisitions", "leadership",
          "risk management", "machine learning", "strategy", "cloud computing"]


def main(count: int, outfile: str) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Decision Makers"
    ws.append(COLUMNS)

    for i in range(count):
        first, last = random.choice(FIRST), random.choice(LAST)
        company = random.choice(COMPANIES)
        domain = company.replace(" ", "") + ".com"
        slug = f"{first}-{last}-{random.randint(10000000, 99999999):x}"
        country = random.choice(COUNTRIES)
        work = f"{first}.{last}{i}@{domain}"
        personal = f"{first}{last}{i}@gmail.com"

        has_work = random.random() < 0.56          # 56.4% fill rate
        emails = ";".join([work, personal]) if random.random() < 0.5 else work
        if random.random() < 0.02:                  # 2.1% missing emails
            emails = None

        ws.append([
            emails,
            country if random.random() < 0.9 else f"{country};{random.choice(COUNTRIES)}",
            first,
            f"{first} {last}",
            random.choice(["male", "female", None, "male", "female"]),  # ~16% missing
            random.choice(INDUSTRIES) if random.random() < 0.985 else None,
            company,
            random.choice(SIZES),
            domain if random.random() < 0.914 else None,
            random.choice(TITLES),
            float(random.randint(50, 500)) if random.random() < 0.99 else None,
            f"linkedin.com/in/{slug}",
            slug,
            country,
            float(f"1416{random.randint(1000000, 9999999)}") if random.random() < 0.061 else None,
            f"+1416{random.randint(1000000, 9999999)}" if random.random() < 0.12 else None,
            ";".join(random.sample(SKILLS, k=random.randint(2, 5))) if random.random() < 0.76 else None,
            work if has_work else None,
        ])

    wb.save(outfile)
    print(f"Wrote {count} rows to {outfile}")


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    outfile = sys.argv[2] if len(sys.argv) > 2 else "Decision_Makers_sample.xlsx"
    main(count, outfile)
