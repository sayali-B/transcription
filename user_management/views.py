from rest_framework.views import APIView                    # type: ignore
from rest_framework.response import Response                # type: ignore
from rest_framework import status                           # type: ignore
from rest_framework_simplejwt.tokens import RefreshToken    # type: ignore
from .serializers import UserSerializer
from django.contrib.auth.models import User                 # type: ignore
from rest_framework.permissions import AllowAny             # type: ignore

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({'message': 'User registered successfully',
                             'access_token': access_token}, 
                            status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class GetJWTTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token)
                }, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
