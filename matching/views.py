from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .forms import ClientMatchingForm, TherapistMatchingForm
from .matching_algorithm import get_client_matching_data, run_algorithm, create_mpp_matrices, calculate_local_weights #, get_therapist_matching_data
from users.models import User  # Use our custom User model
from .models import Criterion, MatchingResult
from psychotherapists.models import Psychotherapist
from matching.models import CriterionScore

# Create your views here.

@login_required
def client_matching_form(request):
    """View for clients to rate their preferences"""
    if request.user.user_role != 'client':
        messages.error(request, _('This form is only for clients.'))
        return redirect('users:client_account')
    
    if request.method == 'POST':
        form = ClientMatchingForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            request.user.survey_done = True
            request.user.save()
            messages.success(request, _('Your preferences have been saved.'))
            return redirect('users:client_account')
    else:
        form = ClientMatchingForm(user=request.user)
    
    # Get criteria for display
    criteria = list(Criterion.objects.all().order_by('id'))
    
    return render(request, 'matching/client_matching_form.html', {
        'form': form,
        'criteria': criteria,
        'intro_text': form.intro_text
    })

@login_required
def therapist_matching_form(request):
    """View for therapists to rate themselves"""
    if request.user.user_role != 'therapist':
        messages.error(request, _('This form is only for therapists.'))
        return redirect('users:therapist_account')
    
    if request.method == 'POST':
        form = TherapistMatchingForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            request.user.survey_done = True
            request.user.save()
            messages.success(request, _('Your ratings have been saved.'))
            return redirect('users:therapist_account')
    else:
        form = TherapistMatchingForm(user=request.user)
    
    # Get criteria for display
    criteria = list(Criterion.objects.all().order_by('id'))
    
    return render(request, 'matching/therapist_matching_form.html', {
        'form': form,
        'criteria': criteria,
        'intro_text': form.intro_text
    })

@login_required
def test_matching_data(request):
    """View for testing the matching algorithm with debug output"""
    if request.user.user_role != 'client':
        messages.error(request, _('This view is only for clients.'))
        return redirect('users:client_account')
    
    if not request.user.survey_done:
        messages.error(request, _('Please complete the matching survey first.'))
        return redirect('matching:client_matching_form')
    
    # Get client and therapist scores
    client_scores, therapist_scores = get_client_matching_data(request.user)
    
    # Get criteria for display
    criteria = list(Criterion.objects.all().order_by('id'))
    
    # Get client scores as a list
    client_score_list = list(
        CriterionScore.objects.filter(user=request.user)
        .order_by('criterion_id')
        .values_list('score', flat=True)
    )
    
    # Run the algorithm
    ranked_therapist_ids, ranked_weights = run_algorithm(request.user)
    
    # Get therapist details
    therapists = Psychotherapist.objects.filter(
        user_id__in=ranked_therapist_ids
    ).select_related(
        'user',
        'working_methodology'
    )
    
    # Sort therapists according to the ranking
    therapists = sorted(
        therapists,
        key=lambda x: ranked_therapist_ids.index(x.user_id)
    )
    
    # Get therapist names for display
    therapist_names = {
        therapist.user_id: therapist.user.get_full_name()
        for therapist in therapists
    }
    
    # Create matrices for display
    expert_matrix, criteria_matrices, alternative_matrices = create_mpp_matrices(client_scores, therapist_scores)
    
    # Calculate weights for each matrix
    expert_weights, _ = calculate_local_weights(expert_matrix)
    
    criteria_weights = {}
    for expert_id, matrix in criteria_matrices.items():
        weights, _ = calculate_local_weights(matrix)
        criteria_weights[expert_id] = weights
    
    alternative_weights = {}
    for (expert_id, criterion_idx), matrix in alternative_matrices.items():
        weights, _ = calculate_local_weights(matrix)
        alternative_weights[(expert_id, criterion_idx)] = weights
    
    context = {
        'client_scores': client_scores,
        'therapist_scores': therapist_scores,
        'ranked_therapists': therapists,
        'ranked_weights': ranked_weights,
        'criteria': criteria,
        'client_score_list': client_score_list,
        'therapist_names': therapist_names,
        'client_id': request.user.id,
        'raw_data': {
            'client_scores_dict': client_scores,
            'therapist_scores_dict': therapist_scores
        },
        'expert_matrix': expert_matrix,
        'expert_weights': expert_weights,
        'criteria_matrices': criteria_matrices,
        'criteria_weights': criteria_weights,
        'alternative_matrices': alternative_matrices,
        'alternative_weights': alternative_weights,
        'ranked_therapist_ids': ranked_therapist_ids,
    }
    
    return render(request, 'matching/test_matching.html', context)
