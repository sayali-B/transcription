from django.urls import path                                                    # type: ignore
from .views import RegisterView, GetJWTTokenView 

urlpatterns = [
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/token/', GetJWTTokenView.as_view(), name='token_obtain_pair'),
]