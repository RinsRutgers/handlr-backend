from django.shortcuts import render
from rest_framework import generics, permissions
from .serializers import RegisterSerializer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.response import Response
from rest_framework import status

# Create your views here.

class RegisterView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class CookieTokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            access = response.data.get('access')
            refresh = response.data.get('refresh')
            # Set cookies
            response.set_cookie(
                key='access',
                value=access,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite='Lax',
                path='/',
            )
            response.set_cookie(
                key='refresh',
                value=refresh,
                httponly=True,
                secure=False,
                samesite='Lax',
                path='/',
            )
        return response
