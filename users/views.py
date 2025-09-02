from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .serializers import RegisterSerializer, UserProfileSerializer, UserProfileUpdateSerializer, ChangePasswordSerializer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Count

User = get_user_model()

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


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def user_profile_combined(request):
    """Get or update current user profile information."""
    if request.method == 'GET':
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    elif request.method in ['PUT', 'PATCH']:
        serializer = UserProfileUpdateSerializer(request.user, data=request.data, partial=(request.method == 'PATCH'))
        if serializer.is_valid():
            serializer.save()
            # Return updated profile data
            profile_serializer = UserProfileSerializer(request.user)
            return Response(profile_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_profile(request):
    """Update current user profile information."""
    serializer = UserProfileUpdateSerializer(request.user, data=request.data, partial=(request.method == 'PATCH'))
    if serializer.is_valid():
        serializer.save()
        # Return updated profile data
        profile_serializer = UserProfileSerializer(request.user)
        return Response(profile_serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """Change user password."""
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats(request):
    """Get user statistics."""
    user = request.user
    
    # Import here to avoid circular imports
    from projects.models import Project
    from qr.models import QRCard
    
    # Get user's projects and related stats
    projects = Project.objects.filter(user=user)
    total_projects = projects.count()
    
    # Get QR cards for user's projects
    qr_cards = QRCard.objects.filter(project__user=user)
    total_qr_cards = qr_cards.count()
    
    # Count total photos across all user's QR cards
    total_photos = sum(qr_card.photo_count for qr_card in qr_cards)
    
    # Count projects created this month
    from django.utils import timezone
    from datetime import datetime
    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_projects = projects.filter(created_at__gte=current_month).count()
    
    return Response({
        'total_projects': total_projects,
        'total_qr_cards': total_qr_cards,
        'total_photos': total_photos,
        'this_month_projects': this_month_projects,
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """Logout user and blacklist refresh token."""
    try:
        # Try to get refresh token from request data or cookies
        refresh_token = request.data.get('refresh') or request.COOKIES.get('refresh')
        
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        # Create response
        response = Response({'message': 'Successfully logged out.'}, status=status.HTTP_200_OK)
        
        # Clear cookies
        response.delete_cookie('access', path='/')
        response.delete_cookie('refresh', path='/')
        
        return response
        
    except Exception as e:
        # Even if token blacklisting fails, clear cookies and return success
        response = Response({'message': 'Successfully logged out.'}, status=status.HTTP_200_OK)
        response.delete_cookie('access', path='/')
        response.delete_cookie('refresh', path='/')
        return response
