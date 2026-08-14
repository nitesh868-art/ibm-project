"""
Placement Preparation Views
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from quiz.models import Question, MockTest, Subject, TestAttempt, Bookmark
from companies.models import Company


@login_required
def placement_home(request):
    """Placement preparation home page."""
    subjects = Subject.objects.all()
    companies = Company.objects.filter(is_active=True)[:12]
    total_questions = Question.objects.filter(is_active=True).count()

    return render(request, 'placement/home.html', {
        'subjects': subjects,
        'companies': companies,
        'total_questions': total_questions,
    })


@login_required
def aptitude(request):
    """Aptitude practice questions."""
    subjects = Subject.objects.filter(category='aptitude')
    questions = Question.objects.filter(
        subject__category='aptitude', is_active=True
    ).order_by('difficulty')[:50]
    return render(request, 'placement/practice.html', {
        'questions': questions, 'category': 'Aptitude', 'category_slug': 'aptitude'
    })


@login_required
def reasoning(request):
    """Logical reasoning questions."""
    questions = Question.objects.filter(
        subject__category='reasoning', is_active=True
    ).order_by('difficulty')[:50]
    return render(request, 'placement/practice.html', {
        'questions': questions, 'category': 'Logical Reasoning', 'category_slug': 'reasoning'
    })


@login_required
def verbal(request):
    """Verbal ability questions."""
    questions = Question.objects.filter(
        subject__category='verbal', is_active=True
    ).order_by('difficulty')[:50]
    return render(request, 'placement/practice.html', {
        'questions': questions, 'category': 'Verbal Ability', 'category_slug': 'verbal'
    })


@login_required
def programming(request):
    """Programming practice — all languages."""
    LANGUAGES = ['python', 'java', 'c', 'cpp', 'javascript', 'sql']
    questions_by_lang = {}
    for lang in LANGUAGES:
        questions_by_lang[lang] = Question.objects.filter(
            language=lang, is_active=True
        ).count()
    return render(request, 'placement/programming.html', {'languages': questions_by_lang})


@login_required
def programming_by_language(request, language):
    """Programming questions filtered by language."""
    questions = Question.objects.filter(language=language, is_active=True).order_by('difficulty')
    difficulty = request.GET.get('difficulty', '')
    if difficulty:
        questions = questions.filter(difficulty=difficulty)
    return render(request, 'placement/practice.html', {
        'questions': questions,
        'category': language.upper(),
        'category_slug': language,
    })


@login_required
def company_questions(request, pk):
    """Company-specific interview questions."""
    company = get_object_or_404(Company, pk=pk)
    questions = Question.objects.filter(company=company, is_active=True)
    return render(request, 'placement/company_questions.html', {
        'company': company, 'questions': questions
    })


@login_required
def mock_tests(request):
    """Available mock tests."""
    tests = MockTest.objects.filter(is_active=True, is_published=True)
    my_attempts = {
        a.test_id: a for a in TestAttempt.objects.filter(student=request.user)
    }
    return render(request, 'placement/mock_tests.html', {
        'tests': tests, 'my_attempts': my_attempts
    })


@login_required
def leaderboard(request):
    """Global leaderboard."""
    from django.db.models import Avg, Count
    leaderboard_data = TestAttempt.objects.filter(
        is_completed=True
    ).values(
        'student__username', 'student__first_name', 'student__last_name'
    ).annotate(
        avg_score=Avg('percentage'),
        test_count=Count('id')
    ).order_by('-avg_score')[:20]

    return render(request, 'placement/leaderboard.html', {
        'leaderboard': leaderboard_data,
        'current_user': request.user.username,
    })


@login_required
def progress(request):
    """Student's placement preparation progress."""
    attempts = TestAttempt.objects.filter(student=request.user, is_completed=True)
    bookmarks = Bookmark.objects.filter(student=request.user).select_related('question')

    subject_progress = {}
    for attempt in attempts:
        if attempt.test.subject:
            subj = attempt.test.subject.name
            if subj not in subject_progress:
                subject_progress[subj] = []
            subject_progress[subj].append(float(attempt.percentage))

    avg_by_subject = {
        subj: round(sum(scores) / len(scores), 1)
        for subj, scores in subject_progress.items()
    }

    return render(request, 'placement/progress.html', {
        'attempts': attempts,
        'bookmarks': bookmarks,
        'avg_by_subject': avg_by_subject,
    })
