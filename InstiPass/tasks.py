from celery import shared_task
from django.core.mail import send_mail
import os
import json
from dotenv import load_dotenv
import requests
import base64


load_dotenv()

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

sms_leopard_url = "https://api.smsleopard.com/v1/sms/send"
SMS_LEOPARD_API_KEY = os.getenv("SMS_LEOPARD_API_KEY")
SMS_LEOPARD_API_SECRET = os.getenv("SMS_LEOPARD_API_SECRET")
# WHATSAPP_API_URL = f"https://graph.facebook.com/v20.0/{WHATASPP_PHONE_NUMBER_ID}/messages"

# WHATSAPP_HEADERS = {
#     "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
#     "Content-Type": "application/json"
# }

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 30}
)
def send_email(self, *, plain_message, receiver, html_message, subject):
    try:
        if type(receiver) == str:
            receiver = [receiver]

        # If receiver is a string that *looks* like a list, convert it
        # if isinstance(receiver, str):
        #     if receiver.startswith("[") and receiver.endswith("]"):
        #         receiver = literal_eval(receiver)  # safely parse into list
        #     else:
        #         receiver = [receiver]  # wrap single email in a list


        # # Ensure it's a list of strings
        # if not isinstance(receiver, list):
        #     receiver = [str(receiver)]


        send_mail (

            subject=subject,
            message=plain_message,
            from_email="notifications@instipass.com",
            recipient_list=receiver,
            html_message=html_message,
            fail_silently=False
        )
    except Exception as exc:

        raise self.retry(exc=exc, countdown=60)



 # From Meta App

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 30}
)
def send_whatsapp_message(self,to_number: str, template: str, variables: list = None):
    url = f"https://graph.facebook.com/v22.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"

    if variables is None:
        variables = []

    # Build parameters in order
    parameters = [{"type": "text", "text": str(v)} for v in variables]

    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "template",
        "template": {
            "name": template,  # must match template name in BM
            "language": {"code": "en"},
            "components": [
                {
                    "type": "body",
                    "parameters": parameters
                }
            ]
        }
    }

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload)
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        print("Error:", response.status_code, response.text)

    response.raise_for_status()
    return response.json()


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 30}
)
def send_sms(self,recipients,message,multi):
    credentials = f"{SMS_LEOPARD_API_KEY}:{SMS_LEOPARD_API_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    if multi:
        # Build destination with same message for each number
        destination = [{"number": num, "message": message} for num in recipients]

        body = {
            "source": "InstipassDemo",
            "multi": True,
            "message": message,
            "destination": destination,
            "status_url": "",
            "status_secret": ""
        }
    else:
        body = {
            "source": "InstipassDemo",
            "message": message,
            "destination": [{"number": recipients}],
            "status_url": "",
            "status_secret": ""
        }

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json"
    }
    response = requests.post(sms_leopard_url, headers=headers, data=json.dumps(body))

    if response.status_code == 200:
        print("SMS sent successfully:")
        print(response.json())
    else:
        print(f"Failed to send SMS. Status code: {response.status_code}")
        print(response.text)
    







    




   
