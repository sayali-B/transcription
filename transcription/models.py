from django.db import models                                   # type: ignore

class TranscriptionTaskModel(models.Model):
    task_id = models.CharField(max_length=255, unique=True)
    file_path = models.CharField(max_length=500, null=True, blank=True)  
    audio_file_name = models.CharField(max_length=255)
    transcription = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, default="PENDING")


