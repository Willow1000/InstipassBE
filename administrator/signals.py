from django.core.mail import send_mail
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import uuid
from datetime import datetime, timedelta,timezone
from InstiPass.middleware import get_current_request
from logs.models import AdminActionsLog
from institution.models import DemoBooking, ContactUs





@receiver(post_delete,sender=DemoBooking,dispatch_uid="demobooking_deleted")
def delete_demobooking(sender,instance,**kwargs):
    request = get_current_request()
    user = request.user if request else None
    AdminActionsLog.objects.create(
        action = "DELETE",
        admin = user,
        victim_type= "DEMOBOOKING",
        victim = f"{instance.id} {instance.institution} {instance.email} ")

@receiver(post_delete,sender=ContactUs,dispatch_uid='contactus_message_deleted')
def delete_contactus_message(sender,instance,*args,**kwargs):
    request = get_current_request()
    user = request.user if request else None
    AdminActionsLog.objects.create(
        action = "DELETE",
        admin = user,
        victim_type= "CONTACTUSMESSAGE",
        victim = f"{instance.id} {instance.email} ")

