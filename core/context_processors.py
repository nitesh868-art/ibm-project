"""
Core Context Processors — Inject global data into all templates
"""
from notifications.models import Notification


def global_context(request):
    """
    Global context available in every template.
    Provides: unread notification count, user profile shortcut
    """
    context = {
        'app_name': 'AI Placement Portal',
        'app_version': '1.0.0',
    }

    if request.user.is_authenticated:
        try:
            unread_count = Notification.objects.filter(
                user=request.user, is_read=False
            ).count()
            context['unread_notifications'] = unread_count
        except Exception:
            context['unread_notifications'] = 0

        # Quick access to profile
        context['student_profile'] = getattr(request.user, 'student_profile', None)
        context['faculty_profile'] = getattr(request.user, 'faculty_profile', None)

    return context
