from django.db.models import Q
from .models import Criterion, CriterionScore
from users.models import User

def get_client_matching_data(client_user):
    """
    Get matching data for a client to find suitable therapists.
    
    Args:
        client_user: The User instance of the logged-in client
        
    Returns:
        tuple: (client_scores_dict, therapist_scores_dict)
            - client_scores_dict: dict of {client_id: list_of_scores}
            - therapist_scores_dict: dict of {therapist_id: list_of_scores}
    """
    # Get client's scores as a list
    client_scores = list(
        CriterionScore.objects.filter(user=client_user)
        .order_by('criterion_id')
        .values_list('score', flat=True)
    )
    
    # Format client scores in the same way as therapist scores
    client_scores_dict = {client_user.id: client_scores}
    
    # Get all therapists who have completed their survey
    therapists = User.objects.filter(
        user_role='therapist',
        survey_done=True
    )
    
    # Get all therapist scores
    therapist_scores_dict = {}
    for therapist in therapists:
        scores = list(
            CriterionScore.objects.filter(user=therapist)
            .order_by('criterion_id')
            .values_list('score', flat=True)
        )
        if scores:  # Only add if therapist has any scores
            therapist_scores_dict[therapist.id] = scores
    
    print(f"{client_scores_dict=}\n")
    print(f"{therapist_scores_dict=}\n")
    
    return client_scores_dict, therapist_scores_dict

# def get_therapist_matching_data(therapist_user):
#     """
#     Get matching data for a therapist.
    
#     Args:
#         therapist_user: The User instance of the logged-in therapist
        
#     Returns:
#         tuple: (therapist_scores, criteria)
#             - therapist_scores: dict of criterion_id: score for the therapist
#             - criteria: list of Criterion objects in the order they were rated
#     """
#     # Get all criteria in the order they were created
#     criteria = list(Criterion.objects.all().order_by('id'))
#     criterion_ids = [c.id for c in criteria]
    
#     # Get therapist's scores
#     therapist_scores = {}
#     therapist_score_objects = CriterionScore.objects.filter(
#         user=therapist_user,
#         criterion_id__in=criterion_ids
#     ).select_related('criterion')
    
#     for score in therapist_score_objects:
#         therapist_scores[score.criterion_id] = score.score
    
#     print(f"{therapist_scores=}\n")
#     print(f"{criteria=}\n")
    
#     return therapist_scores, criteria 



import re
import numpy as np

float_formatter = "{:.5f}".format
np.set_printoptions(linewidth=np.inf,
                    formatter={'float_kind':float_formatter})

# Значення CIS для різних розмірів матриць
CIS_values = {1: 0, 2: 0, 3: 0.52, 4: 0.89, 5: 1.11, 6: 1.25, 7: 1.35, 8: 1.40, 9: 1.45, 10: 1.49}


def create_mpp_matrices(client_scores_dict, therapist_scores_dict):
    """
    Create three types of pairwise comparison matrices:
    1. Expert matrix (1x1) - since we have one client
    2. Criteria matrix (nxn) - comparing criteria (all equal in our case)
    3. Alternative matrices - one for each criterion, comparing therapists
    
    Args:
        client_scores_dict: dict of {client_id: list_of_scores}
        therapist_scores_dict: dict of {therapist_id: list_of_scores}
        
    Returns:
        tuple: (expert_matrix, criteria_matrices, alternative_matrices)
            - expert_matrix: 1x1 matrix for the single client
            - criteria_matrices: dict of {expert_id: matrix} where matrix is nxn (n=number of criteria)
            - alternative_matrices: dict of {(expert_id, criterion_idx): matrix} where matrix compares therapists
    """
    # Get client scores (we only have one client)
    client_id = next(iter(client_scores_dict.keys()))
    client_scores = client_scores_dict[client_id]
    client_score_length = len(client_scores)
    
    # 1. Create expert matrix (1x1) - since we have one client
    expert_matrix = np.ones((1, 1))  # Just one client, so 1x1 matrix with value 1
    
    # 2. Create criteria matrix (nxn where n is number of criteria)
    # Since all criteria are equivalent, fill with ones
    criteria_matrix = np.ones((client_score_length, client_score_length))
    criteria_matrices = {client_id: criteria_matrix}  # Dict with one matrix for our single client
    
    # Find valid therapists (those with matching score lengths)
    valid_therapist_ids = []
    therapist_score_differences = {}  # Store differences for each therapist
    
    for therapist_id, therapist_scores in therapist_scores_dict.items():
        if len(therapist_scores) == client_score_length:
            valid_therapist_ids.append(therapist_id)
            # Calculate absolute differences between client and therapist scores
            differences = [abs(client_score - therapist_score) 
                         for client_score, therapist_score in zip(client_scores, therapist_scores)]
            therapist_score_differences[therapist_id] = differences
    
    if not valid_therapist_ids:
        return expert_matrix, criteria_matrices, {}
    
    # 3. Create alternative matrices (one for each criterion)
    alternative_matrices = {}
    n_therapists = len(valid_therapist_ids)
    
    # For each criterion
    for criterion_idx in range(client_score_length):
        # Create matrix filled with ones (diagonal)
        matrix = np.ones((n_therapists, n_therapists))
        
        # Get differences for this criterion for all therapists
        criterion_differences = {
            therapist_id: differences[criterion_idx]
            for therapist_id, differences in therapist_score_differences.items()
        }
        
        # Fill the matrix with pairwise comparisons
        for i, therapist1_id in enumerate(valid_therapist_ids):
            for j, therapist2_id in enumerate(valid_therapist_ids):
                if i != j:  # Skip diagonal
                    diff1 = criterion_differences[therapist1_id]
                    diff2 = criterion_differences[therapist2_id]
                    
                    if diff1 < diff2:
                        # If therapist1's difference is less, it's preferred
                        matrix[i, j] = abs(diff2 - diff1) + 1
                        matrix[j, i] = 1 / matrix[i, j]
                    elif diff2 < diff1:
                        # If therapist2's difference is less, it's preferred
                        matrix[j, i] = abs(diff1 - diff2) + 1
                        matrix[i, j] = 1 / matrix[j, i]
                    else:
                        # If differences are equal, both are equally preferred
                        matrix[i, j] = 1
                        matrix[j, i] = 1
        
        alternative_matrices[(client_id, criterion_idx)] = matrix
    
    print(f"Expert matrix (1x1):\n{expert_matrix}\n")
    print(f"Criteria matrix ({client_score_length}x{client_score_length}):\n{criteria_matrix}\n")
    print(f"Number of alternative matrices: {len(alternative_matrices)}")
    for (expert_id, criterion_idx), matrix in alternative_matrices.items():
        print(f"\nAlternative matrix for expert {expert_id}, criterion {criterion_idx + 1}:")
        print(f"Client score for this criterion: {client_scores[criterion_idx]}")
        print("Therapist differences from client score:")
        for therapist_id in valid_therapist_ids:
            print(f"Therapist {therapist_id}: {therapist_score_differences[therapist_id][criterion_idx]}")
        print("Pairwise comparison matrix:")
        print(matrix)
    
    return expert_matrix, criteria_matrices, alternative_matrices


def calculate_lambda_CI_CR(matrix, max_iterations=100):
    """Обчислення максимального характеристичного числа (lambda_max) методом простої векторної ітерації,
    обчислення індекса (CI) та відношення узгодженості (CR)"""
    n = matrix.shape[0]
    x = np.ones(n)  # Початковий вектор x^(0)

    prev_lambda_values = np.zeros(n)  # Попереднє значення для перевірки зупинки
    tolerance = 1e-5  # Точність до 5-го знаку після коми

    vectors = [x.copy()]  # Результати векторів
    lambda_values = []

    for _ in range(max_iterations):
        x_new = np.dot(matrix, x)  # Множення матриці на вектор
        lambda_vec = x_new / x  # x^(m+1) / x^(m)

        vectors.append(x_new.copy())
        lambda_values.append(lambda_vec.copy())

        # Перевірка на зупинку, якщо різниця між ітераціями < 1e-5
        if np.all(np.abs(lambda_vec - prev_lambda_values) < tolerance):
            break

        prev_lambda_values = lambda_vec
        x = x_new

    # Визначення lambda_max як середнє значення останнього вектора lambda_vec
    lambda_max = np.mean(lambda_vec)

    CI = (lambda_max - n) / (n - 1) if n > 1 else 0
    CIS = CIS_values.get(n, 0)
    CR = CI / CIS if CIS != 0 else 0

    return np.array(vectors).T, np.array(lambda_values).T, lambda_max, CI, CR


def calculate_local_weights(matrix):
    """Обчислення вагових коефіцієнтів методом середніх геометричних"""
    k = matrix.shape[0]

    # Обчислення середнього геометричного для кожного рядка
    geometric_means = np.prod(matrix, axis=1) ** (1 / k)

    # Нормування середніх геометричних
    weights = geometric_means / np.sum(geometric_means)

    return weights, geometric_means


def calculate_expert_global_weights(criteria_matrices, alternative_matrices):
    """Обчислення глобальних вагових коефіцієнтів експертів"""
    expert_global_weights = []
    for expert in range(1, experts_count + 1):
        criteria_weights = calculate_local_weights(criteria_matrices[expert])[0]  # w_j(s)
        alternative_weights = []

        for criterion in range(1, criteria_count + 1):
            alternative_weights.append(calculate_local_weights(alternative_matrices[(expert, criterion)])[0])

        alternative_weights = np.array(alternative_weights)  # p_ij(s)

        global_weights = np.dot(np.diag(criteria_weights), alternative_weights)  # w_j(s) * p_ij(s)
        print(f"global_weights expert {expert}\n{global_weights}")
        global_sum = np.sum(global_weights, axis=0)  # ∑ w_j(s) * p_ij(s)

        expert_global_weights.append(global_sum)

    expert_global_weights = np.array(expert_global_weights)

    return expert_global_weights


def run_algorithm(client_user):
    """
    Run the matching algorithm for a client to find suitable therapists.
    
    Args:
        client_user: The User instance of the logged-in client
        
    Returns:
        tuple: (ranked_therapist_ids, ranked_weights)
            - ranked_therapist_ids: list of therapist IDs in order of preference
            - ranked_weights: list of corresponding weights
    """
    # Get client and therapist scores
    client_scores_dict, therapist_scores_dict = get_client_matching_data(client_user)
    
    # Create matrices for the AHP algorithm
    expert_matrix, criteria_matrices, alternative_matrices = create_mpp_matrices(
        client_scores_dict, therapist_scores_dict
    )
    
    # Get valid therapist IDs directly from therapist_scores_dict
    valid_therapist_ids = list(therapist_scores_dict.keys())
    if not valid_therapist_ids:
        return [], []
    
    print("МПП експертів:")
    vectors, lambda_values, lambda_max, CI, CR = calculate_lambda_CI_CR(expert_matrix)
    print(f"Максимальне характеристичне число: {lambda_max:.5f}")
    print(f"Індекс узгодженості CI: {CI:.5f}")
    print(f"Коефіцієнт узгодженості CR: {CR:.5f}")

    expert_weights, _ = calculate_local_weights(expert_matrix)
    print("Вагові коефіцієнти експертів:", expert_weights)
    
    print("\n\nМПП критеріїв:")
    criteria_weights = {}  # Store weights for each expert
    for expert_id, matrix in criteria_matrices.items():
        print(f"Експерт {expert_id}:")
        vectors, lambda_values, lambda_max, CI, CR = calculate_lambda_CI_CR(matrix)
        print(f"Максимальне характеристичне число: {lambda_max:.5f}")
        print(f"Індекс узгодженості CI: {CI:.5f}")
        print(f"Коефіцієнт узгодженості CR: {CR:.5f}")

        weights, _ = calculate_local_weights(matrix)
        criteria_weights[expert_id] = weights
        print("Вагові коефіцієнти критеріїв:", weights, "\n")

    print("\n\nМПП альтернатив:")
    alternative_weights = {}  # Store weights for each criterion
    for (expert_id, criterion_idx), matrix in alternative_matrices.items():
        print(f"Експерт {expert_id}, Критерій {criterion_idx + 1}:")
        vectors, lambda_values, lambda_max, CI, CR = calculate_lambda_CI_CR(matrix)
        print(f"Максимальне характеристичне число: {lambda_max:.5f}")
        print(f"Індекс узгодженості CI: {CI:.5f}")
        print(f"Коефіцієнт узгодженості CR: {CR:.5f}")

        weights, _ = calculate_local_weights(matrix)
        alternative_weights[(expert_id, criterion_idx)] = weights
        print("Вагові коефіцієнти альтернатив:", weights, "\n")

    # Calculate global weights for each criterion
    global_weights = np.zeros(len(valid_therapist_ids))
    for criterion_idx, weights in alternative_weights.items():
        # Since all criteria are equal, we just average the weights
        global_weights += weights / len(alternative_weights)

    # Create a dictionary mapping therapist IDs to their global weights
    therapist_weights = dict(zip(valid_therapist_ids, global_weights))
    
    # Sort therapists by their weights in descending order
    ranked_therapist_ids = sorted(
        therapist_weights.keys(),
        key=lambda x: therapist_weights[x],
        reverse=True
    )
    ranked_weights = [therapist_weights[tid] for tid in ranked_therapist_ids]
    
    print("\n\nГлобальні пріоритети альтернатив (ранжовані):")
    for therapist_id, weight in zip(ranked_therapist_ids, ranked_weights):
        print(f"Терапевт {therapist_id}: {weight:.5f}")
    
    print(f"\nНайкращий терапевт: {ranked_therapist_ids[0]}")
    
    # Save results to database
    from .models import MatchingResult
    
    # Delete old results for this client
    MatchingResult.objects.filter(client=client_user).delete()
    
    # Save new results
    for rank, (therapist_id, weight) in enumerate(zip(ranked_therapist_ids, ranked_weights), 1):
        therapist = User.objects.get(id=therapist_id)
        MatchingResult.objects.create(
            client=client_user,
            therapist=therapist,
            score=weight,
            rank=rank
        )
    
    return ranked_therapist_ids, ranked_weights

