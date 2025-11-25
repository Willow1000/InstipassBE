from django.core.mail import send_mail
from django.dispatch import receiver
from django.db.models.signals import post_save,post_delete
from django.utils import timezone
from .models import *
from django.utils.html import strip_tags
from django.utils.timezone import now
from django.template.loader import render_to_string
from accounts.models import *
from .utils import generate_student_registration_token,generate_signup_token
from InstiPass.middleware import get_current_request
from logs.models import AdminActionsLog,TransactionsLog
from django.template.loader import render_to_string
import uuid
from django.urls import reverse
from datetime import datetime, timedelta,timezone
from InstiPass.utils import send_email as sendmail
from InstiPass.tasks import send_email
from InstiPass.middleware import get_client_ip
from django.shortcuts import get_object_or_404


# Institution Profile Update Signals
@receiver(post_save, sender=Institution, dispatch_uid="institution_profile_update")
def send_institution_profile_update_email(sender, instance, created, **kwargs):
    if not created:
        # Email subject
        subject = "Your profile has been updated successfully"
        
        # Context data for the template
        context = {
            'institution_name': instance.name,
            'update_date': now().strftime('%B %d, %Y'),
            'updated_fields': getattr(instance, 'updated_fields', None)
        }
        
        # Render the HTML template with context
        template_name = 'institution/institution_profile_update.html'
        html_message = render_to_string(template_name, context)
        
        # Create a plain text version for email clients that don't support HTML
        plain_message = strip_tags(html_message)
        Notifications.objects.create(
                type = "success",
                recipient = instance,
                title = "Profile Update".upper(),
                message = f"Your Profile has been upadted successfully"

        )
        receiver = instance.email
        # Send the email with both HTML and plain text versions
        try:
            send_email.delay(
                subject=subject,
                plain_message=plain_message,
                
                receiver = receiver,
                html_message=html_message,
               
            )
        except Exception as e:
            print(f"Failed to send institution profile update email: {e}")


@receiver(post_save, sender=Institution, dispatch_uid="admin_profile_update_notification")
def send_admin_profile_update_notification(sender, instance, created, **kwargs):
    if not created:
        # Email subject
        subject = f"{instance.name}'s profile has been updated successfully"
        
        # Get admin name if available, otherwise use a default
        admin_name = getattr(instance, 'admin_name', 'Administrator')
        
        # Context data for the template
        context = {
            'admin_name': admin_name,
            'institution_name': instance.name,
            'update_date': now().strftime('%B %d, %Y'),
            'updated_fields': getattr(instance, 'updated_fields', None)
        }
        
        # Render the HTML template with context
        template_name = 'administrator/admin_profile_update_notification.html'
        html_message = render_to_string(template_name, context)
        
        # Create a plain text version for email clients that don't support HTML
        plain_message = strip_tags(html_message)
        receiver = instance.admin_email
        
        # Send the email with both HTML and plain text versions
        try:
            send_email.delay(
                subject=subject,
                plain_message=plain_message,
                
                receiver = receiver,
                html_message=html_message,
                
            )
        except Exception as e:
            print(f"Failed to send admin profile update notification: {e}")


# Institution Registration Signals
@receiver(post_save, sender=Institution, dispatch_uid="institution_registration")
def send_institution_registration_email(sender, instance, created, **kwargs):
    if created:
        # Email subject
        subject = f"{instance.name} has been successfully registered to InstiPass"
        
        # Generate a unique institution ID for reference
        institution_id = str(uuid.uuid4())[:6].upper()
        
        # Context data for the template
        context = {
            'institution_name': instance.name,
            'account_id': 'INST-',
            'institution_id': institution_id,
            'registration_date': now().strftime('%B %d, %Y')
        }
        Notifications.objects.create(
                type = "success",
                recipient = instance,
                title = "Welcome".upper(),
                message = f"{instance.name} has been registered to Instipass"

        )
        # Render the HTML template with context
        template_name = 'institution/institution_registration.html'
        html_message = render_to_string(template_name, context)
        
        # Create a plain text version for email clients that don't support HTML
        plain_message = strip_tags(html_message)
        receiver = instance.email
        # Send the email with both HTML and plain text versions
        try:
            send_email.delay(
                subject=subject,
                plain_message=plain_message,
                
                receiver = receiver,
                html_message=html_message,
                
            )
        except Exception as e:
            print(f"Failed to send institution registration email: {e}")


@receiver(post_save, sender=Institution, dispatch_uid="admin_registration_notification")
def send_admin_registration_email(sender, instance, created, **kwargs):
    if created:
        # Email subject
        subject = f"You have been selected as the admin for {instance.name} InstiPass"
        
        # Generate a unique institution ID for reference
        institution_id = str(uuid.uuid4())[:6].upper()
        
        # Get admin name if available, otherwise use a default
        admin_name = getattr(instance, 'admin_name', 'Administrator')
        
        # Context data for the template
        context = {
            'admin_name': admin_name,
            'institution_name': instance.name,
            'account_id': 'INST-',
            'institution_id': institution_id,
            'registration_date': now().strftime('%B %d, %Y')
        }
        
        # Render the HTML template with context
        template_name = 'institution/institution_admin_notification.html'
        html_message = render_to_string(template_name, context)
        
        # Create a plain text version for email clients that don't support HTML
        plain_message = strip_tags(html_message)
        receiver = instance.admin_email
        # Send the email with both HTML and plain text versions
        try:
            send_email.delay(
                subject=subject,
                plain_message=plain_message,
                
                receiver = receiver,
                html_message=html_message,
                
            )
        except Exception as e:
            print(f"Failed to send admin registration notification: {e}")


# Institution Settings Signals
@receiver(post_save, sender=InstitutionSettings, dispatch_uid="institution_settings_received")
def send_institution_settings_received_email(sender, instance, created, **kwargs):
    if created:
        # Email subject
        subject = f"{instance.institution.name}, Your preferences have been successfully received."
        
        # Context data for the template
        context = {
            'institution_name': instance.institution.name,
            'submission_date': now().strftime('%B %d, %Y'),
        }
        
        # Render the HTML template with context
        template_name = 'institution/institution_settings_received.html'
        html_message = render_to_string(template_name, context)
        
        # Create a plain text version for email clients that don't support HTML
        plain_message = strip_tags(html_message)
        Notifications.objects.create(
                type = "success",
                recipient = instance.institution,
                title = "Settings Received".upper(),
                message = f"Your ID preferences have been uploaded successfully"


        )
        receiver = instance.institution.email
        # Send the email with both HTML and plain text versions
        try:
            send_email.delay(
                subject=subject,
                plain_message=plain_message,
                
                receiver = receiver,
                html_message=html_message,
                
            )
        except Exception as e:
            print(f"Failed to send institution settings received email: {e}")


@receiver(post_save, sender=InstitutionSettings, dispatch_uid="admin_settings_received")
def send_admin_settings_received_email(sender, instance, created, **kwargs):
    if created:
        # Email subject
        subject = f"{instance.institution.name}'s preferences have been successfully received."
        
        # Get admin name if available, otherwise use a default
        admin_name = getattr(instance.institution, 'admin_name', 'Administrator')
        
        # Context data for the template
        context = {
            'admin_name': admin_name,
            'institution_name': instance.institution.name,
            'submission_date': now().strftime('%B %d, %Y'),
        }
        
        # Render the HTML template with context
        template_name = 'administrator/admin_settings_received.html'
        html_message = render_to_string(template_name, context)
        
        # Create a plain text version for email clients that don't support HTML
        plain_message = strip_tags(html_message)
        receiver = instance.institution.admin_email
        # Send the email with both HTML and plain text versions
        try:
            send_email.delay(
                subject=subject,
                plain_message=plain_message,
                
                receiver = receiver,
                html_message=html_message,
                
            )
        except Exception as e:
            print(f"Failed to send admin settings received notification: {e}")


@receiver(post_save, sender=InstitutionSettings, dispatch_uid="institution_settings_update")
def send_institution_settings_update_email(sender, instance, created, **kwargs):
    if not created:
        # Email subject
        subject = "Your institution settings have been updated successfully"
        
        # Context data for the template
        context = {
            'institution_name': instance.institution.name,
            'update_date': now().strftime('%B %d, %Y'),
        }
        
        # Render the HTML template with context
        template_name = 'institution/institution_settings_update.html'
        html_message = render_to_string(template_name, context)
        
        # Create a plain text version for email clients that don't support HTML
        plain_message = strip_tags(html_message)
        Notifications.objects.create(
                type = "success",
                recipient = instance.institution,
                title = "Settings updated".upper(),
                message = f"Your institution Settings were updated successfully"

        )
        receiver = instance.institution.email
        # Send the email with both HTML and plain text versions
        try:
            send_email.delay(
                subject=subject,
                plain_message=plain_message,
                
                receiver = receiver,
                html_message=html_message,
                
            )
        except Exception as e:
            print(f"Failed to send institution settings update email: {e}")


@receiver(post_save, sender=InstitutionSettings, dispatch_uid="admin_settings_update")
def send_admin_settings_update_notification(sender, instance, created, **kwargs):
    if not created:
        # Email subject
        subject = f"{instance.institution.name}'s settings have been updated successfully"
        
        # Get admin name if available, otherwise use a default
        admin_name = getattr(instance.institution, 'admin_name', 'Administrator')
        
        # Context data for the template
        context = {
            'admin_name': admin_name,
            'institution_name': instance.institution.name,
            'update_date': now().strftime('%B %d, %Y'),
        }
        
        # Render the HTML template with context
        template_name = 'administrator/admin_settings_update.html'
        html_message = render_to_string(template_name, context)
        
        # Create a plain text version for email clients that don't support HTML
        plain_message = strip_tags(html_message)
        receiver = instance.institution.admin_email
        # Send the email with both HTML and plain text versions
        try:
            send_email.delay(
                subject=subject,
                plain_message=plain_message,
                
                receiver = receiver,
                html_message=html_message,
                
            )
        except Exception as e:
            print(f"Failed to send admin settings update notification: {e}")

# @receiver(post_save, sender=InstitutionSettings, dispatch_uid="student_registration_token")
# def create_student_registration_token(sender, instance, created, **kwargs):
#     if created:
#         token_obj =generate_student_registration_token(instance.institution)
#         token = token_obj.get('token')
#         lifetime = token_obj.get("lifetime")
#         exp = token_obj.get('expiry_date')
#         StudentRegistrationToken.objects.create(institution=instance.institution,token=token,lifetime=lifetime,expiry_date=exp)

@receiver(post_save,sender=StudentRegistrationToken,dispatch_uid = "student_registration_link")
def send_student_registration_link(sender,instance,created,**kwargs):
    subject = f"{instance.institution.name}'s student registration link"
    token = instance.token
    lifetime = instance.lifetime
    exp = instance.expiry_date
    # Get admin name if available, otherwise use a default
    admin_name = getattr(instance.institution, 'admin_name', 'Administrator')
    
    # Context data for the template
    context = {
        'institution_name': instance.institution.name,
        'registration_link':f"http://127.0.0.1:3000/students?token={token}",
        'lifetime': lifetime,
        'expiry_date': exp,
    }
    
    # Render the HTML template with context
    template_name = 'emailtemplates/student_registration_link.html'
    html_message = render_to_string(template_name, context)
    
    # Create a plain text version for email clients that don't support HTML
    plain_message = strip_tags(html_message)
    receiver = [instance.institution.email,instance.institution.admin_email]
    try:
            send_email.delay(
                subject=subject,
                plain_message=plain_message,
                
                receiver = receiver,
                html_message=html_message,
                
            )
        # send_mail(
        #     subject='Student Registration link',
        #     message=f'students can register for their Ids using this link http://127.0.0.1:3000/students?token={token} , desclaimer: a device can only register one student',
        #     from_email="notifications@instipass.com",
        #     recipient_list=[instance.institution.email],
        #     html_message=html_message,
        #     fail_silently=False
        # )
    except Exception as e:
        print(f"Failed to send admin settings update notification: {e}")

@receiver(post_delete,sender=Institution,dispatch_uid="institution_deleted")
def delete_institution(sender,instance,**kwargs):
    request = get_current_request()
    user = request.user if request else None
    AdminActionsLog.objects.create(
        action = "DELETE",
        admin = user,
        victim_type= "INSTITUTION",
        victim = f"{instance.id} {instance.name}"

    )

@receiver(post_save,sender=NewsLetter,dispatch_uid = 'notify_user_they_signed_up_for_newsletter')
def send_newsletter_signup_confirmation(sender,instance,created,**kwargs):

    # Email subject
    subject = "Thank you for signing up for InstiPass newsletter service"
    
    # Context data for the template
    context = {
        'user_name': getattr(instance, 'name', getattr(instance, 'username', '')),
    }
    
    # Render the HTML template with context
    template_name = 'administrator/newsletter_signup_conf.html'
    html_message = render_to_string(template_name, context)
    
    # Create a plain text version for email clients that don't support HTML
    plain_message = strip_tags(html_message)
    receiver=instance.email
    # Send the email with both HTML and plain text versions
    return send_email.delay(
            subject=subject,
            plain_message=plain_message,
            
            receiver = receiver,
            html_message=html_message,
            
        )

@receiver(post_save,sender=ContactUs,dispatch_uid = 'message_received')
def send_contact_confirmation(sender,instance,created,**kwargs):

    # Email subject
    subject = "Thank you for contacting InstiPass"
    
    # Generate a unique ticket ID for reference
    ticket_id = str(uuid.uuid4())[:8].upper()
    
    # Context data for the template
    context = {
        'user_name': getattr(instance, 'name'),
        'ticket_id': ticket_id,
        'reference_number': 'CONTACT-',
    }
    
    # Render the HTML template with context
    template_name = 'administrator/contact_confirmation.html'
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
    # return sendmail(to = instance.email,subject=subject,context=context,from_email="noreply@instipass.com",template_name=template_name)

# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.template.loader import render_to_string
# from django.utils.html import strip_tags
# from .tasks import send_email  # Your Celery task
# from .models import Issue, PaymentProofVerification, ContactUs  # Your models


# Signal 1: Issue Report Notification
@receiver(post_save, sender=Issue)
def notify_admin_issue_reported(sender, instance, created, **kwargs):
    """
    Send notification to admin when a new issue is reported
    """
    if created:
        # Determine styling based on issue type
        issue_type_styles = {
            'bug': 'danger',
            'payment': 'warning',
            'fraud': 'danger',
            'template': 'warning',
            'other': 'info'
        }
        
        issue_type_emojis = {
            'bug': '🐛',
            'payment': '💳',
            'fraud': '🚨',
            'template': '🎨',
            'other': '📋'
        }
        
        # Map issue types to display names
        issue_type_display = {
            'bug': 'Bug Report',
            'payment': 'Payment Issue', 
            'fraud': 'Fraud Alert',
            'template': 'Template Issue',
            'other': 'Other Issue'
        }
        
        # Map status to display names
        status_display = {
            'open': 'Open',
            'in_progress': 'In Progress',
            'resolved': 'Resolved',
            'closed': 'Closed'
        }
        
        context = {
            'notification_type': 'New Issue Reported',
            'subject': f'{issue_type_display.get(instance.issue_type, "Issue")}: {instance.institution.name}',
            'introduction_text': f'A new issue has been reported by {instance.institution.name} that requires your attention.',
            'emoji': issue_type_emojis.get(instance.issue_type, '📋'),
            'details_heading': 'Issue Details',
            'details': {
                'Institution': instance.institution.name,
                'Institution Email': instance.institution.email if hasattr(instance.institution, 'email') else 'N/A',
                'Issue Type': issue_type_display.get(instance.issue_type, 'Other Issue'),
                'Status': status_display.get(instance.status, 'Open'),
                'Description': instance.description,
                'Attachment': 'Yes - View in admin panel' if instance.attachment else 'No attachment',
                'Reported On': instance.created_at.strftime('%Y-%m-%d at %H:%M:%S'),
                'Issue ID': f'#ISS-{instance.id}'
            },
            'cta_buttons': [
                {
                    'url': f'https://127.0.0.1:8000/super/issues/{instance.id}/',
                    'text': 'View Issue Details',
                    'secondary': False
                },
                {
                    'url': f'https://127.0.0.1:8000/super/issues/{instance.id}/assign/',
                    'text': 'Assign to Team Member',
                    'secondary': False
                },
                {
                    'url': f'https://127.0.0.1:8000/super/institutions/{instance.institution.id}/',
                    'text': 'View Institution Profile',
                    'secondary': False
                }
            ],
            'action_items': [
                {
                    'icon': '🔍',
                    'title': 'Investigate Issue',
                    'description': 'Review the issue details and any attachments. Check system logs if it\'s a technical issue.'
                },
                {
                    'icon': '👤',
                    'title': 'Assign & Acknowledge',
                    'description': 'Assign the issue to the appropriate team member and acknowledge receipt to the institution within 2 hours.'
                },
                {
                    'icon': '⏱️',
                    'title': 'Set Priority',
                    'description': 'Fraud and payment issues: Immediate action. Bugs: Within 24 hours. Template/Other: Within 48 hours.'
                },
                {
                    'icon': '📊',
                    'title': 'Track Resolution',
                    'description': 'Update the issue status as work progresses and notify the institution when resolved.'
                }
            ],
            'important_note': 'Fraud and payment issues require immediate attention. Please escalate critical issues to senior management if needed.',
            'notification_style': issue_type_styles.get(instance.issue_type, 'info')
        }
        
        subject = f'[InstiPass] New {issue_type_display.get(instance.issue_type, "Issue")} - {instance.institution.name}'
        template_name = 'emailtemplates/admin_notification.html'
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        
        send_email.delay(
            subject=subject,
            plain_message=plain_message,
            receiver=['wilkinsondari7@gmail.com'],  # Admin email(s)
            html_message=html_message,
        )


# Signal 2: Payment Proof Verification Notification
@receiver(post_save, sender=PaymentProofVerification)
def notify_admin_payment_verification(sender, instance, created, **kwargs):
    """
    Send notification to admin when a new payment proof is submitted for verification
    """
    if created:
        # Map status to display names
        status_display = {
            'pending': 'Pending Verification',
            'approved': 'Approved',
            'rejected': 'Rejected'
        }
        
        context = {
            'notification_type': 'Payment Proof Verification Required',
            'subject': 'New Payment Proof Submitted',
            'introduction_text': f'{instance.institution.name} has submitted a payment proof document that requires your verification before their account can be activated.',
            'emoji': '💳',
            'details_heading': 'Verification Request',
            'details': {
                'Institution Name': instance.institution.name,
                'Institution Email': instance.institution.email if hasattr(instance.institution, 'email') else 'N/A',
                'Document': 'Uploaded - View in admin panel',
                'Status': status_display.get(instance.status, 'Pending Verification'),
                'Remarks': instance.remarks if instance.remarks else 'No remarks yet',
                'Submitted On': instance.created_at.strftime('%Y-%m-%d at %H:%M:%S'),
                'Last Updated': instance.updated_at.strftime('%Y-%m-%d at %H:%M:%S'),
                'Verification ID': f'#VER-{instance.id}'
            },
            'cta_buttons': [
                {
                    'url': f'https://127.0.0.1:8000/super/payment-verifications/{instance.id}/verify/',
                    'text': 'Review & Verify Payment',
                    'secondary': False
                },
                {
                    'url': f'https://127.0.0.1:8000/super/payment-verifications/{instance.id}/',
                    'text': 'View Full Details',
                    'secondary': False
                },
                {
                    'url': f'https://127.0.0.1:8000/super/institutions/{instance.institution.id}/',
                    'text': 'View Institution Profile',
                    'secondary': False
                }
            ],
            'action_items': [
                {
                    'icon': '📄',
                    'title': 'Review Document',
                    'description': 'Download and carefully examine the payment proof document. Verify it contains: transaction reference, amount, date, and payment method.'
                },
                {
                    'icon': '✅',
                    'title': 'Verify Payment',
                    'description': 'Check your bank/M-Pesa/payment gateway records to confirm the payment was received and matches the proof document details.'
                },
                {
                    'icon': '📝',
                    'title': 'Update Status',
                    'description': 'Approve if verified, or reject with clear remarks explaining why. The institution will be notified of your decision.'
                },
                {
                    'icon': '🔔',
                    'title': 'Activate Account',
                    'description': 'Once approved, ensure the institution\'s subscription is activated and they receive access to their dashboard.'
                }
            ],
            'important_note': '⚠️ Please verify this payment within 24 hours. Delayed verifications impact customer satisfaction and may cause institutions to lose trust in our service.',
            'additional_message': 'If you need to reject this payment proof, please provide detailed remarks explaining what information is missing or incorrect so the institution can resubmit properly.',
            'notification_style': 'warning'
        }
        
        subject = f'[InstiPass] Payment Verification Required - {instance.institution.name}'
        template_name = 'emailtemplates/admin_notification.html'
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        
        send_email.delay(
            subject=subject,
            plain_message=plain_message,
            receiver=['wilkinsondari7@gmail.com'],  # Admin email(s)
            html_message=html_message,
        )


# Signal 3: ContactUs Form Submission Notification
@receiver(post_save, sender=ContactUs)
def notify_admin_contactus_form(sender, instance, created, **kwargs):
    """
    Send notification to admin when a new ContactUs form is submitted
    """
    if created:
        # Map category to appropriate emoji, style, and display name
        category_config = {
            'business': {
                'emoji': '💼', 
                'style': 'info', 
                'priority': 'HIGH',
                'display_name': 'Business Inquiry'
            },
            'support': {
                'emoji': '🆘', 
                'style': 'warning', 
                'priority': 'HIGH',
                'display_name': 'Support Request'
            },
            'bug': {
                'emoji': '🐛', 
                'style': 'danger', 
                'priority': 'MEDIUM',
                'display_name': 'Bug Report'
            },
            'job': {
                'emoji': '💼', 
                'style': 'info', 
                'priority': 'LOW',
                'display_name': 'Job Application'
            },
            'spam': {
                'emoji': '🚫', 
                'style': 'danger', 
                'priority': 'IGNORE',
                'display_name': 'Spam'
            },
            'general': {
                'emoji': '💬', 
                'style': 'info', 
                'priority': 'MEDIUM',
                'display_name': 'General Inquiry'
            }
        }
        
        config = category_config.get(instance.category, category_config['general'])
        
        # Skip notification for spam
        if instance.category == 'spam':
            return
        
        context = {
            'notification_type': 'New Contact Request',
            'subject': f'{config["display_name"]} - {instance.name}',
            'introduction_text': f'A new {config["display_name"].lower()} has been submitted through the InstiPass contact form. Priority: {config["priority"]}',
            'emoji': config['emoji'],
            'details_heading': 'Contact Details',
            'details': {
                'Full Name': instance.name,
                'Email Address': instance.email,
                'Category': config['display_name'],
                'Priority Level': config['priority'],
                'Message': instance.message,
                'Submitted On': instance.created_at.strftime('%Y-%m-%d at %H:%M:%S') if instance.created_at else 'Just now',
                'Contact ID': f'#CTU-{instance.id}'
            },
            'cta_buttons': [
                {
                    'url': f'mailto:{instance.email}?subject=Re: Your InstiPass Inquiry&body=Hi {instance.name},%0D%0A%0D%0AThank you for contacting InstiPass.',
                    'text': 'Reply via Email',
                    'secondary': False
                },
                {
                    'url': f'https://127.0.0.1:8000/super/contactus/{instance.id}/',
                    'text': 'View in Admin Dashboard',
                    'secondary': False
                }
            ],
            'action_items': [
                {
                    'icon': '⚡',
                    'title': 'Response Timeline',
                    'description': 'Business inquiries: 2 hours. Support requests: 4 hours. Bug reports: 24 hours. Job requests: 48 hours. General: 24 hours.'
                },
                {
                    'icon': '📊',
                    'title': 'Log and Track',
                    'description': 'Add this contact to your CRM system and track the conversation for proper follow-up and reporting.'
                },
                {
                    'icon': '🎯',
                    'title': 'Personalize Response',
                    'description': 'Review the message carefully and provide a tailored response that addresses their specific needs.'
                },
                {
                    'icon': '✅',
                    'title': 'Mark as Resolved',
                    'description': 'Update the contact status in the admin panel once you\'ve responded and resolved their inquiry.'
                }
            ],
            'important_note': 'Business and support inquiries are high priority and should be addressed as soon as possible to maintain excellent customer service and conversion rates.',
            'additional_message': f'This message has been auto-categorized as "{config["display_name"]}" based on content analysis. You can recategorize if needed in the admin panel.',
            'notification_style': config['style']
        }
        
        subject = f'[InstiPass] {config["priority"]} Priority - {config["display_name"]} from {instance.name}'
        template_name = 'emailtemplates/admin_notification.html'
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        
        # Send to admin(s)
        send_email.delay(
            subject=subject,
            plain_message=plain_message,
            receiver=['wilkinsondari7@gmail.com'],  # Admin email(s)
            html_message=html_message,
        )

def to_google_calendar_format(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime('%Y%m%dT%H%M%SZ')

@receiver(post_save,sender=DemoBooking,dispatch_uid = 'notify_user_they_signed_up_for_newsletter')
def send_demo_booking_confirmation(sender,instance,created,**kwargs):
    demo_date = getattr(instance,'date','')
    demo_time = getattr(instance,'time','')
    # date_obj = datetime.strptime(demo_date, "%Y-%m-%d").date()
    time_obj = date_obj = datetime.strptime(demo_time, "%H:%M").time()
    combined_dt = datetime.combine(demo_date,time_obj)
    end_dt = combined_dt + timedelta(minutes=30)
    start_google_format = to_google_calendar_format(combined_dt)
    end_google_format = to_google_calendar_format(end_dt)
    if created:

        # Email subject
        subject = "Thank you for booking a demo session with InstiPass"
        
        # Generate a unique booking ID for reference
        booking_id = str(uuid.uuid4())[:6].upper()
        
        # Get demo details from instance or use placeholders
        # In a real implementation, these would come from your booking model
        timezone_name =  'EAT'
        
        
        # Format date and time for display
        demo_date = getattr(instance,'date','')
        demo_time = getattr(instance,'time','')
        # date_obj = datetime.strptime(demo_date, "%Y-%m-%d").date()
        time_obj = date_obj = datetime.strptime(demo_time, "%H:%M").time()
        combined_dt = datetime.combine(demo_date,time_obj)
        end_dt = combined_dt + timedelta(minutes=30)
        start_google_format = to_google_calendar_format(combined_dt)
        end_google_format = to_google_calendar_format(end_dt)

        # Context data for the template
        context1 = {
            'user_name': getattr(instance, 'name', getattr(instance, 'username', '')),
            'booking_id': booking_id,
            'booking_reference': 'DEMO-',
            'demo_date': demo_date,
            'demo_time': demo_time,
            'timezone': timezone_name,
            'presenter_name': getattr(instance, 'presenter_name', 'An InstiPass Specialist'),
            'platform': getattr(instance, 'platform', 'Zoom Meeting'),
            'meeting_link': getattr(instance, 'meeting_link', ''),
            'meeting_id': getattr(instance, 'meeting_id', ''),
            'passcode': getattr(instance, 'passcode', ''),
            'calendar_link': f"https://calendar.google.com/calendar/render?action=TEMPLATE&text=Instipass+DemoSession&dates={start_google_format}/{end_google_format}&details=Prepare+as+many+questions+as+you+can&location=zoom",
            'ics_link': getattr(instance, 'ics_link', '#')
        }
        
        # Render the HTML template with context
        template_name1 = 'administrator/demo_booking_confirmation.html'
        html_message1 = render_to_string(template_name1, context1)
        
        # Create a plain text version for email clients that don't support HTML
        plain_message1 = strip_tags(html_message1)
        
        # Send the email with both HTML and plain text versions
        context = {
        'institution': instance.institution,
    }
    
        # Add optional fields if they exist
        optional_fields = ['date', 'time', 'contact_person', 'email', 'phone']
        for field in optional_fields:
            if hasattr(instance, field):
                context[field] = getattr(instance, field)
        
        # Render HTML content
        template_name = 'emailtemplates/new_demo_booked.html'
        html_message = render_to_string(template_name, context)
        
        # Create plain text version for email clients that don't support HTML
        plain_message = strip_tags(html_message)
        receiver = instance.email
        # Send email with both HTML and plain text versions
        send_email.delay(
            subject=subject,
            plain_message=plain_message,
            
            receiver = ['wilkinsondari7@gmail.com'],
            html_message=html_message,
                
            )
        return send_email.delay(

            subject=subject,
            plain_message=plain_message1,
            
            receiver = receiver,
            html_message=html_message1,
                
            )  
    elif not created and instance.status == 'SCHEDULED' :

        # print('CONFIRMED')
        return
        context = {
            'date': instance.date,
            'time': instance.time,
            'calendar_link': f"https://calendar.google.com/calendar/render?action=TEMPLATE&text=Instipass+DemoSession&dates={start_google_format}/{end_google_format}&details=Prepare+as+many+questions+as+you+can&location=zoom"
        }
    
    # Render HTML content
        template_name = 'emailtemplates/demo_reschedule.html'
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

@receiver(post_save, sender=Issue, dispatch_uid="issue_created_email")
def send_issue_creation_email(sender, instance, created, **kwargs):
    if created:
        # Assuming the Issue instance has a way to get the associated institution's email
        # For this example, let's assume instance.institution_email directly holds the email
        # In a real scenario, you might have instance.institution.email if there's a ForeignKey
        institution_email = instance.institution.email # Or instance.institution.email
        admin_email = instance.institution.admin_email
        institution_name = instance.institution.name

        subject = f"New Issue Reported - Issue ID: {instance.id}"
        
        context = {
            'issue_id': instance.id,
            'submission_date': instance.created_at.strftime('%B %d, %Y %H:%M'),
            'institution_name': institution_name,
        }
        
        template_name = 'emailtemplates/issue_reported_template.html'
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        
        try:
            Notifications.objects.create(
                type = "info",
                recipient = instance.institution,
                title = "Your Issue has been received".upper(),
                message = "We have received your issue, expect us to reach out in the next 12-24 hours. We appreciate your patience."

            )
            receiver = [admin_email]
            send_email.delay(
                subject=subject,
                plain_message=plain_message,
                
                receiver = receiver,
                html_message=html_message,
                
            )
            
        except Exception as e:
            print(f"Failed to send issue creation email: {e}")

@receiver(post_save, sender=Issue, dispatch_uid="issue_resolved_email")
def send_issue_resolution_email(sender, instance, created, **kwargs):
    if not created and hasattr(instance, 'status') and instance.status == 'resolved': # Assuming 'status' field and 'resolved' value
        institution_email = instance.institution.email # Or instance.institution.email
        institution_name = instance.institution.name
        admin_email = instance.institution.admin_email

        subject = f"Issue Resolved - Issue ID: {instance.id}"
        
        context = {
            'issue_id': instance.id,
            'resolution_date': now().strftime('%B %d, %Y %H:%M'),
            'institution_name': institution_name,
        }
        
        template_name = 'emailtemplates/issue_resolved_email.html'
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        
        try:
            Notifications.objects.create(
                type = "success",
                recipient = instance.institution,
                title = "Your Issue has been resolved".upper(),
                message = f"We are glad to inform you that your {instance.issue_type} issue has been resolved. Thanks for your patience"

            )
            receiver = [admin_email]
            send_email.delay(
                subject=subject,
                plain_message=plain_message,
                
                receiver = receiver,
                html_message=html_message,
                
            )

        except Exception as e:
            print(f"Failed to send issue resolution email: {e}")


@receiver(post_save, sender=InstitutionMagicLinkToken, dispatch_uid="send_institution_login_link")
def send_institution_login_link(sender, instance, created, **kwargs):
    if created:
        request = get_current_request()
        institution = instance.institution
        email = institution.email
        admin_email = institution.admin_email
        # generate token + login link
        
        token = instance.token
        expiry_date = instance.expiry_date
        link = f"http://127.0.0.1:3000/institution/auth/login/?token={token}"  # FIXED missing slashes

        # build context for email template
        context = {
            "login_url": link,
            "user_name": institution.name,
            "device_info": request.META.get("HTTP_USER_AGENT", ""),
            "ip": get_client_ip(request),
        }

        # render email
        template_name = 'emailtemplates/institution_login_link.html'
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)

        # send email
        subject = "Login Link"
        
        
        # Send the email with both HTML and plain text versions
        try:
            send_email.delay(
            plain_message=plain_message,
            receiver=[email,admin_email],   # FIXED receiver
            html_message=html_message,
            subject=subject
        )
        except Exception as e:
            print(f"Failed to send admin profile update notification: {e}")            

@receiver(post_save, sender=PaymentProofVerification, dispatch_uid="send_proof_under_review")
def send_proof_under_review(sender, instance, created, **kwargs):
    if created:
        context = {
        # Institution information
        'institution_name': instance.institution.name,  # Name of the institution
        
        # Payment proof details
        'submission_date': instance.created_at,  # Date when proof was submitted
        'reference_number': f"PAY-PROOF-{instance.id}",  # Unique reference number for the payment
        }
        email = instance.institution.email
        admin_email = instance.institution.admin_email
        template_name = 'emailtemplates/payment_proof_under_review.html'
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)

        # send email
        subject = "Payment Proof under review"

        context_admin = {
                "institution_name": instance.institution.name,
                "document_name": "Filename of the uploaded payment proof document", 
                "submission_date": instance.created_at,
                "verification_id":  f"PAY-PROOF-{instance.id}",
                "admin_url": reverse("admin_payment_proof"),
                "admin_dashboard_url": reverse("institutions_admin")
            }
        email_admin = "wilkinsondari7@gmail.com"
        template_name_admin = 'emailtemplates/payment_proof_admin.html'
        html_message_admin = render_to_string(template_name_admin, context_admin)
        plain_message_admin = strip_tags(html_message_admin)

        # send email
        subject_admin = "New Payment Proof Submitted"
        
        try:
            send_email.delay(
            plain_message=plain_message,
            receiver=[email,admin_email],   # FIXED receiver
            html_message=html_message,
            subject=subject
        )
            send_email.delay(
                plain_message=plain_message_admin,
                receiver=[email_admin],   # FIXED receiver
                html_message=html_message_admin,
                subject=subject_admin
            )
            Notifications.objects.create(
                type = "info",
                recipient = instance.institution,
                title = "Payment proof".upper(),
                message = f"Your proof of payment is under review, Kindly check email for more updates."

        )
        except Exception as e:
            print(f"error occured: {e}") 

@receiver(post_save, sender=PaymentProofVerification, dispatch_uid="send_proof_verified")
def send_proof_verified(sender, instance, created, **kwargs):
    if not created and instance.status=="APPROVED":
        context = {
        # Institution information
        'institution_name': instance.institution.name,  # Name of the institution
        
        # Payment proof details
        'submission_date': instance.updated_at,  # Date when proof was submitted
        'reference_number': f"PAY-PROOF-{instance.id}",  # Unique reference number for the payment
        }
        email = instance.institution.email
        admin_email = instance.institution.admin_email
        template_name = 'emailtemplates/payment_proof_verified.html'
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        request = get_current_request()
        # send email
        subject = "Payment Proof Verified"
        
        try:
            send_email.delay(
            plain_message=plain_message,
            receiver=[email,admin_email],   # FIXED receiver
            html_message=html_message,
            subject=subject
        )
            Notifications.objects.create(
                type = "success",
                recipient = instance.institution,
                title = "Payment proof".upper(),
                message = f"Your proof of payment has been approved. Kindly, check your email for more details"

        )
            TransactionsLog.objects.create(
                admin=request.user,
                action="VERIFY",
                victim_type = "PAYMENTPROOF",
                victim = f"{instance}"
            ) 
        except Exception as e:
            print(f"error occured: {e}")    

@receiver(post_save, sender=PaymentProofVerification, dispatch_uid="send_proof_rejected")
def send_proof_rejected(sender, instance, created, **kwargs):
    if not created and instance.status=="REJECTED":
        context = {
        # Institution information
        'institution_name': instance.institution.name,  # Name of the institution
        
        # Payment proof details
        'submission_date': instance.updated_at,  # Date when proof was submitted
        'reference_number': f"PAY-PROOF-{instance.id}",  # Unique reference number for the payment
        }
        email = instance.institution.email
        admin_email = instance.institution.admin_email
        template_name = 'emailtemplates/payment_proof_rejected.html'
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        request = get_current_request()
        # send email
        subject = "Payment Proof Rejected"

        try:
            send_email.delay(
            plain_message=plain_message,
            receiver=[email,admin_email],   # FIXED receiver
            html_message=html_message,
            subject=subject
        )
            Notifications.objects.create(
                type = "error",
                recipient = instance.institution,
                title = "Payment proof".upper(),
                message = f"Your proof of payment has been rejected, kindly upload a valid document. If this problem persists kindly contact support"

        )
            TransactionsLog.objects.create(
                admin=request.user,
                action="REJECT",
                victim_type = "PAYMENTPROOF",
                victim = f"{instance}"
            ) 
        except Exception as e:
            print(f"error occured: {e}")  


@receiver(post_save, sender=Payment, dispatch_uid="send_receipt")
def send_receipt(sender, instance, created, **kwargs):
    if created:
        token_obj = generate_signup_token(instance.institution.email)
        token=token_obj.get('token')
        expiry_date=token_obj.get('expiry_date')
        context = {
        "customer_name": instance.institution.name,
        "reference_number": f"REF-{instance.reference_number}",
        "download_url": f"http://127.0.0.1:8000/institution/download/receipt/?token={token}",
        }
        PaymentReceiptDownloadToken.objects.create(
            payment=instance,
            token=token,
            expiry_date=expiry_date
        )
        # email_html = render_to_string('emails/receipt_email.html', email_context)
        admin_email = instance.institution.admin_email
        template_name = 'emailtemplates/payment_receipt.html'
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)

        # send email
        subject = "Payment successful"
        try:
            send_email.delay(
            plain_message=plain_message,
            receiver=[admin_email],   # FIXED receiver
            html_message=html_message,
            subject=subject
        )
        except Exception as e:
            print(f"Failed to send admin profile update notification: {e}") 

@receiver(post_save, sender=InvoiceDownloadToken, dispatch_uid="send_receipt")
def send_invoice(sender, instance, created, **kwargs):
    if created:
        token = instance.token
        institution = get_object_or_404(Institution,email=instance.email)
        expiry_date=instance.expiry_date
        context = {
        "customer_name": institution.name,
        "reference_number": f"INV-{instance.id}",
        "download_url": f"http://127.0.0.1:8000/institution/download/invoice/?token={token}",
        }
        # PaymentReceiptDownloadToken.objects.create(
        #     payment=instance,
        #     token=token,
        #     expiry_date=expiry_date
        # )
        # email_html = render_to_string('emails/receipt_email.html', email_context)
        admin_email = institution.admin_email
        email = instance.email
        template_name = 'emailtemplates/payment_invoice.html'
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)

        # send email
        subject = "Invoice"
        try:
            send_email.delay(
            plain_message=plain_message,
            receiver=[admin_email],   # FIXED receiver
            html_message=html_message,
            subject=subject
        )
        except Exception as e:
            print(f"Failed to send admin profile update notification: {e}") 
