from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_role', 'client')  # Default role for superuser
        extra_fields.setdefault('profile_completed', True)  # Superusers have completed profiles
        extra_fields.setdefault('survey_done', False)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser):
    """
    Custom user model that extends Django's built-in AbstractBaseUser.
    This model stores all user information for both clients and therapists.
    """
    USER_ROLE_CHOICES = (
        ('client', _('Client')),
        ('therapist', _('Psychotherapist')),
    )
    
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    phone_number = models.CharField(_('phone number'), max_length=15, blank=True)
    
    user_role = models.CharField(
        max_length=10,
        choices=USER_ROLE_CHOICES,
        default='client',
        verbose_name=_('User Role'),
        help_text=_('User role in the system')
    )
    
    profile_completed = models.BooleanField(
        default=False,
        verbose_name=_('Profile Completed'),
        help_text=_('Indicates if the user has completed their profile')
    )
    
    survey_done = models.BooleanField(
        default=False,
        verbose_name=_('Survey Completed'),
        help_text=_('Whether the user has completed the matching survey')
    )
    
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_superuser = models.BooleanField(_('superuser status'), default=False)
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    def __str__(self):
        return f"{self.email} ({self.get_user_role_display()})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name
    
    def has_perm(self, perm, obj=None):
        return self.is_superuser
    
    def has_module_perms(self, app_label):
        return self.is_superuser
    
    def save(self, *args, **kwargs):
        # Set profile_completed based on user_role
        if self._state.adding:  # Only on creation
            if self.user_role == 'client':
                self.profile_completed = True
            elif self.user_role == 'therapist':
                self.profile_completed = False
        super().save(*args, **kwargs)

class TherapistClientRelationship(models.Model):
    """
    Through model to manage the relationship between therapists and clients
    """
    therapist = models.ForeignKey(
        'psychotherapists.Psychotherapist',
        on_delete=models.CASCADE
    )
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_role': 'client'}
    )
    start_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('therapist', 'client')
        verbose_name = _('Therapist-Client Relationship')
        verbose_name_plural = _('Therapist-Client Relationships')
    
    def __str__(self):
        return f"{self.therapist} - {self.client.get_full_name()}"