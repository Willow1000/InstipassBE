from django.apps import AppConfig


class IdConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Id'

    def ready(self):
        from Id.signals import send_id_processing_update, send_id_ready_notification,delete_in_process_once_ready