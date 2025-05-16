from django.urls import path
from . import views

app_name = 'psychotherapists'

urlpatterns = [
    path('', views.TherapistListView.as_view(), name='therapist_list'),
    path('search/', views.TherapistSearchView.as_view(), name='therapist_search'),
    path('<int:pk>/', views.TherapistDetailView.as_view(), name='therapist_detail'),
] 


# from django.contrib import admin
# from django.urls import path, include
# from django.conf import settings
# from django.conf.urls.static import static

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('users/', include('users.urls')),
#     path('matching/', include('matching.urls', namespace='matching')),
# ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 