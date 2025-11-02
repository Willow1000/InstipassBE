from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        from .signals import send_signup_link, send_institution_registration_link, log_user_delete,send_registration_link,log_ip_ban
