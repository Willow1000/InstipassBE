# utils/send_email.py

from django.template.loader import render_to_string
import resend
import os

resend.api_key = os.getenv("RESEND_API_KEY")

def send_email(to, subject, template_name, context=None, from_email="noreply@yourdomain.com"):
    html = render_to_string(template_name, context or {})
    
    params: resend.Emails.SendParams = {
        "from": from_email,
        "to": to,
        "subject": subject,
        "html": html,
    }

    try:
        response = resend.Emails.send(params)
        
        # If it has an 'id', it's successful
        if response.get("id"):
            return response
        else:
            print(f"Failed to send email. Resend response: {response}")
            return None

    except Exception as e:
        print(f"Exception while sending email to {to}: {e}")
        return None
