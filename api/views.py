"""
API Views — Django REST Framework
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from quiz.models import Question, Subject
from notifications.models import Notification
from core.ai_service import ai_chat, generate_study_plan
from django.utils import timezone
from datetime import timedelta


class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """API ViewSet for questions."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Question.objects.filter(is_active=True)
        subject_id = self.request.query_params.get('subject')
        difficulty = self.request.query_params.get('difficulty')
        language = self.request.query_params.get('language')
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        if language:
            qs = qs.filter(language=language)
        return qs

    def list(self, request, *args, **kwargs):
        questions = self.get_queryset()[:20]
        data = [{
            'id': q.id,
            'question': q.question_text,
            'options': q.get_options(),
            'difficulty': q.difficulty,
            'subject': q.subject.name,
        } for q in questions]
        return Response(data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        try:
            q = Question.objects.get(pk=pk, is_active=True)
            return Response({
                'id': q.id,
                'question': q.question_text,
                'options': q.get_options(),
                'correct_answer': q.correct_answer,
                'explanation': q.explanation,
                'difficulty': q.difficulty,
            })
        except Question.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)


class NotificationViewSet(viewsets.ModelViewSet):
    """API ViewSet for notifications."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        notifs = self.get_queryset()[:10]
        data = [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.notification_type,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat(),
        } for n in notifs]
        return Response({'count': self.get_queryset().count(), 'results': data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """API endpoint returning dashboard statistics."""
    from studyplanner.models import DailyStudyLog, StudySubject
    from quiz.models import TestAttempt

    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    # Study hours this week
    week_logs = DailyStudyLog.objects.filter(student=request.user, date__gte=week_ago)
    total_study_mins = sum(l.duration_minutes for l in week_logs)

    # Test scores
    attempts = TestAttempt.objects.filter(student=request.user, is_completed=True)
    avg_score = 0
    if attempts.exists():
        from django.db.models import Avg
        avg = attempts.aggregate(avg=Avg('percentage'))['avg']
        avg_score = round(float(avg), 1) if avg else 0

    # Subjects
    subjects = StudySubject.objects.filter(student=request.user, is_active=True)
    avg_completion = 0
    if subjects.exists():
        avg_completion = sum(s.completion_percentage for s in subjects) // subjects.count()

    return Response({
        'study_hours_this_week': round(total_study_mins / 60, 1),
        'tests_taken': attempts.count(),
        'average_score': avg_score,
        'subjects_count': subjects.count(),
        'avg_completion': avg_completion,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def study_data(request):
    """Study analytics data for charts."""
    from studyplanner.models import DailyStudyLog
    today = timezone.now().date()
    data = []
    for i in range(7):
        day = today - timedelta(days=6-i)
        logs = DailyStudyLog.objects.filter(student=request.user, date=day)
        total = sum(l.duration_minutes for l in logs)
        data.append({'date': day.isoformat(), 'day': day.strftime('%a'), 'hours': round(total/60, 1)})
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_chat(request):
    """API endpoint for AI chatbot."""
    message = request.data.get('message', '').strip()
    if not message:
        return Response({'error': 'Message is required'}, status=400)

    from core.ai_service import ai_chat as chat_fn
    result = chat_fn(message)
    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_study_plan(request):
    """API endpoint to generate AI study plan."""
    from studyplanner.models import StudySubject
    subjects = StudySubject.objects.filter(student=request.user, is_active=True)
    subjects_data = [{'name': s.name, 'topics_count': s.topics.count(), 'priority': s.get_priority_display()} for s in subjects]
    days = int(request.data.get('days', 30))
    hours = float(request.data.get('daily_hours', 4))
    result = generate_study_plan(subjects_data, days, hours)
    return Response(result)
