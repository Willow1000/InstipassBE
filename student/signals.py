from django.dispatch import receiver
from .models import *
from Id.models import IdOnQueue
from django.db.models.signals import post_save,post_delete
from django.utils import timezone
# from datetime import datetime
from django.core.mail import send_mail
from logs.models import IdprogressLog,AdminActionsLog
from InstiPass.middleware import get_current_request
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import uuid
from datetime import datetime, timedelta
from django.core.handlers.wsgi import WSGIRequest
from logs.models import AdminActionsLog
from logs.models import IdprogressLog
from InstiPass.tasks import send_email #send_sms


@receiver(post_save,sender=Student,dispatch_uid = 'notify_student_and_update_process_status')
def send_id_processing_update(sender,instance,created,**kwargs):
    if instance.status == "id_processing":

        # Email subject
        subject = "Your ID is in the processing stage"
        student_first_name=getattr(instance, 'firstname',"")
        student_last_name = getattr(instance, 'lastname',"")

        student_name = student_first_name + " " + student_last_name
        
        # Get the student email
        
        # Get student name or use a default

        
        # Get ID reference number
        id_reference = getattr(instance, 'id_number', str(uuid.uuid4())[:6].upper())
        
        # Get processing start time
        processing_started = getattr(instance.updated_at, 'started_processing', datetime.now())
        if hasattr(processing_started, 'strftime'):
            processing_started_str = processing_started.strftime('%B %d, %Y at %I:%M %p')
        else:
            processing_started_str = str(processing_started)
        
        # Get request date
        request_date = getattr(instance.Id, 'created_at', 
                    getattr(instance.Id, 'request_date', ''))
        if hasattr(request_date, 'strftime'):
            request_date_str = request_date.strftime('%B %d, %Y')
        else:
            request_date_str = str(request_date)
        
        # Context data for the template
        context = {
            'student_name': student_name,
            'id_number': 'ID-',
            'id_reference': id_reference,
            'estimated_days': '3-5',
            'request_date': request_date_str,
            'institution_name': getattr(instance.Id.student, 'institution', 'Your Institution'),
            'id_type': getattr(instance.Id, 'id_type', 'Student ID'),
            'processing_started': processing_started_str
        }
        
        # Render the HTML template with context
        template_name = 'id_processing.html'
        html_message = render_to_string(template_name, context)
        
        # Create a plain text version for email clients that don't support HTML
        plain_message = strip_tags(html_message)
        receiver = instance.email
        # Send the email with both HTML and plain text versions
        return send_email.delay(

            subject=subject,
            plain_message=plain_message,
            
            receiver = receiver,
            html_message=html_message,
                
        )
    
@receiver(post_save,sender=Student,dispatch_uid = 'notify_student_and_update_ready_status')
def send_id_ready_notification(sender,instance,created, **kwargs):
    if instance.status == 'id_ready':
    # Email subject
        subject = "Your ID is ready"
        
        # Get the student email
        
        # Get student name or use a default
        student_first_name=getattr(instance, 'firstname',"")
        student_last_name = getattr(instance, 'lastname',"")

        student_name = student_first_name + " " + student_last_name
        # Get ID reference number
        id_reference = getattr(instance, 'id', str(uuid.uuid4())[:6].upper())
        
        # Get processing finished time
        processing_finished = getattr(instance.updated_at, 'finished_processing', datetime.now())
        if hasattr(processing_finished, 'strftime'):
            processing_finished_str = processing_finished.strftime('%B %d, %Y at %I:%M %p')
        else:
            processing_finished_str = str(processing_finished)
        
        # Get request date
        request_date = getattr(instance, 'updated_at', 
                    getattr(instance, 'request_date', ''))
        if hasattr(request_date, 'strftime'):
            request_date_str = request_date.strftime('%B %d, %Y')
        else:
            request_date_str = str(request_date)
        
        # Generate pickup reference
        pickup_id = str(uuid.uuid4())[:6].upper()
        
        # Calculate pickup deadline (30 days from now)
        pickup_deadline = datetime.now() + timedelta(days=30)
        pickup_deadline_str = pickup_deadline.strftime('%B %d, %Y')
        
        # Context data for the template
        context = {
            'student_name': student_name,
            'id_number': 'ID-',
            'id_reference': id_reference,
            'request_date': request_date_str,
            'institution_name': getattr(instance.institution.name, 'institution', 'Your Institution'),
            'id_type': getattr(instance.id, 'id_type', 'Student ID'),
            'processing_finished': processing_finished_str,
            'pickup_location': 'Student Services Center, Room 101',  # Customize as needed
            'pickup_hours': 'Monday-Friday, 9:00 AM - 5:00 PM',      # Customize as needed
            'available_from': 'Immediately',
            'required_documents': 'Government-issued photo ID (driver\'s license, passport, etc.)',
            'pickup_reference': 'PICKUP-',
            'pickup_id': pickup_id,
            'pickup_deadline_days': '30',
            'pickup_deadline': pickup_deadline_str
        }
        
        # Render the HTML template with context
        template_name = 'id_ready_notification.html'
        html_message = render_to_string(template_name, context)
        
        # Create a plain text version for email clients that don't support HTML
        plain_message = strip_tags(html_message)
        receiver = instance.email
        # Send the email with both HTML and plain text versions
        return send_email.delay(

            subject=subject,
            plain_message=plain_message,
            
            receiver = receiver,
            html_message=html_message,
                
            )


def send_application_received_email(instance):
    """
    Send an application received notification email with HTML formatting.
    
    Args:
        instance: The Student model instance
    """
    # Context for the email template
    # context = {
    #     'submission_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    #     'application_id': instance.id
    # }
    to_number =  instance.phone_number
    student_name = instance.first_name

    # Add name fields if they exist
    # if hasattr(instance, 'first_name'):
    #     context['first_name'] = instance.first_name
    # if hasattr(instance, 'last_name'):
    #     context['last_name'] = instance.last_name
    
    # # Render HTML content
    # template_name = 'emailtemplates/application_received.html'
    # html_message = render_to_string(template_name, context)
    
    # # Create plain text version for email clients that don't support HTML
    # subject = "application received".upper()
    # plain_message = strip_tags(html_message)
    # receiver = instance.email
    # # Send email with both HTML and plain text versions
    # send_email.delay(

    #     subject=subject,
    #     plain_message=plain_message,
        
    #     receiver = receiver,
    #     html_message=html_message,
                
    # )
    # send_sms.delay(recipients=to_number,multi=False,message=f"Hello {student_name}, your application has been received. Stay tuned for more updates.")

def send_application_updated_email(instance):
    """
    Send an application updated notification email with HTML formatting.
    
    Args:
        instance: The Student model instance
    """
    # Context for the email template
    context = {
        'update_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'application_id': instance.id
    }
    
    # Add name fields if they exist
    if hasattr(instance, 'first_name'):
        context['first_name'] = instance.first_name
    if hasattr(instance, 'last_name'):
        context['last_name'] = instance.last_name
    
    # Render HTML content
    template_name = 'emailtemplates/application_updated.html'
    html_message = render_to_string(template_name, context)
    
    # Create plain text version for email clients that don't support HTML
    plain_message = strip_tags(html_message)
    receiver = instance.email
    # Send email with both HTML and plain text versions
    send_email.delay(
        subject=subject,
        plain_message=plain_message,
        
        receiver = receiver,
        html_message=html_message,
        
    )

# Optimized signal receivers
@receiver(post_save, sender=Student, dispatch_uid="update_status")
def application_received(sender, instance, created, **kwargs):
    if created:
        # Update status
        sender.objects.filter(id=instance.id).update(status="application_received")
        
        # Create queue and log entries
        # from id.models import IdOnQueue, IdprogressLog
        queue_entry = IdOnQueue.objects.create(student=instance)
        IdprogressLog.objects.create(Id=queue_entry)
        
        # Send HTML email notification
        send_application_received_email(instance)

@receiver(post_save, sender=Student, dispatch_uid="student_updated")
def update_student(sender, instance, created, **kwargs):
    if not created:
        # Send HTML email notification
        send_application_updated_email(instance)
        
        # Log admin action
        
        
        # Get current request safely
        try:
            from threading import local
            _thread_locals = local()
            request = getattr(_thread_locals, 'request', None)
            user = request.user if request and hasattr(request, 'user') else None
        except:
            user = None
        
        # Create log entry
        AdminActionsLog.objects.create(
            action="UPDATE",
            admin=user,
            victim_type="STUDENT",
            victim=f"{instance.id} {instance.first_name} {instance.last_name}"
        )


@receiver(post_delete,sender=Student,dispatch_uid="student_deleted")
def delete_student(sender,instance,**kwargs):
    request = get_current_request()
    user = request.user if request else None
    AdminActionsLog.objects.create(
        action = "DELETE",
        admin = user,
        victim_type= "STUDENT",
        victim = f"{instance.id} {instance.first_name} {instance.last_name} "

    )







