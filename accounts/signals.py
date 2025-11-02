"""
Django Signals for Email Notifications and Admin Logging

This module contains signal handlers for automated email notifications
and admin action logging when specific model events occur.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from InstiPass.middleware import get_current_request
from InstiPass.tasks import send_email
from institution.utils import generate_signup_token
from logs.models import AdminActionsLog

from .models import User, InstitutionSignupToken, InstitutionRegistrationToken, BannedIP


@receiver(post_save, sender=User, dispatch_uid="send_institution_registration_email")
def send_institution_registration_link(sender, instance, created, **kwargs):
    """
    Send registration email when a new User is created.
    
    Generates a registration token and sends an email with the registration link
    to the new user's email address.
    
    Args:
        sender: The model class (User)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        # Generate registration token
        token_obj = generate_signup_token(instance.email)
        token = token_obj.get('token')
        lifetime = token_obj.get("lifetime")
        exp = token_obj.get('expiry_date')
        
        # Create token record in database
        InstitutionRegistrationToken.objects.create(
            user=instance,
            token=token,
            expiry_date=exp
        )
        
        subject = "Complete Registration Process"
        
        # Context data for the email template
        context = {
            'registration_link': f"http://127.0.0.1:3000/institution/details?token={token}",
        }
        
        # Render the HTML template with context
        template_name = 'emailtemplates/institution_registration_link.html'
        html_message = render_to_string(template_name, context)
        
        # Create a plain text version for email clients that don't support HTML
        plain_message = strip_tags(html_message)
        
        receiver_email = instance.email
        
        try:
            # Send email asynchronously via Celery task
            send_email.delay(
                subject='Institution Registration link',
                plain_message=plain_message,
                receiver=receiver_email,
                html_message=html_message,
            )

        except Exception as e:
            print(f"Failed to send institution registration email: {e}")


@receiver(post_save, sender=InstitutionSignupToken, dispatch_uid="send_signup_link")
def send_signup_link(sender, instance, created, **kwargs):
    """
    Send signup link email when a new InstitutionSignupToken is created.
    
    Args:
        sender: The model class (InstitutionSignupToken)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        # Context for the email template
        context = {
            'signup_url': f"http://127.0.0.1:3000/institution/signup/?token={instance.token}"
        }
        
        # Render HTML content
        template_name = 'emailtemplates/signup_link.html'
        html_message = render_to_string(template_name, context)
        
        # Create plain text version for email clients that don't support HTML
        plain_message = strip_tags(html_message)
        receiver_email = instance.email
        
        # Send email with both HTML and plain text versions
        send_email.delay(
            subject="InstiPass Institution Signup",
            plain_message=plain_message,
            receiver=receiver_email,
            html_message=html_message,
        )


@receiver(post_save, sender=InstitutionRegistrationToken, dispatch_uid="send_registration_link")
def send_registration_link(sender, instance, created, **kwargs):
    """
    Send registration link email when a new InstitutionRegistrationToken is created for institutions.
    
    Args:
        sender: The model class (InstitutionRegistrationToken)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created and instance.role == "institution":
        # Context for the email template
        context = {
            'registration_url': f"http://127.0.0.1:3000/institution/details/?token={instance.token}"
        }
        
        # Render HTML content
        template_name = 'emailtemplates/registration_link.html'
        html_message = render_to_string(template_name, context)
        
        # Create plain text version for email clients that don't support HTML
        plain_message = strip_tags(html_message)
        receiver_email = instance.user.email
        
        # Send email with both HTML and plain text versions
        send_email.delay(
            subject="InstiPass Institution Signup",
            plain_message=plain_message,
            receiver=receiver_email,
            html_message=html_message,
        )


@receiver(post_delete, sender=User, dispatch_uid="log_user_delete")
def log_user_delete(sender, instance, **kwargs):
    """
    Log user deletion events in AdminActionsLog.
    
    Records when a user is deleted, capturing information about
    the admin performing the action and the user being deleted.
    
    Args:
        sender: The model class (User)
        instance: The actual instance being deleted
        **kwargs: Additional keyword arguments
    """
    request = get_current_request()
    user = request.user if request else None
    
    AdminActionsLog.objects.create(
        action="DELETE",
        admin=user,
        victim_type="USER",
        victim=f"{instance.id} {instance.email} {instance.role}"
    )


@receiver(post_save, sender=BannedIP, dispatch_uid="log_ip_ban")
def log_ip_ban(sender, instance, created, **kwargs):
    """
    Log IP ban events in AdminActionsLog.
    
    Records when an IP address is banned, capturing information about
    the admin performing the action and the banned IP details.
    
    Args:
        sender: The model class (BannedIP)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    request = get_current_request()
    
    # Handle anonymous users (system-initiated bans)
    if request and request.user.is_anonymous:
        user = None    
    else:
        user = request.user if request else None
        
    AdminActionsLog.objects.create(
        action="BAN",
        admin=user,
        victim_type="IP",
        victim=f"{instance.ip_address} {instance.reason}"
    )