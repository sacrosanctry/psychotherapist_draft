from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User

class Criterion(models.Model):
    """
    Stores criteria that both therapists and clients will rate.
    Each criterion has a name, description, and explanations for minimum and maximum scores.
    """
    name = models.CharField(
        max_length=255,
        verbose_name=_('Criterion Name'),
        help_text=_('Name of the criterion (e.g., "Experience with anxiety")')
    )
    description = models.TextField(
        verbose_name=_('Description'),
        help_text=_('Detailed description of what this criterion means')
    )
    score_meaning_1 = models.TextField(
        verbose_name=_('Score 1 Meaning'),
        help_text=_('What does a score of 1 mean for this criterion? (e.g., "flexible, unstructured approach")'),
        null=True,
        blank=True
    )
    score_meaning_9 = models.TextField(
        verbose_name=_('Score 9 Meaning'),
        help_text=_('What does a score of 9 mean for this criterion? (e.g., "very structured, with a plan and tasks")'),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('Criterion')
        verbose_name_plural = _('Criteria')
    
    def __str__(self):
        return self.name

class CriterionScore(models.Model):
    """
    Stores scores given by users (both therapists and clients) for each criterion.
    Therapists rate how well they meet each criterion.
    Clients rate how important each criterion is for their ideal therapist.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='criterion_scores',
        verbose_name=_('User')
    )
    criterion = models.ForeignKey(
        Criterion,
        on_delete=models.CASCADE,
        related_name='scores',
        verbose_name=_('Criterion')
    )
    score = models.PositiveSmallIntegerField(
        verbose_name=_('Score'),
        help_text=_('Score from 1 to 9'),
        validators=[
            MinValueValidator(1, _('Score must be at least 1')),
            MaxValueValidator(9, _('Score cannot be more than 9'))
        ]
    )

    class Meta:
        verbose_name = _('Criterion Score')
        verbose_name_plural = _('Criterion Scores')
        unique_together = ['user', 'criterion']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.criterion.name}: {self.score}"

    @property
    def is_therapist_score(self):
        """Check if this score is from a therapist"""
        return self.user.user_role == 'therapist'

    @property
    def is_client_score(self):
        """Check if this score is from a client"""
        return self.user.user_role == 'client'

class MatchingResult(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matching_results')
    therapist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_matches')
    score = models.FloatField()
    rank = models.IntegerField()
    
    class Meta:
        unique_together = ('client', 'therapist')
        ordering = ['client', 'rank']
    
    def __str__(self):
        return f"{self.client.get_full_name()} - {self.therapist.get_full_name()}: {self.score:.4f} (rank {self.rank})"
