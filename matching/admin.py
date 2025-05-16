from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Criterion, CriterionScore

@admin.register(Criterion)
class CriterionAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'score_meaning_1', 'score_meaning_9')
    search_fields = ('name', 'description', 'score_meaning_1', 'score_meaning_9')
    list_filter = ('name',)
    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        (_('Score Meanings'), {
            'fields': ('score_meaning_1', 'score_meaning_9'),
            'description': _('Explain what scores 1 and 9 mean for this criterion')
        }),
    )

@admin.register(CriterionScore)
class CriterionScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'criterion', 'score', 'is_therapist_score', 'is_client_score')
    list_filter = ('criterion', 'user__user_role')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'criterion__name')
    raw_id_fields = ('user', 'criterion')
    
    def is_therapist_score(self, obj):
        return obj.is_therapist_score
    is_therapist_score.boolean = True
    is_therapist_score.short_description = _('Is Therapist Score')
    
    def is_client_score(self, obj):
        return obj.is_client_score
    is_client_score.boolean = True
    is_client_score.short_description = _('Is Client Score')
