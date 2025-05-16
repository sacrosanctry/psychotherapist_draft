from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Psychotherapist, WorkingMethodology
from users.models import User

@admin.register(WorkingMethodology)
class WorkingMethodologyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Psychotherapist)
class PsychotherapistAdmin(admin.ModelAdmin):
    list_display = (
        'get_full_name', 'working_methodology', 'experience', 'price',
        'is_profile_complete'
    )
    list_filter = ('working_methodology', 'user__is_active')
    search_fields = (
        'user__first_name', 'user__last_name', 'user__email',
        'working_methodology__name', 'education_institution'
    )
    readonly_fields = ('get_education_display', 'get_age')
    
    fieldsets = (
        (_('User'), {
            'fields': ('user',)
        }),
        (_('Personal Information'), {
            'fields': (
                'birth_date', 'gender', 'image', 'get_age'
            )
        }),
        (_('Education'), {
            'fields': (
                'education_institution',
                ('education_start_year', 'education_end_year'),
                'get_education_display'
            )
        }),
        (_('Professional Information'), {
            'fields': (
                'about', 'working_methodology', 'experience', 'price'
            )
        }),
    )

    def get_full_name(self, obj):
        return obj.user.get_full_name() if obj.user else '-'
    get_full_name.short_description = _('Full Name')
    get_full_name.admin_order_field = 'user__last_name'

    def get_age(self, obj):
        age = obj.get_age()
        return f"{age} {_('years')}" if age else '-'
    get_age.short_description = _('Age')
    get_age.admin_order_field = 'birth_date'

    def is_profile_complete(self, obj):
        return obj.is_profile_complete()
    is_profile_complete.boolean = True
    is_profile_complete.short_description = _('Profile Complete')

    def get_education_display(self, obj):
        return obj.get_education_display()
    get_education_display.short_description = _('Education')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'working_methodology'
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(user_role='therapist')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change and obj.user:  # If creating new therapist
            obj.user.user_role = 'therapist'
            obj.user.save(update_fields=['user_role'])
        super().save_model(request, obj, form, change)

