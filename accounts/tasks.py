from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_email(plain_message,receiver,html_message,subject):
    send_mail(
        subject=subject,
        message=plain_message,
        from_email="notifications@instipass.com",
        recipient_list=rec[receiver],
        html_message=html_message,
        fail_silently=False
    )


