from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.db.models import Q
from .models import Psychotherapist
from users.models import User

# Create your views here.

class TherapistListView(ListView):
    model = Psychotherapist
    template_name = 'psychotherapists/therapist_list.html'
    context_object_name = 'therapists'
    paginate_by = 9

    def get_queryset(self):
        return Psychotherapist.objects.filter(
            user__profile_completed=True
        ).select_related(
            'user',
            'working_methodology'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get unique methodologies for the filter dropdown
        methodologies = Psychotherapist.objects.filter(
            user__profile_completed=True,
            working_methodology__isnull=False
        ).values_list(
            'working_methodology', flat=True
        ).distinct()
        
        # Filter out empty strings in Python
        context['methodologies'] = sorted([m for m in methodologies if m])
        return context

class TherapistDetailView(DetailView):
    model = Psychotherapist
    template_name = 'psychotherapists/therapist_detail.html'
    context_object_name = 'therapist'

    def get_queryset(self):
        return Psychotherapist.objects.filter(
            user__profile_completed=True
        ).select_related(
            'user',
            'working_methodology'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        therapist = self.get_object()
        
        # Add additional context data
        context.update({
            'full_name': therapist.user.get_full_name(),
            'age': therapist.get_age(),
            'education': therapist.get_education_display(),
            'gender': therapist.get_gender_display(),
            'methodology': therapist.working_methodology.name,
            'experience': therapist.experience,
            'price': therapist.price,
            'about': therapist.about,
            'image': therapist.image,
            'phone': therapist.user.phone_number,
            'email': therapist.user.email,
        })
        return context

class TherapistSearchView(ListView):
    model = Psychotherapist
    template_name = 'psychotherapists/therapist_list.html'
    context_object_name = 'therapists'
    paginate_by = 9

    def get_queryset(self):
        queryset = Psychotherapist.objects.filter(
            user__profile_completed=True
        ).select_related(
            'user',
            'working_methodology'
        )
        
        q = self.request.GET.get('q')
        methodology = self.request.GET.get('methodology')
        experience = self.request.GET.get('experience')

        if q:
            queryset = queryset.filter(
                Q(user__first_name__icontains=q) |
                Q(user__last_name__icontains=q) |
                Q(working_methodology__name__icontains=q)
            )
        
        if methodology:
            queryset = queryset.filter(working_methodology__name=methodology)
        
        if experience:
            queryset = queryset.filter(experience__gte=int(experience))
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get unique methodologies for the filter dropdown
        methodologies = Psychotherapist.objects.filter(
            user__profile_completed=True,
            working_methodology__isnull=False
        ).values_list(
            'working_methodology', flat=True
        ).distinct()
        
        # Filter out empty strings in Python
        context['methodologies'] = sorted([m for m in methodologies if m])
        return context
