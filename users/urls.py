from django.urls import path
from .views import (
    RegisterView, CookieTokenObtainPairView, user_profile_combined, 
    update_profile, change_password, user_stats, logout_view
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CookieTokenObtainPairView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('user/', user_profile_combined, name='user_profile'),
    path('user/update/', update_profile, name='update_profile'),
    path('user/stats/', user_stats, name='user_stats'),
    path('change-password/', change_password, name='change_password'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
