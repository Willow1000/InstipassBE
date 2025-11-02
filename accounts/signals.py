# from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db.models.signals import post_save,post_delete
from InstiPass.middleware import get_current_request
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import User as user
from .models import InstitutionSignupToken,InstitutionRegistrationToken,BannedIP
from logs.models import AdminActionsLog
from institution.utils import generate_signup_token
from InstiPass.tasks import send_email

@receiver(post_save, sender=user, dispatch_uid="send_institution_registration_email")
def send_institution_registration_link(sender, instance, created, **kwargs):
    if created:
        token_obj = generate_signup_token(instance.email)
        token = token_obj.get('token')
        lifetime = token_obj.get("lifetime")
        exp = token_obj.get('expiry_date')
        InstitutionRegistrationToken.objects.create(user=instance,token=token,expiry_date=exp)
        subject = f"Complete Registration Process"
        
        # Get admin name if available, otherwise use a default
        # admin_name = getattr(instance.institution, 'admin_name', 'Administrator')
        
        # Context data for the template
        context = {
            'registration_link':f"http://127.0.0.1:3000/institution/details?token={token}",
        }
        
        # Render the HTML template with context
        template_name = 'emailtemplates/institution_registration_link.html'
        html_message = render_to_string(template_name, context)
        
        # Create a plain text version for email clients that don't support HTML
        plain_message = strip_tags(html_message)
        
        receiver = instance.email
        try:
            send_email.delay(
                subject='Institution Registration link',
                plain_message=plain_message,
               
                receiver=receiver,
                html_message=html_message,
               
            )

        except Exception as e:
            print(f"Failed to send admin settings update notification: {e}")


@receiver(post_save, sender=InstitutionSignupToken, dispatch_uid="send_signup_link")
def send_signup_link(sender, instance, created, **kwargs):
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
        receiver = instance.email
        # Send email with both HTML and plain text versions
        send_email.delay(
            subject="InstiPass Institution Signup",
            plain_message=plain_message,
            receiver=receiver,
        
            html_message=html_message,
        )

@receiver(post_save, sender=InstitutionRegistrationToken, dispatch_uid="send_registration_link")
def send_registration_link(sender, instance, created, **kwargs):
    
    if created and instance.role =="institution":

    # Context for the email template
        context = {
            'registration_url': f"http://127.0.0.1:3000/institution/details/?token={instance.token}"
        }
        
        # Render HTML content
        template_name = 'emailtemplates/registration_link.html'
        html_message = render_to_string(template_name, context)
        # Create plain text version for email clients that don't support HTML
        plain_message = strip_tags(html_message)
        receiver = instance.user.email
        # Send email with both HTML and plain text versions
        send_email.delay(
            subject="InstiPass Institution Signup",
            plain_message=plain_message,
            receiver=receiver,
        
            html_message=html_message,
        )


@receiver(post_delete,sender=user,dispatch_uid="log_user_delete")
def log_user_delete(sender,instance,**kwargs):
    request = get_current_request()
    user = request.user if request else None
    AdminActionsLog.objects.create(
        action = "DELETE",
        admin = user,
        victim_type= "USER",
        victim = f"{instance.id} {instance.email} {instance.role}"

    )
@receiver(post_save,sender=BannedIP,dispatch_uid="log_ip_ban")
def log_ip_ban(sender,instance,created,**kwargs):
    request = get_current_request()
    if request.user.is_anonymous:
        user= None    
        
    else:
        user = request.user
    AdminActionsLog.objects.create(
        action = "BAN",
        admin = user,
        victim_type= "IP",
        victim = f"{instance.ip_address} {instance.reason}"

    )    
