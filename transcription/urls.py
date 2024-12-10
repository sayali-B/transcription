from django.urls import path # type: ignore
from .views import transcribe_audio, check_task_status    

urlpatterns = [

    path('api/transcribe-audio/upload/', transcribe_audio, name='upload_audio'),
    path('api/check_task_status/<str:task_id>/', check_task_status, name='task_status'),

]
