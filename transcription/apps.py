from django.apps import AppConfig


class TranscriptionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transcription'

    def ready(self):
        import transcription.tasks