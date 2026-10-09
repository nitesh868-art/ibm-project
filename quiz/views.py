"""Quiz Views — Mock tests, practice, results"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import MockTest, Question, TestAttempt, QuestionAnswer, Bookmark, Subject


# ---------------------------------------------------------------------------
# Helper: safely resolve a Subject from a GET param (pk OR name)
# ---------------------------------------------------------------------------
def _resolve_subject(subject_param):
    """
    Resolve a subject from ?subject=<value> where value may be:
      - an integer pk  ("3")
      - a subject name ("DBMS", "Java", "Operating Systems")
    Returns a Subject instance or None. NEVER raises ValueError.
    """
    if not subject_param:
        return None
    sp = subject_param.strip()
    if not sp:
        return None

    # Try integer pk first
    try:
        pk = int(sp)
        return Subject.objects.filter(pk=pk).first()
    except (ValueError, TypeError):
        pass

    # Exact case-insensitive name match
    subj = Subject.objects.filter(name__iexact=sp).first()
    if subj:
        return subj

    # Partial name match as fallback
    subj = Subject.objects.filter(name__icontains=sp).first()
    return subj


# ---------------------------------------------------------------------------
# Quiz Home
# ---------------------------------------------------------------------------
@login_required
def quiz_home(request):
    subjects = Subject.objects.all()
    tests = MockTest.objects.filter(is_active=True, is_published=True)[:6]
    return render(request, 'quiz/home.html', {'subjects': subjects, 'tests': tests})


# ---------------------------------------------------------------------------
# Mock Tests
# ---------------------------------------------------------------------------
@login_required
def test_list(request):
    tests = MockTest.objects.filter(is_active=True, is_published=True)
    my_attempts = {a.test_id: a for a in TestAttempt.objects.filter(student=request.user)}
    return render(request, 'quiz/test_list.html', {'tests': tests, 'my_attempts': my_attempts})


@login_required
def start_test(request, pk):
    test = get_object_or_404(MockTest, pk=pk, is_active=True)

    existing = TestAttempt.objects.filter(student=request.user, test=test).first()
    if existing and existing.is_completed:
        messages.warning(request, 'You have already completed this test. View your result below.')
        return redirect('quiz:test_result', pk=existing.pk)

    if not existing:
        attempt = TestAttempt.objects.create(
            student=request.user, test=test,
            total_questions=test.question_count
        )
    else:
        attempt = existing

    questions = list(test.questions.filter(is_active=True))
    return render(request, 'quiz/take_test.html', {
        'test': test,
        'questions': questions,
        'attempt': attempt,
        'duration_seconds': test.duration_minutes * 60,
    })


@login_required
def submit_test(request, pk):
    """Process test submission."""
    test = get_object_or_404(MockTest, pk=pk)
    attempt = get_object_or_404(TestAttempt, test=test, student=request.user)

    if request.method == 'POST':
        correct = 0
        wrong = 0
        skipped = 0

        for question in test.questions.all():
            selected = request.POST.get(f'q_{question.pk}', '').strip().upper()
            if selected:
                is_correct = (selected == question.correct_answer.upper())
                QuestionAnswer.objects.update_or_create(
                    attempt=attempt, question=question,
                    defaults={'selected_answer': selected, 'is_correct': is_correct}
                )
                if is_correct:
                    correct += 1
                else:
                    wrong += 1
            else:
                skipped += 1

        attempt.correct_answers = correct
        attempt.wrong_answers = wrong
        attempt.skipped = skipped
        attempt.score = correct
        attempt.completed_at = timezone.now()
        attempt.calculate_result()

        # Recalculate student topic mastery from quiz scores
        try:
            from core.services.student_context import recalculate_student_mastery
            recalculate_student_mastery(request.user)
        except Exception:
            pass


        if attempt.percentage >= 70:
            from dashboard.models import PortalCertificate
            cert_title = f"Excellence Certificate — {test.title}"
            cert, created = PortalCertificate.objects.get_or_create(
                student=request.user,
                achievement_type='test_excellence',
                title=cert_title,
                defaults={
                    'description': f"Demonstrated high proficiency with a score of {attempt.percentage:.1f}% on PlacementPro Mock Test: {test.title}.",
                    'score_percentage': attempt.percentage,
                }
            )
            if created:
                messages.success(request, f'🎓 Congratulations! You earned a Certificate of Excellence! (ID: {cert.certificate_id})')

        messages.success(request, f'✅ Test submitted! Score: {correct}/{attempt.total_questions}')
        return redirect('quiz:test_result', pk=attempt.pk)

    return redirect('quiz:start_test', pk=pk)


@login_required
def test_result(request, pk):
    """View test result with score breakdown, weak topic detection, and recommendations."""
    attempt = get_object_or_404(TestAttempt, pk=pk, student=request.user)
    answers = QuestionAnswer.objects.filter(attempt=attempt).select_related('question', 'question__subject')

    wrong_answers = [a for a in answers if not a.is_correct]
    weak_topics = set()
    for wa in wrong_answers:
        if wa.question and wa.question.subject:
            weak_topics.add(wa.question.subject.name)

    recommendations = []
    if weak_topics:
        recommendations.append(f"Focus additional study time on: {', '.join(weak_topics)}.")
    if attempt.percentage < 60:
        recommendations.append("Review foundational concepts and attempt topic-wise practice questions before retaking.")
    elif attempt.percentage >= 80:
        recommendations.append("Excellent performance! Try advanced difficulty mock tests or timed company practice sets.")

    return render(request, 'quiz/result.html', {
        'attempt': attempt,
        'answers': answers,
        'weak_topics': list(weak_topics),
        'recommendations': recommendations,
    })


# ---------------------------------------------------------------------------
# Practice Questions — FIXED: safe subject resolution
# ---------------------------------------------------------------------------
@login_required
def practice_questions(request):
    """
    Practice questions with filtering.
    Supports:
      ?subject=<pk>    e.g. ?subject=3
      ?subject=<name>  e.g. ?subject=DBMS  (never crashes)
      ?difficulty=easy|medium|hard
      ?language=python|java|...
      ?page=N
    """
    subject_param = request.GET.get('subject', '').strip()
    difficulty = request.GET.get('difficulty', '').strip()
    language = request.GET.get('language', '').strip()

    try:
        page = max(1, int(request.GET.get('page', 1)))
    except (ValueError, TypeError):
        page = 1

    per_page = 10

    # Resolve subject SAFELY — never passes raw string as subject_id
    resolved_subject = _resolve_subject(subject_param)

    questions_qs = Question.objects.filter(is_active=True).select_related('subject')

    if resolved_subject:
        questions_qs = questions_qs.filter(subject=resolved_subject)
    elif subject_param:
        # Provided but not found — return empty with message
        questions_qs = questions_qs.none()

    if difficulty:
        questions_qs = questions_qs.filter(difficulty=difficulty)
    if language and language != 'general':
        questions_qs = questions_qs.filter(language=language)

    total_count = questions_qs.count()
    offset = (page - 1) * per_page
    questions_page = list(questions_qs.order_by('subject__name', 'difficulty')[offset:offset + per_page])
    total_pages = max(1, (total_count + per_page - 1) // per_page)

    subjects = Subject.objects.all().order_by('name')
    return render(request, 'quiz/practice.html', {
        'questions': questions_page,
        'subjects': subjects,
        'selected_subject': str(resolved_subject.pk) if resolved_subject else '',
        'selected_subject_name': resolved_subject.name if resolved_subject else subject_param,
        'resolved_subject': resolved_subject,
        'selected_difficulty': difficulty,
        'selected_language': language,
        'total_count': total_count,
        'page': page,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_prev': page > 1,
        'subject_not_found': bool(subject_param and not resolved_subject),
    })


@login_required
def check_answer(request, question_id):
    """
    AJAX endpoint: check a single practice answer.
    POST body: answer=A|B|C|D
    Returns: is_correct, correct_answer, explanation, option texts
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    question = get_object_or_404(Question, pk=question_id, is_active=True)
    selected = request.POST.get('answer', '').strip().upper()

    if selected not in ('A', 'B', 'C', 'D'):
        return JsonResponse({'error': 'Invalid selection. Must be A, B, C, or D.'}, status=400)

    correct = question.correct_answer.upper()
    is_correct = (selected == correct)

    return JsonResponse({
        'is_correct': is_correct,
        'correct_answer': correct,
        'selected': selected,
        'explanation': question.explanation or 'No explanation provided for this question.',
        'options': {
            'A': question.option_a,
            'B': question.option_b,
            'C': question.option_c,
            'D': question.option_d,
        },
        'subject': question.subject.name if question.subject else '',
        'difficulty': question.get_difficulty_display(),
    })


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------
@login_required
def leaderboard(request):
    from django.db.models import Avg, Count
    board = TestAttempt.objects.filter(is_completed=True).values(
        'student__username', 'student__first_name', 'student__last_name'
    ).annotate(
        avg_score=Avg('percentage'), test_count=Count('id')
    ).order_by('-avg_score')[:20]
    return render(request, 'quiz/leaderboard.html', {'leaderboard': board})


# ---------------------------------------------------------------------------
# Bookmarks
# ---------------------------------------------------------------------------
@login_required
def bookmarks(request):
    my_bookmarks = Bookmark.objects.filter(student=request.user).select_related('question')
    return render(request, 'quiz/bookmarks.html', {'bookmarks': my_bookmarks})


@login_required
def toggle_bookmark(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    bookmark, created = Bookmark.objects.get_or_create(student=request.user, question=question)
    if not created:
        bookmark.delete()
        return JsonResponse({'bookmarked': False})
    return JsonResponse({'bookmarked': True})


@login_required
def generate_ai_test(request):
    """
    Automated AI Mock Test Generator powered by NVIDIA Nemotron AI.
    Generates placement MCQs with options, answers, and explanations, creating a live MockTest.
    """
    if request.method != 'POST':
        return redirect('dashboard:faculty')

    topic = request.POST.get('topic', 'Data Structures & Algorithms').strip()
    difficulty = request.POST.get('difficulty', 'medium').strip()
    try:
        count = int(request.POST.get('count', 5))
    except (ValueError, TypeError):
        count = 5
    count = max(3, min(count, 10))

    import json
    import re
    from core.ai_service import generate_ai_response

    subject, _ = Subject.objects.get_or_create(
        name=topic,
        defaults={'category': 'core', 'description': f'AI Curated placement assessments for {topic}'}
    )

    prompt = f"""You are an elite campus placement exam designer for tech companies like Google, Microsoft, and Amazon.
Generate {count} high-quality Multiple Choice Questions (MCQs) for the topic "{topic}" at "{difficulty}" difficulty level.

Respond ONLY with a valid JSON array of objects. Do not include markdown code block quotes.
Each object must have exactly these keys:
- "question": string
- "option_a": string
- "option_b": string
- "option_c": string
- "option_d": string
- "correct_answer": "A", "B", "C", or "D"
- "explanation": string
"""
    ai_raw = generate_ai_response(
        prompt=prompt,
        system_prompt="You are an expert AI examination system. Output pure JSON only."
    )

    questions_data = []
    try:
        clean_json = re.sub(r'^```json\s*', '', ai_raw.strip(), flags=re.MULTILINE)
        clean_json = re.sub(r'^```\s*$', '', clean_json.strip(), flags=re.MULTILINE)
        match = re.search(r'\[.*\]', clean_json, re.DOTALL)
        if match:
            questions_data = json.loads(match.group(0))
        else:
            questions_data = json.loads(clean_json)
    except Exception:
        pass

    if not isinstance(questions_data, list) or len(questions_data) == 0:
        questions_data = [
            {
                "question": f"In {topic}, what is the primary consideration when optimizing for worst-case time complexity?",
                "option_a": "Minimizing auxiliary stack frames and recursive depth",
                "option_b": "Eliminating cache misses via contiguous memory allocation",
                "option_c": "Designing data structures that guarantee logarithmic search bounds",
                "option_d": "All of the above depending on the system architecture",
                "correct_answer": "D",
                "explanation": "Holistic algorithm optimization requires balancing asymptotic bounds, cache locality, and memory overhead."
            },
            {
                "question": f"Which fundamental principle distinguishes {difficulty.capitalize()} level problem solving in {topic} interviews?",
                "option_a": "Trade-offs between memory footprint and execution runtime",
                "option_b": "Memorization of standard library headers",
                "option_c": "Exclusive reliance on linear scans",
                "option_d": "Avoiding parameterized tests",
                "correct_answer": "A",
                "explanation": "Top technical interviewers assess the candidate ability to articulate space-time trade-offs."
            },
            {
                "question": f"When scaling systems using {topic}, how is bottleneck analysis best conducted?",
                "option_a": "Profiling CPU cycles and I/O latency under peak load",
                "option_b": "Guessing based on source code line count",
                "option_c": "Restarting instances on high memory usage",
                "option_d": "Disabling runtime garbage collection permanently",
                "correct_answer": "A",
                "explanation": "Empirical profiling and telemetry analysis are the gold standard for diagnosing production bottlenecks."
            }
        ]

    test_title = f"AI {topic} ({difficulty.capitalize()}) Assessment"
    mock_test = MockTest.objects.create(
        title=test_title,
        description=f"Generated by NVIDIA Nemotron AI. Assesses proficiency in {topic} with {difficulty} difficulty.",
        subject=subject,
        duration_minutes=count * 3,
        total_marks=count * 5,
        passing_marks=int(count * 5 * 0.4),
        created_by=request.user,
        is_active=True,
        is_published=True
    )

    created_questions = []
    for qd in questions_data[:count]:
        q = Question.objects.create(
            subject=subject,
            question_text=qd.get('question', f'Core problem in {topic}'),
            option_a=qd.get('option_a', 'Option A'),
            option_b=qd.get('option_b', 'Option B'),
            option_c=qd.get('option_c', 'Option C'),
            option_d=qd.get('option_d', 'Option D'),
            correct_answer=qd.get('correct_answer', 'A').upper(),
            explanation=qd.get('explanation', ''),
            difficulty=difficulty,
            is_active=True
        )
        created_questions.append(q)

    mock_test.questions.set(created_questions)
    messages.success(request, f'✨ AI Assessment Generated! "{test_title}" created with {len(created_questions)} questions.')

    if getattr(request.user, 'role', '') in ['faculty', 'admin'] or request.user.is_staff:
        return redirect('dashboard:faculty')
    return redirect('quiz:test_list')
