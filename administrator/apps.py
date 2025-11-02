from django.apps import AppConfig


class AdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'administrator'

    def ready(self):
        from .signals import   delete_demobooking,delete_contactus_message
