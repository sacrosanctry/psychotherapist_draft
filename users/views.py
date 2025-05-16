from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .forms import ClientRegistrationForm, TherapistRegistrationForm, UserUpdateForm, TherapistProfileForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, CreateView, ListView
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy, reverse
from users.models import User
from psychotherapists.models import Psychotherapist, WorkingMethodology
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator

class HomeView(TemplateView):
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        therapist_list = Psychotherapist.objects.all()
        paginator = Paginator(therapist_list, 9)  # 9 therapists per page
        page = self.request.GET.get('page')
        context['therapists'] = paginator.get_page(page)
        return context

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = None  # Use default authentication form
    
    def get_success_url(self):
        user = self.request.user
        if user.user_role == 'client':
            return reverse_lazy('users:client_account')
        return reverse_lazy('users:therapist_account')
    
    def form_invalid(self, form):
        messages.error(self.request, _('Invalid email or password.'))
        return super().form_invalid(form)

class RegisterChoiceView(TemplateView):
    """
    View for choosing registration type (client or therapist)
    """
    template_name = 'registration/register_choice.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hide_navbar'] = True
        return context

class ClientRegistrationView(CreateView):
    """
    View for client registration
    """
    form_class = ClientRegistrationForm
    template_name = 'registration/client_register.html'
    success_url = reverse_lazy('users:client_account')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hide_navbar'] = True
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, _('Registration successful! Welcome to our platform.'))
        return response

class TherapistRegistrationView(CreateView):
    """
    View for therapist registration - first step
    """
    form_class = TherapistRegistrationForm
    template_name = 'registration/therapist_register.html'
    success_url = reverse_lazy('users:therapist_account')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hide_navbar'] = True
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, _('Registration successful! Please complete your profile.'))
        return response

@login_required
def therapist_account(request):
    if request.user.user_role != 'therapist':
        return redirect('users:client_account')
    
    # Get existing therapist profile if it exists
    therapist = Psychotherapist.objects.filter(user=request.user).first()
    
    # If no therapist instance exists, create one and set profile as incomplete
    if not therapist:
        therapist = Psychotherapist(user=request.user)
        # Don't save the therapist instance yet, as it would fail validation
        request.user.profile_completed = False
        request.user.save()
    
    # If profile is not completed, show the profile completion form
    if not request.user.profile_completed:
        if request.method == 'POST':
            # Create forms with POST data
            user_form = UserUpdateForm(request.POST, instance=request.user)
            therapist_form = TherapistProfileForm(request.POST, request.FILES, instance=therapist)
            
            if user_form.is_valid() and therapist_form.is_valid():
                user_form.save()
                # Save therapist instance only after validation passes
                therapist_form.save()
                if request.user.profile_completed:
                    messages.success(request, _('Your profile has been completed successfully!'))
                return redirect('users:therapist_account')
            else:
                # If forms are invalid, they will be re-rendered with errors
                context = {
                    'user_form': user_form,
                    'form': therapist_form,  # Pass the form with errors
                    'therapist': therapist,
                    'methodologies': WorkingMethodology.objects.all(),
                    'current_year': timezone.now().year,
                    'is_profile_completion': True,
                }
                return render(request, 'accounts/therapist_account.html', context)
        
        # Show profile completion form
        context = {
            'user_form': UserUpdateForm(instance=request.user),
            'form': TherapistProfileForm(instance=therapist),  # Pass empty form for GET request
            'therapist': therapist,
            'methodologies': WorkingMethodology.objects.all(),
            'current_year': timezone.now().year,
            'is_profile_completion': True,
        }
        return render(request, 'accounts/therapist_account.html', context)
    
    # Show the completed profile
    context = {
        'therapist': therapist,
        'is_profile_completion': False,
    }
    return render(request, 'accounts/therapist_account.html', context)

@login_required
def client_account(request):
    if request.user.user_role != 'client':
        return redirect('users:therapist_account')
    
    # Handle edit mode
    if request.method == 'POST' and request.POST.get('edit_mode'):
        request.user.profile_completed = False
        request.user.save()
        return redirect('users:client_account')
    
    # Set profile as completed if it's not already
    if not request.user.profile_completed:
        request.user.profile_completed = True
        request.user.save()
    
    # Get matched therapists from database
    from matching.models import MatchingResult
    from psychotherapists.models import Psychotherapist
    
    matched_therapists = []
    if request.user.survey_done:
        # Get matching results ordered by rank with therapist details
        matching_results = MatchingResult.objects.filter(
            client=request.user
        ).select_related(
            'therapist'
        ).order_by('rank')
        
        print(f"Found {matching_results.count()} matching results")  # Debug print
        
        # Get therapist details
        for result in matching_results:
            therapist = Psychotherapist.objects.filter(
                user=result.therapist
            ).select_related(
                'working_methodology'
            ).first()
            
            if therapist:  # Make sure therapist profile exists
                matched_therapists.append({
                    'therapist': therapist,
                    'user': result.therapist,  # Add the User object
                    'score': result.score,
                    'rank': result.rank,
                    'is_best_match': result.rank == 1
                })
                print(f"Added match: {result.therapist.get_full_name()} with score {result.score}")  # Debug print
    
    context = {
        'matched_therapists': matched_therapists,
        'user': request.user
    }
    print(f"Context: {context}")  # Debug print
    return render(request, 'accounts/client_account.html', context)

class CustomLogoutView(LogoutView):
    next_page = 'home'
    
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, _('You have been successfully logged out.'))
        return super().dispatch(request, *args, **kwargs)

@login_required
def edit_client_profile(request):
    if request.user.user_role != 'client':
        return redirect('users:therapist_account')
    
    if request.method == 'POST':
        # Update user fields
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.phone_number = request.POST.get('phone_number')
        request.user.save()
        
        messages.success(request, _('Your profile has been updated!'))
        return redirect('users:client_account')
    
    return render(request, 'accounts/edit_client_profile.html')

@login_required
def edit_therapist_profile(request):
    if request.user.user_role != 'therapist':
        return redirect('users:client_account')
    
    therapist = get_object_or_404(Psychotherapist, user=request.user)
    
    if request.method == 'POST':
        # Update user fields
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.phone_number = request.POST.get('phone_number')
        request.user.save()
        
        # Update therapist fields
        therapist.birth_date = request.POST.get('birth_date')
        therapist.gender = request.POST.get('gender')
        therapist.about = request.POST.get('about')
        therapist.working_methodology_id = request.POST.get('working_methodology')
        therapist.experience = request.POST.get('experience')
        therapist.education_institution = request.POST.get('education_institution')
        therapist.education_start_year = request.POST.get('education_start_year')
        therapist.education_end_year = request.POST.get('education_end_year') or None
        therapist.price = request.POST.get('price')
        
        # Handle image upload with validation
        if 'image' in request.FILES:
            try:
                # Validate image before assigning
                image = request.FILES['image']
                if not image.content_type.startswith('image/'):
                    messages.error(request, _('Please upload a valid image file (JPEG or PNG).'))
                    return redirect('users:edit_therapist_profile')
                therapist.image = image
            except Exception as e:
                messages.error(request, _('Error uploading image. Please make sure it is a valid image file (JPEG or PNG).'))
                return redirect('users:edit_therapist_profile')
        
        try:
            # Validate and save therapist profile
            therapist.full_clean()
            therapist.save()
            messages.success(request, _('Your profile has been updated!'))
            return redirect('users:therapist_account')
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return redirect('users:edit_therapist_profile')
        except ValueError as e:
            messages.error(request, _('Please enter valid numbers for numeric fields.'))
            return redirect('users:edit_therapist_profile')
    
    context = {
        'methodologies': WorkingMethodology.objects.all(),
        'current_year': timezone.now().year,
        'therapist': therapist,
    }
    return render(request, 'accounts/edit_therapist_profile.html', context)


