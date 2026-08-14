"""
Study Planner Views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import StudySubject, Topic, StudyPlan, DailyStudyLog, Goal, PomodoroSession, Semester
from core.ai_service import generate_study_plan as ai_generate_plan
import json


@login_required
def planner_home(request):
    """Study planner home with overview."""
    subjects = StudySubject.objects.filter(student=request.user, is_active=True)
    recent_plans = StudyPlan.objects.filter(student=request.user).order_by('-created_at')[:3]
    recent_logs = DailyStudyLog.objects.filter(student=request.user).order_by('-date')[:7]
    active_goals = Goal.objects.filter(student=request.user, is_completed=False)

    return render(request, 'studyplanner/home.html', {
        'subjects': subjects,
        'recent_plans': recent_plans,
        'recent_logs': recent_logs,
        'active_goals': active_goals,
    })


@login_required
def subject_list(request):
    """List all study subjects with progress, units, and topic details."""
    from django.db.models import Count
    subjects = StudySubject.objects.filter(student=request.user, is_active=True).annotate(
        topic_count=Count('topics')
    ).prefetch_related('topics')

    return render(request, 'studyplanner/subjects.html', {'subjects': subjects})



@login_required
def add_subject(request):
    """Add a new study subject."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        credits = int(request.POST.get('credits', 3))
        priority = int(request.POST.get('priority', 2))
        exam_date = request.POST.get('exam_date') or None
        difficulty = int(request.POST.get('difficulty_level', 3))
        color = request.POST.get('color', '#6366f1')

        if name:
            StudySubject.objects.create(
                student=request.user,
                name=name, code=code, credits=credits, priority=priority,
                exam_date=exam_date, difficulty_level=difficulty, color=color
            )
            messages.success(request, f'✅ Subject "{name}" added successfully!')
            return redirect('studyplanner:subjects')
        else:
            messages.error(request, 'Subject name is required.')

    return render(request, 'studyplanner/add_subject.html', {
        'priority_choices': StudySubject.PRIORITY_CHOICES,
        'colors': ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6'],
    })


@login_required
def edit_subject(request, pk):
    """Edit an existing subject."""
    subject = get_object_or_404(StudySubject, pk=pk, student=request.user)

    if request.method == 'POST':
        subject.name = request.POST.get('name', subject.name)
        subject.code = request.POST.get('code', subject.code)
        subject.credits = int(request.POST.get('credits', subject.credits))
        subject.priority = int(request.POST.get('priority', subject.priority))
        subject.exam_date = request.POST.get('exam_date') or None
        subject.difficulty_level = int(request.POST.get('difficulty_level', subject.difficulty_level))
        subject.color = request.POST.get('color', subject.color)
        subject.save()
        messages.success(request, f'✅ Subject "{subject.name}" updated!')
        return redirect('studyplanner:subjects')

    return render(request, 'studyplanner/edit_subject.html', {'subject': subject})


@login_required
def delete_subject(request, pk):
    """Delete a study subject."""
    subject = get_object_or_404(StudySubject, pk=pk, student=request.user)
    name = subject.name
    subject.delete()
    messages.success(request, f'🗑️ Subject "{name}" deleted.')
    return redirect('studyplanner:subjects')


@login_required
def topic_list(request, pk):
    """List topics for a subject."""
    subject = get_object_or_404(StudySubject, pk=pk, student=request.user)
    topics = Topic.objects.filter(subject=subject)

    return render(request, 'studyplanner/topics.html', {
        'subject': subject,
        'topics': topics,
        'status_choices': Topic.STATUS_CHOICES,
    })


@login_required
def add_topic(request, subject_id):
    """Add a topic to a subject."""
    subject = get_object_or_404(StudySubject, pk=subject_id, student=request.user)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '')
        estimated_hours = float(request.POST.get('estimated_hours', 1.0))
        deadline = request.POST.get('deadline') or None

        if name:
            Topic.objects.create(
                subject=subject, name=name, description=description,
                estimated_hours=estimated_hours, deadline=deadline
            )
            messages.success(request, f'✅ Topic "{name}" added!')
            return redirect('studyplanner:topics', pk=subject_id)

    return render(request, 'studyplanner/add_topic.html', {'subject': subject})


@login_required
def update_topic_status(request, pk):
    """AJAX endpoint to update topic status."""
    topic = get_object_or_404(Topic, pk=pk, subject__student=request.user)

    if request.method == 'POST':
        new_status = request.POST.get('status', 'not_started')
        valid_statuses = [s[0] for s in Topic.STATUS_CHOICES]
        if new_status in valid_statuses:
            topic.status = new_status
            if new_status == 'completed':
                topic.completed_at = timezone.now()
            topic.save()
            topic.subject.calculate_completion()
            return JsonResponse({
                'status': 'ok',
                'completion': topic.subject.completion_percentage,
                'topic_status': topic.status
            })

    return JsonResponse({'status': 'error'}, status=400)


@login_required
def study_plans(request):
    """List all study plans."""
    plans = StudyPlan.objects.filter(student=request.user)
    return render(request, 'studyplanner/plans.html', {'plans': plans})


@login_required
def generate_ai_plan(request):
    """Generate & persistently save an AI study plan using OpenRouter (NVIDIA Nemotron)."""
    student_profile = getattr(request.user, 'student_profile', None)
    active_goals_count = Goal.objects.filter(student=request.user, is_completed=False).count()

    if request.method == 'POST':
        selected_ids = request.POST.getlist('subject_ids')
        if selected_ids:
            subjects = StudySubject.objects.filter(student=request.user, pk__in=selected_ids, is_active=True)
        else:
            subjects = StudySubject.objects.filter(student=request.user, is_active=True)

        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        daily_hours = float(request.POST.get('daily_hours', 4))
        weak_subjects = request.POST.get('weak_subjects', '').strip()

        from datetime import date, datetime
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            days_available = max(1, (end_date - start_date).days)
        except Exception:
            days_available = 30
            start_date = date.today()
            end_date = date.today()

        subjects_data = [
            {
                'name': s.name,
                'topics_count': s.topics.count(),
                'priority': s.get_priority_display(),
                'completion': s.completion_percentage,
            }
            for s in subjects
        ]

        if not subjects_data:
            messages.warning(request, "⚠️ No active subjects found. Please add your subjects first to generate a personalized study plan.")
            return redirect('studyplanner:add_subject')

        # Pull rich student context
        from core.services.student_context import get_student_context
        s_ctx = get_student_context(request.user)

        extra_context = ""
        if s_ctx.get('weak_topics'):
            extra_context += f"- Priority Weak Topics (Mastery < 50%): {', '.join(s_ctx['weak_topics'])}\n"
        if weak_subjects:
            extra_context += f"- User Highlighted Weak Subjects: {weak_subjects}\n"
        extra_context += f"- Student Info: Year {s_ctx['year']}, Semester {s_ctx['semester']}, Branch: {s_ctx['branch']}, CGPA: {s_ctx['cgpa']}\n"
        extra_context += f"- Quiz Performance: Avg Score {s_ctx['avg_quiz_score']}%\n"

        result = ai_generate_plan(subjects_data, days_available, daily_hours, exam_date=end_date, extra_context=extra_context)


        if result.get('success'):
            plan_content = json.dumps(result['plan'], indent=2)
            plan = StudyPlan.objects.create(
                student=request.user,
                title=result['plan'].get('title', 'Personalised AI Study Plan'),
                plan_content=plan_content,
                start_date=start_date,
                end_date=end_date,
                is_ai_generated=True,
                daily_study_hours=daily_hours,
            )
            plan.subjects.set(subjects)
            messages.success(request, '🤖 AI Study Plan generated & saved to database!')
            return redirect('studyplanner:plans')
        else:
            messages.warning(request, '⚠️ AI study plan is temporarily unavailable. A basic plan has been saved.')

    subjects = StudySubject.objects.filter(student=request.user, is_active=True)
    return render(request, 'studyplanner/generate_plan.html', {
        'subjects': subjects,
        'student_profile': student_profile,
        'active_goals_count': active_goals_count,
    })


@login_required
def pomodoro(request):
    """Pomodoro timer page."""
    topics = Topic.objects.filter(
        subject__student=request.user,
        status__in=['not_started', 'in_progress']
    )
    return render(request, 'studyplanner/pomodoro.html', {'topics': topics})


@login_required
def goals(request):
    """Goals list."""
    active_goals = Goal.objects.filter(student=request.user, is_completed=False)
    completed_goals = Goal.objects.filter(student=request.user, is_completed=True)
    return render(request, 'studyplanner/goals.html', {
        'active_goals': active_goals,
        'completed_goals': completed_goals,
    })


@login_required
def add_goal(request):
    """Add a new goal."""
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        goal_type = request.POST.get('goal_type', 'daily')
        target_date = request.POST.get('target_date') or None
        description = request.POST.get('description', '')

        if title:
            Goal.objects.create(
                student=request.user, title=title, goal_type=goal_type,
                target_date=target_date, description=description
            )
            messages.success(request, f'✅ Goal "{title}" added!')
            return redirect('studyplanner:goals')

    return render(request, 'studyplanner/add_goal.html', {'goal_types': Goal.GOAL_TYPE_CHOICES})


@login_required
def complete_goal(request, pk):
    """Mark a goal as complete."""
    goal = get_object_or_404(Goal, pk=pk, student=request.user)
    goal.is_completed = True
    goal.completed_at = timezone.now()
    goal.save()
    messages.success(request, f'🎉 Goal "{goal.title}" completed!')
    return redirect('studyplanner:goals')


@login_required
def study_log(request):
    """Study log history."""
    logs = DailyStudyLog.objects.filter(student=request.user).order_by('-date')
    return render(request, 'studyplanner/log.html', {'logs': logs})


@login_required
def add_study_log(request):
    """Log study session."""
    if request.method == 'POST':
        duration = int(request.POST.get('duration_minutes', 0))
        subject_id = request.POST.get('subject_id')
        notes = request.POST.get('notes', '')

        subject = None
        if subject_id:
            try:
                subject = StudySubject.objects.get(pk=subject_id, student=request.user)
            except StudySubject.DoesNotExist:
                pass

        DailyStudyLog.objects.create(
            student=request.user,
            date=timezone.now().date(),
            subject=subject,
            duration_minutes=duration,
            notes=notes
        )
        return JsonResponse({'status': 'ok'})

    return JsonResponse({'status': 'error'}, status=400)


@login_required
def calendar_view(request):
    """Calendar view of study schedule."""
    subjects = StudySubject.objects.filter(student=request.user, is_active=True)
    topics = Topic.objects.filter(
        subject__student=request.user,
        deadline__isnull=False
    ).values('name', 'deadline', 'status', 'subject__name', 'subject__color')

    # Serialize for calendar JS
    events = [
        {
            'title': f"{t['subject__name']}: {t['name']}",
            'start': t['deadline'].isoformat(),
            'color': t['subject__color'],
            'status': t['status'],
        }
        for t in topics
    ]

    return render(request, 'studyplanner/calendar.html', {
        'subjects': subjects,
        'events_json': json.dumps(events),
    })


@login_required
def study_materials(request):
    """My Notes & Study Materials list view."""
    from core.models import StudyMaterial
    materials = StudyMaterial.objects.filter(uploaded_by=request.user) | StudyMaterial.objects.filter(is_demo=True)
    materials = materials.order_by('-created_at')

    return render(request, 'studyplanner/materials.html', {'materials': materials})


@login_required
def upload_notes(request):
    """Upload new study notes with validation & text extraction."""
    from core.models import StudyMaterial, CurriculumUnit, CurriculumTopic, log_activity
    from core.utils import validate_file_upload, extract_document_pipeline

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        material_type = request.POST.get('material_type', 'notes')
        uploaded_file = request.FILES.get('file')

        if not title:
            messages.error(request, 'Title is required.')
            return redirect('studyplanner:materials')

        pipeline_res = {'text': '', 'page_count': 1, 'is_scanned': False, 'quality': 'success', 'status_message': ''}
        if uploaded_file:
            is_valid, err_msg = validate_file_upload(uploaded_file)
            if not is_valid:
                messages.error(request, f'❌ Upload failed: {err_msg}')
                return redirect('studyplanner:materials')

            pipeline_res = extract_document_pipeline(uploaded_file)
            if pipeline_res.get('is_scanned'):
                messages.warning(request, pipeline_res.get('status_message'))

        material = StudyMaterial.objects.create(
            title=title,
            description=description,
            material_type=material_type,
            file=uploaded_file,
            extracted_text=pipeline_res['text'] or description,
            page_count=pipeline_res['page_count'],
            is_scanned=pipeline_res['is_scanned'],
            extraction_quality=pipeline_res['quality'],
            uploaded_by=request.user,
            is_demo=False
        )

        log_activity(request.user, f"Uploaded Study Notes: {title}", module="StudyPlanner", request=request)
        messages.success(request, f'✅ Notes "{title}" uploaded successfully! (Pages: {material.page_count})')

        if request.POST.get('explain_now') == '1':
            return redirect('studyplanner:explain_notes', pk=material.id)

        return redirect('studyplanner:materials')

    return render(request, 'studyplanner/upload_notes.html')


@login_required
def explain_notes(request, pk):
    """AI analysis & explanation of uploaded study notes with Document Q&A."""
    from core.models import StudyMaterial, log_activity
    from core.ai_service import explain_uploaded_notes, ai_chat as ai_chat_fn

    material = get_object_or_404(StudyMaterial, pk=pk)

    # Permission check: must be owner or demo content
    if not material.is_demo and material.uploaded_by != request.user:
        messages.error(request, "Access denied to this material.")
        return redirect('studyplanner:materials')

    doc_question = request.POST.get('doc_question', '').strip() or request.GET.get('doc_q', '').strip()
    doc_answer = None

    notes_text = material.extracted_text or material.description or material.title

    if doc_question:
        qa_result = ai_chat_fn(
            message=doc_question,
            mode='notes',
            notes_content=notes_text,
            student_profile={'year': getattr(getattr(request.user, 'student_profile', None), 'year', 3)}
        )
        if qa_result.get('success'):
            doc_answer = qa_result.get('response')

    question = request.GET.get('q', 'Explain this in simple terms and generate exam questions')
    result = explain_uploaded_notes(notes_text, question=question)
    analysis = result.get('analysis')

    user_error = None
    if not analysis:
        from core.ai_service import get_user_friendly_ai_error
        user_error = get_user_friendly_ai_error(result.get('error'))

    log_activity(request.user, f"AI Explained Notes: {material.title}", module="AI-Tutor", request=request)

    return render(request, 'studyplanner/explain_notes.html', {
        'material': material,
        'analysis': analysis,
        'question': question,
        'doc_question': doc_question,
        'doc_answer': doc_answer,
        'user_error': user_error,
    })


