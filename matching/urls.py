from django.urls import path
from . import views

app_name = 'matching'

urlpatterns = [
    path('client/matching/', views.client_matching_form, name='client_matching_form'),
    path('therapist/matching/', views.therapist_matching_form, name='therapist_matching_form'),
    path('test-matching/', views.test_matching_data, name='test_matching_data'),
] 