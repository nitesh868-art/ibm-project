"""
Chatbot Views — AI-powered chat assistant
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from core.ai_service import ai_chat as ai_chat_fn, get_daily_recommendations


@login_required
def chatbot_home(request):
    """AI Chatbot home page."""
    history = request.session.get('chat_history', [])
    return render(request, 'chatbot/home.html', {'history': history})


# Alias: chatbot:chat -> chatbot_home
chat = chatbot_home


@login_required
def ask_ai(request):
    """Process AI chat message with student profile context & mode adaptation."""
    if request.method == 'POST':
        mode = 'tutor'
        notes_content = ''
        message = ''

        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                message = data.get('message', '').strip()
                mode = data.get('mode', 'tutor')
                notes_content = data.get('notes_content', '')
            except json.JSONDecodeError:
                message = ''
        else:
            message = request.POST.get('message', '').strip()
            mode = request.POST.get('mode', 'tutor')
            notes_content = request.POST.get('notes_content', '')

        if not message and not notes_content:
            return JsonResponse({'success': False, 'response': 'Please enter a question or upload notes.'})

        # Build unified page & topic aware student profile context
        from core.services.student_context import get_student_context
        subject_name = data.get('subject', '') if request.content_type == 'application/json' else request.POST.get('subject', '')
        topic_name = data.get('topic', '') if request.content_type == 'application/json' else request.POST.get('topic', '')

        s_ctx = get_student_context(request.user, current_subject=subject_name, current_topic=topic_name)
        student_profile = {
            'year': s_ctx['year'],
            'semester': s_ctx['semester'],
            'branch': s_ctx['branch'],
            'skills': s_ctx['skills'],
            'weak_areas': ', '.join(s_ctx.get('weak_topics', [])) or 'DSA, DBMS',
            'active_topic': topic_name or s_ctx['active_context'].get('topic_name', ''),
            'active_subject': subject_name or s_ctx['active_context'].get('subject_name', ''),
        }

        # Get conversation history
        history = request.session.get('chat_history', [])

        # Get AI response with page/topic-aware profile adaptation
        result = ai_chat_fn(
            message=message or "Explain these uploaded notes",
            conversation_history=history,
            student_profile=student_profile,
            mode=mode,
            notes_content=notes_content,
        )


        # Save to session history
        history.append({'role': 'user', 'content': message or '[Uploaded Notes Analysis]'})
        history.append({'role': 'assistant', 'content': result.get('response', '')})
        request.session['chat_history'] = history[-20:]
        request.session.modified = True

        # Log activity
        from core.models import log_activity
        log_activity(request.user, f"AI Tutor Chat ({mode})", module='Chatbot', request=request)

        if not result.get('success'):
            from core.ai_service import get_user_friendly_ai_error
            user_msg = get_user_friendly_ai_error(result.get('error'))
            return JsonResponse({'success': False, 'response': user_msg})

        return JsonResponse(result)

    return JsonResponse({'error': 'Method not allowed'}, status=405)



@login_required
def daily_recommendations(request):
    """Return daily AI recommendations as JSON for dashboard widget."""
    user = request.user
    try:
        student_data = {
            'branch': user.student_profile.branch,
            'weak_areas': 'DSA, DBMS',
            'streak': user.student_profile.study_streak,
            'target_company': 'Product companies',
            'days_to_placement': 180,
        }
    except Exception:
        student_data = {'branch': 'CSE', 'weak_areas': 'DSA', 'streak': 0}

    result = get_daily_recommendations(student_data)
    return JsonResponse(result)


@login_required
def chat_history(request):
    """Get chat history from session."""
    history = request.session.get('chat_history', [])
    return JsonResponse({'history': history})


@login_required
def clear_history(request):
    """Clear chat history."""
    request.session['chat_history'] = []
    request.session.modified = True
    return JsonResponse({'status': 'ok'})

