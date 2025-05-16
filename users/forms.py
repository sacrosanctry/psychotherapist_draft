from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from users.models import User
from psychotherapists.models import Psychotherapist, WorkingMethodology

class BaseUserRegistrationForm(UserCreationForm):
    """
    Base form for user registration with common fields
    """
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to password fields
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        
        # Update help texts
        self.fields['password1'].help_text = _('''
            Your password must contain at least 8 characters.
            Your password can't be too similar to your other personal information.
            Your password can't be a commonly used password.
            Your password can't be entirely numeric.
        ''')
        self.fields['password2'].help_text = _('Enter the same password as before, for verification.')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_("This email is already registered."))
        return email

class ClientRegistrationForm(BaseUserRegistrationForm):
    """
    Form for client registration
    """
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_role = 'client'
        user.profile_completed = True  # Clients don't need additional profile
        if commit:
            user.save()
        return user

class TherapistRegistrationForm(BaseUserRegistrationForm):
    """
    Form for therapist registration - only basic user info.
    Creates a User instance with role='therapist' and profile_completed=False.
    The Psychotherapist instance will be created only after completing the profile.
    """
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_role = 'therapist'
        user.profile_completed = False  # Profile is not complete until therapist info is filled
        if commit:
            user.save() # Not creating empty therapist instance here, only User instance (therapist is created in the admin panel after filling form)
        return user

class TherapistProfileForm(forms.ModelForm):
    """
    Form for completing therapist profile after registration
    """
    class Meta:
        model = Psychotherapist
        fields = (
            'birth_date', 'gender', 'about', 'working_methodology',
            'education_institution', 'education_start_year', 'education_end_year',
            'experience', 'price', 'image'
        )
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'about': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'working_methodology': forms.Select(attrs={'class': 'form-control'}),
            'education_institution': forms.TextInput(attrs={'class': 'form-control'}),
            'education_start_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'education_end_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'experience': forms.NumberInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class UserUpdateForm(forms.ModelForm):
    """
    Form for updating basic user information
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

class PsychotherapistForm(forms.ModelForm):
    class Meta:
        model = Psychotherapist
        fields = ['birth_date', 'gender', 'about', 'working_methodology', 
                 'education_institution', 'education_start_year', 'education_end_year',
                 'experience', 'price', 'image']
        widgets = {
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'about': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'working_methodology': forms.Select(attrs={'class': 'form-control'}),
            'education_institution': forms.TextInput(attrs={'class': 'form-control'}),
            'education_start_year': forms.NumberInput(attrs={'class': 'form-control', 'min': 1940}),
            'education_end_year': forms.NumberInput(attrs={'class': 'form-control', 'min': 1940}),
            'experience': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png'}),
        }
        error_messages = {
            'birth_date': {
                'required': _('Please enter your birth date.'),
                'invalid': _('Please enter a valid date in YYYY-MM-DD format.'),
            },
            'gender': {
                'required': _('Please select your gender.'),
            },
            'about': {
                'required': _('Please tell us about yourself.'),
            },
            'working_methodology': {
                'required': _('Please select your working methodology.'),
            },
            'education_institution': {
                'required': _('Please enter your educational institution.'),
            },
            'education_start_year': {
                'required': _('Please enter your education start year.'),
                'invalid': _('Please enter a valid year.'),
            },
            'education_end_year': {
                'required': _('Please enter your education end year.'),
                'invalid': _('Please enter a valid year.'),
            },
            'experience': {
                'required': _('Please enter your years of experience.'),
                'invalid': _('Please enter a valid number of years.'),
                'min_value': _('Experience years cannot be negative.'),
            },
            'price': {
                'required': _('Please enter your session price.'),
                'invalid': _('Please enter a valid price.'),
                'min_value': _('Price must be greater than 0.'),
            },
        }
