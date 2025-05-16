from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import User, TherapistClientRelationship

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'user_role', 'is_staff', 'profile_completed')
    list_filter = ('user_role', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    filter_horizontal = ()  # Override to remove groups and permissions
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('User Type', {'fields': ('user_role',)}),
        ('Status', {'fields': ('is_active', 'is_staff')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'user_role'),
        }),
    )

# @admin.register(Client)
# class ClientAdmin(admin.ModelAdmin):
#     list_display = ('user', 'get_full_name')
#     search_fields = ('user__username', 'user__first_name', 'user__last_name')
#     list_filter = ('user__is_active',)
    
#     def get_full_name(self, obj):
#         return obj.user.get_full_name()
#     get_full_name.short_description = 'Full Name'

@admin.register(TherapistClientRelationship)
class TherapistClientRelationshipAdmin(admin.ModelAdmin):
    list_display = ('therapist', 'client', 'start_date', 'is_active')
    list_filter = ('is_active', 'start_date')
    search_fields = ('therapist__user__username', 'client__user__username')
