from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
import logging
from django.utils.http import urlsafe_base64_encode
from django import forms
from django.utils.encoding import force_bytes
from django.core.mail import EmailMultiAlternatives
from django.template import loader
class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email__iexact=email)
            if user.check_password(password):
                return user
        except UserModel.DoesNotExist:
            return None




# Get the custom user model
UserModel = get_user_model()

logger = logging.getLogger(__name__)

class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        """
        Sends a password reset email to `to_email`.
        """
        subject = loader.render_to_string(subject_template_name, context)
        subject = "".join(subject.splitlines())  # Remove any newlines
        body = loader.render_to_string(email_template_name, context)

        email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
        if html_email_template_name:
            html_email = loader.render_to_string(html_email_template_name, context)
            email_message.attach_alternative(html_email, "text/html")

        try:
            email_message.send()
        except Exception:
            logger.exception("Failed to send password reset email to %s", context["user"].pk)

    def get_users(self, email):
        """
        Given an email, return matching user(s) who should receive a reset email.
        """
        email_field_name = UserModel.get_email_field_name()
        active_users = UserModel._default_manager.filter(
            **{f"{email_field_name}__iexact": email, "is_active": True}
        )

        return (
            u
            for u in active_users
            if u.has_usable_password() and u.email.lower() == email.lower()
        )

    def save(
        self,
        domain_override=None,
        subject_template_name="registration/password_reset_subject.txt",
        email_template_name="registration/password_reset_email.html",
        use_https=False,
        token_generator=default_token_generator,
        from_email=None,
        request=None,
        html_email_template_name=None,
        extra_email_context=None,
    ):
        """
        Generate a one-use password reset link and send it to the user.
        """
        email = self.cleaned_data["email"]
        if not domain_override:
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
        else:
            site_name = domain = domain_override

        # Get users matching the provided email
        users = list(self.get_users(email))  # Convert the generator to a list to evaluate if any user exists

        if not users:
            # If no users are found, display a warning message using Django's messages framework.
            messages.warning(request, "No user found with that email address.")
            return  # Return without proceeding with sending emails
        
        # Send the password reset email for each user
        for user in users:
            user_email = user.email
            context = {
                "email": user_email,
                "domain": domain,
                "site_name": site_name,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "user": user,
                "token": token_generator.make_token(user),
                "protocol": "https" if use_https else "http",
                **(extra_email_context or {}),
            }
            self.send_mail(
                subject_template_name,
                email_template_name,
                context,
                from_email,
                user_email,
                html_email_template_name=html_email_template_name,
            )
