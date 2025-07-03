import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

def send_hire_email(to_email: str, candidate_name: str):
    message = Mail(
        from_email="oreo57879@gmail.com",  
        to_emails=to_email,
        subject=f"Candidate {candidate_name} Marked as Hire",
        plain_text_content=f"The candidate {candidate_name} has been marked as 'Hire' by FairAI Resume Screening."
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"✅ Email sent to {to_email} with status {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
