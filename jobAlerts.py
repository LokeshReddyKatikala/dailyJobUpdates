import requests
import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
API_KEY = os.getenv("RAPID_API_KEY", "bb3a01357dmsh866e9ff85eb7e98p1da509jsn9bc9ffee22f7")
API_HOST = "jsearch.p.rapidapi.com"
BASE_URL = "https://jsearch.p.rapidapi.com/search"

# Email Configuration
EMAIL_USER = os.getenv("EMAIL_USER")      # Your Gmail address
EMAIL_PASS = os.getenv("EMAIL_PASS")      # Your 16-character App Password
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER") # Your personal email

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": API_HOST
}

KEYWORDS = [
    "Software Engineer",
    "Backend Engineer",
    "Full Stack Engineer",
    "SDE",
    "Machine Learning Engineer",
]

LOCATION = "United States"
RESULTS_PER_QUERY = 20


def is_within_last_36_hours(iso_time: str) -> bool:
    posted_time = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    # Using the 48h logic from your snippet to capture the 36h window effectively
    return (now - posted_time) <= timedelta(hours=48)


def fetch_jobs():
    all_jobs = []

    for keyword in KEYWORDS:
        params = {
            "query": keyword,
            "location": LOCATION,
            "page": "1",
            "num_pages": "1",
            "date_posted": "3days", # API-side freshness filter
            "job_requirements": "under_3_years_experience"
        }

        response = requests.get(BASE_URL, headers=HEADERS, params=params)
        response.raise_for_status()

        data = response.json().get("data", [])

        for job in data:
            posted_at = job.get("job_posted_at_datetime_utc")
            if posted_at and is_within_last_36_hours(posted_at):
                all_jobs.append({
                    "title": job.get("job_title"),
                    "company": job.get("employer_name"),
                    "location": job.get("job_city"),
                    "employment_type": job.get("job_employment_type"),
                    "posted_at": posted_at,
                    "link": job.get("job_apply_link"),
                    "description": job.get("job_description", "")[:500]
                })

    return all_jobs


def send_email(jobs):
    if not jobs:
        print("No new jobs found to email.")
        return

    # Formatting the list for the email body
    job_content = f"Found {len(jobs)} jobs posted in the last 36 hours:\n\n"
    for idx, job in enumerate(jobs, 1):
        job_content += f"{idx}. {job['title']} — {job['company']}\n"
        job_content += f"   Location: {job['location']}\n"
        job_content += f"   Link: {job['link']}\n\n"

    msg = MIMEText(job_content)
    msg['Subject'] = f"Daily Job Alert - {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_RECEIVER

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")


if __name__ == "__main__":
    jobs = fetch_jobs()

    # Keep your original print statements for console logging
    print(f"\nFound {len(jobs)} jobs posted in the last 36 hours:\n")

    for idx, job in enumerate(jobs, 1):
        print(f"{idx}. {job['title']} — {job['company']}")
        print(f"   Location: {job['location']}")
        print(f"   Posted: {job['posted_at']}")
        print(f"   Link: {job['link']}\n")
    
    # Trigger the email delivery
    send_email(jobs)
