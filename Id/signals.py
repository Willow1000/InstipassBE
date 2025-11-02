from django.dispatch import receiver
from student.models import *
from django.core.mail import send_mail
from .models import IdInProcess,IdReady
from django.db.models.signals import post_save
from logs.models import IdprogressLog
from django.utils.timezone import now
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.timezone import now
import uuid
from datetime import datetime, timedelta

@receiver(post_save,sender=IdReady,dispatch_uid='delete_once_id_ready')
def delete_in_process_once_ready(sender,instance,created,*args,**kwargs):
    record = IdInProcess.objects.filter(Id = instance.Id)
    if record:
        record.delete()
    else:
        print("Record not found")    
    
@receiver(post_save,sender=IdInProcess,dispatch_uid = 'notify_student_and_update_process_status')
def send_id_processing_update(sender,instance,created,**kwargs):
    student = instance.Id.student
    student.status = "id_processing"
    student.save()

   
    
@receiver(post_save,sender=IdReady,dispatch_uid = 'notify_student_and_update_ready_status')
def send_id_ready_notification(sender,instance,created, **kwargs):
    student = instance.Id.Id.student
    student.status = 'id_ready'
    student.save()

    