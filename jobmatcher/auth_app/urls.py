from django.urls import path
from .views import RegisterView, LoginView, UserProfileView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='get_user_profile'),  # Fetch user profile by email or ID
    path('profile/<str:user_id>/', UserProfileView.as_view(), name='get_user_profile_by_id'),  # Fetch by user ID
]
