from django.contrib import admin               # type: ignore
from django.urls import path, include          # type: ignore

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('transcription.urls')),
    path('', include('user_management.urls')),
]
