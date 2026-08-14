"""
Student Context Service — Centralized Unified Learning State & Mastery Engine
=============================================================================
Provides:
  - Unified student learning state (subjects, topics, mastery scores, weak areas)
  - Real-time page & topic awareness for AI Tutor
  - Curated reliable resource discovery
  - Topic mastery recalculation
"""

from django.utils import timezone
from studyplanner.models import StudySubject, Topic, TopicMastery, DailyStudyLog, Goal, StudyPlan
from quiz.models import TestAttempt, QuestionAnswer
from core.models import StudyMaterial, ActivityLog


def get_curated_resources(subject_name: str, topic_name: str = '') -> list:
    """
    Return reliable, real educational resource links based on subject & topic.
    Never invents broken URLs.
    """
    sub_lower = (subject_name or '').lower()
    top_lower = (topic_name or '').lower()
    q_str = f"{subject_name} {topic_name}".strip()

    resources = []

    # 1. Official Documentation / Trusted Docs
    if 'python' in sub_lower:
        resources.append({
            'title': 'Official Python Documentation',
            'source': 'docs.python.org',
            'type': 'Documentation',
            'url': 'https://docs.python.org/3/',
            'icon': 'bi-journal-code'
        })
        resources.append({
            'title': f'W3Schools Python — {topic_name or "Tutorial"}',
            'source': 'W3Schools',
            'type': 'Tutorial',
            'url': 'https://www.w3schools.com/python/',
            'icon': 'bi-book'
        })
    elif 'java' in sub_lower:
        resources.append({
            'title': 'Oracle Java Documentation',
            'source': 'docs.oracle.com',
            'type': 'Documentation',
            'url': 'https://docs.oracle.com/en/java/',
            'icon': 'bi-journal-code'
        })
        resources.append({
            'title': f'GeeksforGeeks Java — {topic_name or "Overview"}',
            'source': 'GeeksforGeeks',
            'type': 'Article',
            'url': f'https://www.geeksforgeeks.org/search/?q={q_str.replace(" ", "+")}',
            'icon': 'bi-file-text'
        })
    elif 'dbms' in sub_lower or 'database' in sub_lower or 'sql' in sub_lower:
        resources.append({
            'title': 'W3Schools SQL & Database Tutorial',
            'source': 'W3Schools',
            'type': 'Tutorial',
            'url': 'https://www.w3schools.com/sql/',
            'icon': 'bi-database'
        })
        resources.append({
            'title': f'GeeksforGeeks DBMS — {topic_name or "DBMS Topics"}',
            'source': 'GeeksforGeeks',
            'type': 'Article',
            'url': f'https://www.geeksforgeeks.org/dbms/',
            'icon': 'bi-book'
        })
    elif 'operating' in sub_lower or 'os' in sub_lower:
        resources.append({
            'title': 'GeeksforGeeks Operating Systems Notes',
            'source': 'GeeksforGeeks',
            'type': 'Study Material',
            'url': 'https://www.geeksforgeeks.org/operating-systems/',
            'icon': 'bi-cpu'
        })
    elif 'network' in sub_lower or 'cn' in sub_lower:
        resources.append({
            'title': 'GeeksforGeeks Computer Networks Notes',
            'source': 'GeeksforGeeks',
            'type': 'Study Material',
            'url': 'https://www.geeksforgeeks.org/computer-network-tutorials/',
            'icon': 'bi-globe'
        })
    else:
        resources.append({
            'title': f'GeeksforGeeks — {q_str}',
            'source': 'GeeksforGeeks',
            'type': 'Tutorial',
            'url': f'https://www.geeksforgeeks.org/search/?q={q_str.replace(" ", "+")}',
            'icon': 'bi-book'
        })

    # 2. YouTube Video Search link (always valid)
    resources.append({
        'title': f'YouTube Video Tutorials — {q_str}',
        'source': 'YouTube',
        'type': 'Video',
        'url': f'https://www.youtube.com/results?search_query={q_str.replace(" ", "+")}+tutorial',
        'icon': 'bi-youtube'
    })

    return resources


def recalculate_student_mastery(user):
    """
    Refresh all TopicMastery records for all topics of active subjects for this user.
    """
    subjects = StudySubject.objects.filter(student=user, is_active=True)
    mastery_records = []
    for s in subjects:
        for t in s.topics.all():
            tm, _ = TopicMastery.objects.get_or_create(student=user, topic=t, subject=s)
            tm.update_mastery()
            mastery_records.append(tm)
    return mastery_records


def get_student_context(user, current_subject=None, current_topic=None, page_context=None) -> dict:
    """
    Build rich unified student learning context dictionary for AI Tutor, Study Planner & Dashboard.
    """
    profile = getattr(user, 'student_profile', None)

    # Re-calculate mastery records
    masteries = recalculate_student_mastery(user)
    weak_masteries = [m for m in masteries if m.is_weak]

    subjects = StudySubject.objects.filter(student=user, is_active=True)
    subjects_summary = []
    for s in subjects:
        top_list = []
        for t in s.topics.all():
            tm = next((m for m in masteries if m.topic_id == t.pk), None)
            top_list.append({
                'id': t.pk,
                'name': t.name,
                'status': t.get_status_display(),
                'mastery': tm.mastery_score if tm else 0,
                'is_weak': tm.is_weak if tm else False,
            })
        subjects_summary.append({
            'name': s.name,
            'completion': s.completion_percentage,
            'priority': s.get_priority_display(),
            'exam_date': s.exam_date.strftime('%Y-%m-%d') if s.exam_date else 'Not set',
            'topics': top_list,
        })

    # Quiz performance
    attempts = TestAttempt.objects.filter(student=user, is_completed=True)
    avg_quiz_score = 0
    if attempts.exists():
        avg_quiz_score = round(sum(float(a.percentage) for a in attempts) / attempts.count(), 1)

    # Active goals
    goals = Goal.objects.filter(student=user, is_completed=False).values_list('title', flat=True)

    # Recent materials
    materials = StudyMaterial.objects.filter(uploaded_by=user).values_list('title', flat=True)[:5]

    # Current page / topic context
    active_context = {}
    if current_topic:
        active_context['topic_name'] = current_topic.name if hasattr(current_topic, 'name') else str(current_topic)
        active_context['topic_status'] = current_topic.get_status_display() if hasattr(current_topic, 'get_status_display') else ''
        if hasattr(current_topic, 'subject'):
            active_context['subject_name'] = current_topic.subject.name
    elif current_subject:
        active_context['subject_name'] = current_subject.name if hasattr(current_subject, 'name') else str(current_subject)

    if page_context:
        active_context['page'] = page_context

    weak_topic_names = [f"{m.topic.name} ({m.subject.name}: {m.mastery_score}%)" for m in weak_masteries]

    # Recommended next topic: first weak topic, or first not_started topic
    recommended_topic = None
    if weak_masteries:
        recommended_topic = weak_masteries[0].topic
    else:
        for s in subjects:
            ns = s.topics.filter(status='not_started').first()
            if ns:
                recommended_topic = ns
                break

    return {
        'student_name': user.get_full_name() or user.username,
        'year': getattr(profile, 'year', 3) if profile else 3,
        'semester': getattr(profile, 'semester', 5) if profile else 5,
        'branch': profile.get_branch_display() if (profile and hasattr(profile, 'get_branch_display')) else (getattr(profile, 'branch', 'CSE') if profile else 'CSE'),
        'cgpa': float(getattr(profile, 'cgpa', 8.0) or 8.0) if profile else 8.0,
        'skills': getattr(profile, 'skills', 'Python, SQL') if profile else 'Python, SQL',
        'subjects_summary': subjects_summary,
        'total_subjects': subjects.count(),
        'weak_topics': weak_topic_names,
        'weak_topics_count': len(weak_topic_names),
        'avg_quiz_score': avg_quiz_score,
        'tests_taken': attempts.count(),
        'active_goals': list(goals),
        'uploaded_materials': list(materials),
        'active_context': active_context,
        'recommended_topic': recommended_topic,
        'curated_resources': get_curated_resources(active_context.get('subject_name', 'CS'), active_context.get('topic_name', 'General'))
    }
