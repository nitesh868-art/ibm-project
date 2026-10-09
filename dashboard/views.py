"""
Dashboard Views — Student, Faculty, Admin dashboards
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta


@login_required
def dashboard_home(request):
    """Main dashboard — routes to correct dashboard by role."""
    user = request.user
    if user.is_faculty:
        return redirect('dashboard:faculty')
    if user.is_admin_user:
        return redirect('dashboard:admin')
    return student_dashboard(request)


def student_dashboard(request):
    """Student dashboard with study stats, placement readiness, tasks."""
    user = request.user

    # Import here to avoid circular imports
    from studyplanner.models import StudySubject, Goal, DailyStudyLog, PomodoroSession
    from quiz.models import TestAttempt, MockTest
    from resume_builder.models import Resume
    from notifications.models import Notification

    today = timezone.now().date()

    # Gather all stats
    try:
        student_profile = user.student_profile
    except Exception:
        student_profile = None

    # Study subjects and progress
    subjects = StudySubject.objects.filter(student=user, is_active=True)
    total_subjects = subjects.count()
    avg_completion = 0
    if total_subjects > 0:
        avg_completion = sum(s.completion_percentage for s in subjects) // total_subjects

    # Today's goals
    today_goals = Goal.objects.filter(student=user, goal_type='daily',
                                       is_completed=False)

    # Recent test attempts
    recent_tests = TestAttempt.objects.filter(
        student=user, is_completed=True
    ).order_by('-started_at')[:5]

    # Average test score
    test_scores = list(TestAttempt.objects.filter(
        student=user, is_completed=True
    ).values_list('percentage', flat=True)[:10])
    avg_score = round(sum(float(s) for s in test_scores) / len(test_scores), 1) if test_scores else 0

    # Study log for last 7 days
    week_ago = today - timedelta(days=7)
    study_logs = DailyStudyLog.objects.filter(
        student=user, date__gte=week_ago
    ).order_by('date')

    # Weekly study data for chart
    weekly_data = []
    for i in range(7):
        day = today - timedelta(days=6-i)
        day_log = study_logs.filter(date=day)
        total_mins = sum(l.duration_minutes for l in day_log)
        weekly_data.append({
            'day': day.strftime('%a'),
            'hours': round(total_mins / 60, 1),
        })

    # Resume completion
    resume = Resume.objects.filter(student=user, is_primary=True).first()
    resume_ats = resume.ats_score if resume else 0

    # Notifications
    notifications = Notification.objects.filter(user=user, is_read=False)[:5]

    # Placement readiness score (composite metric)
    placement_readiness = _calculate_placement_readiness(
        avg_score, avg_completion, resume_ats, student_profile
    )

    # Upcoming mock tests
    upcoming_tests = MockTest.objects.filter(
        is_active=True, is_published=True,
        start_time__gte=timezone.now()
    ).order_by('start_time')[:3]

    # Unified Student Context & Mastery
    try:
        from core.services.student_context import get_student_context
        s_ctx = get_student_context(user)
    except Exception:
        s_ctx = {}

    context = {
        'student_profile': student_profile,
        'student_context': s_ctx,
        'total_subjects': total_subjects,
        'avg_completion': avg_completion,
        'today_goals': today_goals,
        'recent_tests': recent_tests,
        'avg_score': avg_score,
        'weekly_data': weekly_data,
        'resume': resume,
        'resume_ats': resume_ats,
        'notifications': notifications,
        'placement_readiness': placement_readiness,
        'upcoming_tests': upcoming_tests,
        'subjects': subjects[:6],
        'today': today,
    }

    return render(request, 'dashboard/student_dashboard.html', context)


@login_required
def faculty_dashboard(request):
    """Faculty dashboard."""
    if not request.user.is_faculty:
        return redirect('dashboard:home')

    from quiz.models import MockTest, TestAttempt
    from accounts.models import User

    total_students = User.objects.filter(role='student').count()
    my_tests = MockTest.objects.filter(created_by=request.user)
    recent_attempts = TestAttempt.objects.filter(
        test__created_by=request.user, is_completed=True
    ).order_by('-started_at')[:10]

    context = {
        'total_students': total_students,
        'my_tests': my_tests,
        'recent_attempts': recent_attempts,
    }
    return render(request, 'dashboard/faculty_dashboard.html', context)


@login_required
def admin_dashboard(request):
    """Admin dashboard with system-wide analytics."""
    if not request.user.is_admin_user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("403 Forbidden: You are not authorized to view the Administrator Dashboard.")

    from accounts.models import User, StudentProfile
    from quiz.models import MockTest, TestAttempt, Question
    from companies.models import Company
    from core.models import ActivityLog

    total_users = User.objects.count()
    total_students = User.objects.filter(role='student').count()
    from studyplanner.models import StudySubject
    total_subjects = StudySubject.objects.count()
    total_companies = Company.objects.count()
    placed_students = StudentProfile.objects.filter(placement_status='placed').count()

    students_ratio = round((total_students / total_users * 100)) if total_users > 0 else 0
    placed_ratio = round((placed_students / total_students * 100)) if total_students > 0 else 0

    context = {
        'total_users': total_users,
        'total_students': total_students,
        'total_subjects': total_subjects,
        'total_questions': Question.objects.count(),
        'total_tests': MockTest.objects.count(),
        'total_companies': total_companies,
        'placed_students': placed_students,
        'students_ratio': min(100, max(0, students_ratio)),
        'placed_ratio': min(100, max(0, placed_ratio)),
        'recent_users': User.objects.order_by('-date_joined')[:5],
        'recent_activities': ActivityLog.objects.select_related('user')[:10],
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
def activity_log(request):
    """Activity Audit Log view for Administrators."""
    if not request.user.is_admin_user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("403 Forbidden: Administrator access required.")

    from core.models import ActivityLog
    from django.core.paginator import Paginator

    logs_list = ActivityLog.objects.select_related('user').all()

    # Search & Filter
    module = request.GET.get('module', '').strip()
    role = request.GET.get('role', '').strip()
    search = request.GET.get('q', '').strip()

    if module:
        logs_list = logs_list.filter(module=module)
    if role:
        logs_list = logs_list.filter(role=role)
    if search:
        logs_list = logs_list.filter(action__icontains=search)

    paginator = Paginator(logs_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'selected_module': module,
        'selected_role': role,
        'search_query': search,
    }
    return render(request, 'dashboard/activity_log.html', context)


@login_required
def ai_health_check(request):
    """AI Health Check — manually triggered, tests real OpenRouter connection."""
    if not request.user.is_admin_user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("403 Forbidden: Admin access required.")

    from core.ai_service import _generate, is_ai_available, _get_model

    test_prompt = "Explain binary search in 3 sentences for a computer science student."
    api_connected = False
    response_text = None
    error_msg = None

    if not is_ai_available():
        error_msg = "OPENROUTER_API_KEY is not set in .env — AI is not configured."
    else:
        try:
            response_text = _generate(test_prompt)
            if response_text:
                api_connected = True
            else:
                error_msg = "OpenRouter returned an empty response. Check your API key and model configuration."
        except Exception as exc:
            error_msg = f"Unexpected error during AI health check: {type(exc).__name__}"

    data = {
        'provider': 'OpenRouter',
        'model': _get_model(),
        'status': 'Connected' if api_connected else 'Failed',
        'api_connected': api_connected,
        'test_prompt': test_prompt,
        'response': response_text,
        'error': error_msg,
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse(data)

    return render(request, 'dashboard/ai_health.html', {'health': data})


@login_required
def profile_completion(request):
    """Profile completion tips."""
    return render(request, 'dashboard/profile_completion.html')


@login_required
def certificates_list(request):
    """List student's portal achievement certificates."""
    from dashboard.models import PortalCertificate
    certs = PortalCertificate.objects.filter(student=request.user)
    return render(request, 'dashboard/certificates.html', {'certificates': certs})


@login_required
def view_certificate(request, cert_id):
    """Display individual portal achievement certificate for preview/print."""
    from dashboard.models import PortalCertificate
    from django.shortcuts import get_object_or_404
    cert = get_object_or_404(PortalCertificate, certificate_id=cert_id, student=request.user)
    return render(request, 'dashboard/view_certificate.html', {'certificate': cert})




def _calculate_placement_readiness(avg_score, study_completion, ats_score, profile):
    """Calculate an overall placement readiness score (0-100)."""
    score = 0
    # Test performance (30%)
    score += min(avg_score * 0.30, 30)
    # Study completion (20%)
    score += min(study_completion * 0.20, 20)
    # Resume ATS score (25%)
    score += min(ats_score * 0.25, 25)
    # Profile completeness (25%)
    if profile:
        score += min(profile.profile_completion * 0.25, 25)
    return round(score)
