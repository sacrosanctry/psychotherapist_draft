from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import JSONField
from users.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
import os
import datetime
from dateutil.relativedelta import relativedelta
from PIL import Image
from django.core.files.uploadedfile import UploadedFile

def get_current_year():
    return datetime.datetime.now().year

def get_min_birth_date():
    # Minimum age: 25 years (must be at least 25 to be a therapist)
    # Calculate date 25 years ago from today
    today = datetime.datetime.now().date()
    return today - relativedelta(years=25)

def get_max_birth_date():
    # Maximum age: 80 years
    # Calculate date 80 years ago from today
    today = datetime.datetime.now().date()
    return today - relativedelta(years=80)

def validate_image_file(value):
    """Validate that the uploaded file is an image"""
    if isinstance(value, UploadedFile):
        try:
            # Try to open the image with PIL
            img = Image.open(value)
            img.verify()  # Verify it's actually an image
            
            # Reset file pointer after verification
            value.seek(0)
            
            # Check if the format is supported (only JPEG and PNG)
            if img.format.lower() not in ['jpeg', 'jpg', 'png']:
                raise ValidationError(_('Unsupported image format. Please upload a JPEG or PNG image.'))
                
        except Exception as e:
            raise ValidationError(_('Invalid image file. Please upload a valid image file.'))
    return value

class WorkingMethodology(models.Model):
    name = models.CharField(max_length=255, unique=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Working Methodology')
        verbose_name_plural = _('Working Methodologies')

class Psychotherapist(models.Model):
    """
    Model for psychotherapists that extends the base User model.
    This model contains all therapist-specific information.
    """
    GENDER_CHOICES = (
        ('M', _('Male')),
        ('F', _('Female')),
    )
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='therapist',
        limit_choices_to={'user_role': 'therapist'}
    )
    
    birth_date = models.DateField(
        verbose_name=_('Birth Date'),
        help_text=_('Your date of birth (you must be at least 25 years old)')
    )
    
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        verbose_name=_('Gender'),
        help_text=_('Select your gender'),
        # default=''  # Add default empty value
    )
    
    about = models.TextField(   
        verbose_name=_('About me'),
        help_text=_('Tell potential clients about yourself, your approach, and experience'),
        # default=''  # Add default empty value
    )
    
    working_methodology = models.ForeignKey(
        WorkingMethodology,
        on_delete=models.PROTECT,
        verbose_name=_('Primary Working Methodology'),
        help_text=_('Select your main therapeutic approach')
    )
    
    education_institution = models.CharField(
        max_length=255,
        verbose_name=_('Educational Institution'),
        help_text=_('Name of your main educational institution'),
        # default=''  # Add default empty value
    )
    
    education_start_year = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1940, message=_('Education start year must be between 1940 and current year')),
            MaxValueValidator(get_current_year, message=_('Education start year cannot be in the future'))
        ],
        verbose_name=_('Education Start Year'),
        help_text=_('Year when your education started'),
        # null=True,  # Allow null for initial creation
        # blank=True  # Allow blank for initial creation
    )
    
    education_end_year = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1940, message=_('Education end year must be between 1940 and current year')),
            MaxValueValidator(get_current_year, message=_('Education end year cannot be in the future'))
        ],
        verbose_name=_('Education End Year'),
        help_text=_('Year when your education ended'),
        # null=True,  # Allow null for initial creation
        # blank=True  # Allow blank for initial creation
    )
    
    experience = models.PositiveIntegerField(
        validators=[
            MinValueValidator(0, message=_('Experience years cannot be negative')),
            MaxValueValidator(100, message=_('Experience years seems too high'))
        ],
        help_text=_('Years of professional experience'),
        verbose_name=_('Years of Experience'),
        # default=0  # Add default value
    )
    
    price = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1, message=_('Price must be greater than 0')),
            MaxValueValidator(10000, message=_('Price seems too high'))
        ],
        verbose_name=_('Session Price'),
        help_text=_('Price per session in your local currency'),
        # default=0  # Add default value
    )
    
    image = models.ImageField(
        upload_to='therapist_photos/',
        default='static/img/profile.png',
        verbose_name=_('Profile Photo'),
        help_text=_('Upload your profile photo (JPEG or PNG only)'),
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),
            validate_image_file
        ]
    )

    # is_verified = models.BooleanField(
    #     default=False,
    #     verbose_name=_('Verified Professional'),
    #     help_text=_('Indicates if the therapist has been verified by the platform')
    # )
    
    # is_available = models.BooleanField(
    #     default=True,
    #     verbose_name=_('Available for New Clients'),
    #     help_text=_('Indicates if the therapist is currently accepting new clients')
    # )
    
    class Meta:
        verbose_name = _('Psychotherapist')
        verbose_name_plural = _('Psychotherapists')
        ordering = ['user__first_name', 'user__last_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.working_methodology.name}"
    
    def is_profile_complete(self):
        """
        Check if all required fields for a complete therapist profile are filled
        """
        required_fields = {
            'birth_date': bool(self.birth_date),
            'gender': bool(self.gender),
            'about': bool(self.about and self.about.strip()),
            'working_methodology': bool(self.working_methodology_id),  # Check ID instead of related object
            'education_institution': bool(self.education_institution and self.education_institution.strip()),
            'education_start_year': bool(self.education_start_year),
            'education_end_year': bool(self.education_end_year),
            'experience': bool(self.experience),
            'price': bool(self.price),
            # 'image': bool(self.image and self.image != 'static/img/profile.png'),
        }
        
        # Check if user's basic info is complete
        user_fields = {
            'first_name': bool(self.user.first_name and self.user.first_name.strip()),
            'last_name': bool(self.user.last_name and self.user.last_name.strip()),
            'phone_number': bool(self.user.phone_number and self.user.phone_number.strip()),
        }
        
        return all(required_fields.values()) and all(user_fields.values())
    
    def save(self, *args, **kwargs):
        self.full_clean()  # Run validation before saving
        
        # Update user's profile_completed status based on profile completion
        profile_complete = self.is_profile_complete()
        if self.user.profile_completed != profile_complete:
            self.user.profile_completed = profile_complete
            self.user.save(update_fields=['profile_completed'])
            
        super().save(*args, **kwargs)
    
    def get_education_display(self):
        """Helper method to format education for display"""
        if not self.education_institution:
            return _("No education information provided")
        
        if self.education_end_year:
            return f"{self.education_institution} ({self.education_start_year}-{self.education_end_year})"
        return f"{self.education_institution} ({self.education_start_year}-present)"
    
    def get_age(self):
        """Calculate and return the therapist's age"""
        if self.birth_date:
            today = datetime.datetime.now().date()
            return relativedelta(today, self.birth_date).years
        return None
    
    def clean(self):
        # Validate birth date
        if self.birth_date:
            today = datetime.datetime.now().date()
            age = relativedelta(today, self.birth_date).years
            
            if age < 25:
                raise ValidationError({
                    'birth_date': _('You must be at least 25 years old to register as a therapist')
                })
            if age > 80:
                raise ValidationError({
                    'birth_date': _('Invalid birth date')
                })
            
            # Check if education years are after birth date
            birth_year = self.birth_date.year
            if self.education_start_year and self.education_start_year < birth_year:
                raise ValidationError({
                    'education_start_year': _('Education start year cannot be before your birth year')
                })

        # Check if end year is after start year
        if self.education_end_year and self.education_start_year and self.education_end_year < self.education_start_year:
            raise ValidationError({
                'education_end_year': _('Education end year cannot be earlier than start year')
            })
        
        # Check if experience is reasonable compared to education years
        if self.education_start_year:  # Only check if we have a start year
            current_year = get_current_year()
            if self.education_end_year:
                max_experience = current_year - self.education_end_year
            else:
                max_experience = current_year - self.education_start_year
                
            if self.experience > max_experience:
                raise ValidationError({
                    'experience': _('Experience years cannot be greater than years since education')
                })
        
        # # Check if profile is complete and raise warning if not
        # if not self.is_profile_complete():
        #     raise ValidationError(_('Please fill in all required fields to complete your profile'))
        
        # Validate image if it's being changed
        if self.image and self.image != 'static/img/profile.png':
            validate_image_file(self.image)