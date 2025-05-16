from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Criterion, CriterionScore

class BaseMatchingForm(forms.ModelForm):
    """Base form for rating criteria"""
    class Meta:
        model = CriterionScore
        fields = ['score']
        widgets = {
            'score': forms.RadioSelect(attrs={'class': 'rating-radio'})
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.criterion = kwargs.pop('criterion', None)
        super().__init__(*args, **kwargs)
        self.fields['score'].label = self.criterion.name
        self.fields['score'].help_text = self._get_help_text()

    def _get_help_text(self):
        help_text = self.criterion.description
        return help_text

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.user
        instance.criterion = self.criterion
        if commit:
            instance.save()
        return instance

class ClientMatchingForm(forms.Form):
    """Form for clients to rate their preferences"""
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Get all criteria
        self.criteria = list(Criterion.objects.all().order_by('id'))
        
        # Add fields for each criterion
        for criterion in self.criteria:
            field_name = f'criterion_{criterion.id}'
            field = forms.ChoiceField(
                label=criterion.name,
                choices=[(i, str(i)) for i in range(1, 10)],
                widget=forms.RadioSelect,
                required=True
            )
            field.criterion = criterion  # Attach criterion to field
            field.help_text = criterion.description
            self.fields[field_name] = field
        
        # Add intro text
        self.intro_text = _("""
        Please rate each criterion on a scale of 1 to 9.
        
        Your ratings will help us match you with therapists who best align with your preferences.
        """)
    
    def save(self):
        """Save the client's preferences"""
        print("Saving client preferences...")  # Debug print
        print(f"Form data: {self.cleaned_data}")  # Debug print
        
        # Delete any existing scores for this user
        CriterionScore.objects.filter(user=self.user).delete()
        
        # Save new scores
        for criterion in self.criteria:
            score_value = int(self.cleaned_data[f'criterion_{criterion.id}'])
            print(f"Saving score for criterion {criterion.id}: {score_value}")  # Debug print
            CriterionScore.objects.create(
                user=self.user,
                criterion=criterion,
                score=score_value
            )
        
        print("All scores saved successfully")  # Debug print

class TherapistMatchingForm(forms.Form):
    """Form for therapists to rate themselves"""
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add introduction text
        self.intro_text = _("""
        Please rate how well each of these characteristics describes you and your therapeutic approach.
        Rate from 1 to 9.
        """)

        # Create a form field for each criterion
        for criterion in Criterion.objects.all():
            field_name = f'criterion_{criterion.id}'
            field = forms.ChoiceField(
                choices=[(i, str(i)) for i in range(1, 10)],
                widget=forms.RadioSelect(attrs={'class': 'rating-radio'}),
                label=criterion.name,
                help_text=criterion.description,
                required=True
            )
            field.criterion = criterion  # Attach criterion to field
            self.fields[field_name] = field

    def save(self):
        for field_name, value in self.cleaned_data.items():
            if field_name.startswith('criterion_'):
                criterion_id = int(field_name.split('_')[1])
                criterion = Criterion.objects.get(id=criterion_id)
                CriterionScore.objects.update_or_create(
                    user=self.user,
                    criterion=criterion,
                    defaults={'score': int(value)}
                ) 