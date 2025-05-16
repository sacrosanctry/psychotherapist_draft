from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication URLs
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    
    # Registration URLs
    path('register/', views.RegisterChoiceView.as_view(), name='register_choice'),
    path('register/client/', views.ClientRegistrationView.as_view(), name='client_register'),
    path('register/therapist/', views.TherapistRegistrationView.as_view(), name='therapist_register'),
    
    # Account URLs
    path('account/client/', views.client_account, name='client_account'),
    path('account/therapist/', views.therapist_account, name='therapist_account'),
    
    # Profile Edit URLs
    path('profile/client/edit/', views.edit_client_profile, name='edit_client_profile'),
    path('profile/therapist/edit/', views.edit_therapist_profile, name='edit_therapist_profile'),
] 