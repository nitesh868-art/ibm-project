"""Interview Practice Views"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from core.ai_service import generate_interview_questions, evaluate_interview_answer


@login_required
def interview_home(request):
    return render(request, 'interview/home.html')


@login_required
def practice(request):
    """Interview practice with questions."""
    HR_QUESTIONS = [
        {'question': 'Tell me about yourself.', 'tips': 'Cover your academic background, skills, and career goal in 2 minutes.'},
        {'question': 'What are your strengths and weaknesses?', 'tips': 'Be honest. For weakness, show how you\'re improving it.'},
        {'question': 'Where do you see yourself in 5 years?', 'tips': 'Align your answer with the company\'s growth.'},
        {'question': 'Why should we hire you?', 'tips': 'Highlight unique skills and how you add value.'},
        {'question': 'What motivates you?', 'tips': 'Connect to your passion for problem-solving or technology.'},
        {'question': 'Describe a challenging situation and how you handled it.', 'tips': 'Use the STAR method: Situation, Task, Action, Result.'},
        {'question': 'What do you know about our company?', 'tips': 'Research the company before the interview.'},
        {'question': 'How do you handle pressure and deadlines?', 'tips': 'Give a real example with a positive outcome.'},
    ]
    return render(request, 'interview/practice.html', {'hr_questions': HR_QUESTIONS})


@login_required
def ai_practice(request):
    """AI-generated interview questions utilizing unified student context."""
    if request.method == 'POST':
        role = request.POST.get('role', 'Software Engineer')
        company_type = request.POST.get('company_type', 'product')
        difficulty = request.POST.get('difficulty', 'medium')

        from core.services.student_context import get_student_context
        s_ctx = get_student_context(request.user)
        student_profile_dict = {
            'branch': s_ctx['branch'],
            'year': s_ctx['year'],
            'skills': s_ctx['skills'],
            'weak_areas': ', '.join(s_ctx.get('weak_topics', [])) or 'DSA, DBMS',
        }

        result = generate_interview_questions(role, company_type, difficulty, student_profile=student_profile_dict)
        return JsonResponse(result)
    return render(request, 'interview/ai_practice.html')


@login_required
def evaluate_answer(request):
    """Evaluate student interview answer using AI with student context."""
    if request.method == 'POST':
        question = request.POST.get('question', '').strip()
        answer = request.POST.get('answer', '').strip()
        role = request.POST.get('role', 'Software Engineer')

        if not question or not answer:
            return JsonResponse({'success': False, 'error': 'Please provide both question and answer.'})

        from core.services.student_context import get_student_context
        s_ctx = get_student_context(request.user)

        result = evaluate_interview_answer(question, answer, role=role, student_context=s_ctx)
        eval_data = result.get('evaluation', {})
        eval_data['success'] = result.get('success', True)
        return JsonResponse(eval_data)


    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def interview_tips(request):
    tips = [
        {'category': 'Before Interview', 'icon': 'bi-calendar-check', 'tips': [
            'Research the company thoroughly',
            'Review your resume and be ready to explain every point',
            'Practice coding on a whiteboard',
            'Prepare 5+ questions to ask the interviewer',
            'Get a good night\'s sleep',
        ]},
        {'category': 'During Interview', 'icon': 'bi-person-check', 'tips': [
            'Arrive 10-15 minutes early',
            'Maintain eye contact and positive body language',
            'Think aloud while solving problems',
            'Ask clarifying questions before jumping to solutions',
            'Be honest about what you don\'t know',
        ]},
        {'category': 'Technical Round', 'icon': 'bi-code-slash', 'tips': [
            'Start with brute force, then optimize',
            'Discuss time and space complexity',
            'Test your code with edge cases',
            'Know your data structures and algorithms',
            'Practice on LeetCode and HackerRank',
        ]},
        {'category': 'After Interview', 'icon': 'bi-send', 'tips': [
            'Send a thank-you email within 24 hours',
            'Reflect on what went well and what to improve',
            'Don\'t be discouraged by rejections — learn from them',
        ]},
    ]
    return render(request, 'interview/tips.html', {'tips': tips})


@login_required
def hr_questions(request):
    categories = [
        {
            'id': 'intro',
            'name': '👤 Introduction',
            'questions': [
                {
                    'question': 'Tell me about yourself.',
                    'tips': 'Keep it to 2 minutes. Cover: who you are, your academic background, a key achievement, and your career goal.',
                    'model_answer': 'I am a final-year B.Tech CSE student. I have a strong foundation in Data Structures, Algorithms, and web development using Python and Django. During my internship, I built a REST API that reduced data fetch time by 30%. I am now seeking an opportunity to apply my skills in a challenging environment at your company.',
                    'mistakes': 'Avoid reciting your resume line by line. Don\'t be too brief or too long. Don\'t say "I am a hard worker" without proof.',
                    'star': False,
                },
                {
                    'question': 'Walk me through your resume.',
                    'tips': 'Mention only relevant highlights. Connect each point to the role you are applying for.',
                    'model_answer': 'I\'ll focus on what\'s most relevant. My academics gave me strong fundamentals in CS. My main project taught me to work with real data at scale. My internship gave me practical team experience. Each of these prepared me for this role.',
                    'mistakes': 'Don\'t just read your resume. Don\'t include irrelevant details like high school marks unless asked.',
                    'star': False,
                }
            ]
        },
        {
            'id': 'strength',
            'name': '💪 Strengths & Weaknesses',
            'questions': [
                {
                    'question': 'What are your strengths?',
                    'tips': 'Pick 2-3 strengths relevant to the role. Back each with a real example.',
                    'model_answer': 'My biggest strength is problem-solving. In my DSA coursework, I consistently break complex problems into manageable parts. My second strength is communication — I mentored juniors in our coding club. Finally, I pick up new tech quickly — I learnt Django in 2 weeks and built a production-ready app.',
                    'mistakes': 'Don\'t say "I\'m a perfectionist" as a fake strength. Don\'t list generic traits without concrete examples.',
                    'star': False,
                },
                {
                    'question': 'What is your biggest weakness?',
                    'tips': 'Choose a real weakness. Show how you are actively improving it. Never choose a weakness critical to the role.',
                    'model_answer': 'I tend to over-prepare before starting a task, which sometimes slows me down initially. I recognized this during a hackathon where I spent too much time planning. Now I use time-boxing: I set a 15-minute planning limit before I start coding. It has improved both my speed and output.',
                    'mistakes': 'Saying "I work too hard" or "I\'m a perfectionist". Choosing a weakness like "I am bad at coding" for a developer role.',
                    'star': False,
                }
            ]
        },
        {
            'id': 'behavior',
            'name': '🤝 Behavioral (STAR)',
            'questions': [
                {
                    'question': 'Describe a time you faced a conflict in a team.',
                    'tips': 'Use STAR (Situation, Task, Action, Result). Focus on how you resolved it professionally.',
                    'model_answer': 'Situation: During a group project, two teammates disagreed on the database architecture — SQL vs NoSQL.\nTask: As the team lead, I had to resolve this without demotivating either.\nAction: I listed the pros/cons of each objectively, benchmarked both with sample data, and we chose PostgreSQL based on requirements.\nResult: The project was delivered on time, and both teammates appreciated the transparent decision process.',
                    'mistakes': 'Don\'t blame team members. Don\'t say "I just ignored them".',
                    'star': True,
                },
                {
                    'question': 'Tell me about a time you failed and what you learned.',
                    'tips': 'Use STAR. Pick a real failure. Focus on the recovery and lessons learned.',
                    'model_answer': 'Situation: I took on 3 projects simultaneously and missed a key deadline for an internship assignment.\nTask: I had to resubmit and explain the delay.\nAction: I apologized, submitted quality work, and immediately adopted a Kanban board to track tasks.\nResult: I haven\'t missed a deadline since, and the internship team appreciated my transparency.',
                    'mistakes': 'Don\'t choose a failure with no lesson learned. Don\'t blame others.',
                    'star': True,
                },
                {
                    'question': 'How do you handle pressure and tight deadlines?',
                    'tips': 'Give a specific example. Show your prioritization process.',
                    'model_answer': 'Situation: During finals week, I also had a client project deadline.\nTask: I had to manage 60 hours of total work in 5 days.\nAction: I prioritized ruthlessly — studied high-yield topics, broke the project into daily deliverables, and used the Pomodoro technique.\nResult: I scored 82% in exams and delivered the project on schedule.',
                    'mistakes': 'Saying "I just push through it" without explaining how.',
                    'star': True,
                }
            ]
        },
        {
            'id': 'career',
            'name': '🎯 Career Goals',
            'questions': [
                {
                    'question': 'Where do you see yourself in 5 years?',
                    'tips': 'Show ambition aligned with the company\'s growth.',
                    'model_answer': 'In 5 years, I see myself as a senior software engineer with deep expertise in distributed systems and cloud architecture. I want to have contributed meaningfully to core products and be mentoring junior developers.',
                    'mistakes': 'Don\'t say "running my own startup" or "in your seat".',
                    'star': False,
                },
                {
                    'question': 'Why should we hire you?',
                    'tips': 'Connect your unique skills to the role\'s requirements.',
                    'model_answer': 'You should hire me because I bring strong CS fundamentals, hands-on experience building web applications, and a proven ability to learn quickly. I delivered production code in the first week of my internship.',
                    'mistakes': 'Giving generic answers like "I am a hard worker".',
                    'star': False,
                }
            ]
        },
        {
            'id': 'company',
            'name': '🏢 Company Fit',
            'questions': [
                {
                    'question': 'Why do you want to work at this company?',
                    'tips': 'Research the company beforehand. Reference specific products or culture.',
                    'model_answer': 'I have followed your company\'s tech blog and product launches. Your work in scalable backend services directly aligns with my interest in system architecture.',
                    'mistakes': 'Saying "because it pays well" or "for the brand name".',
                    'star': False,
                },
                {
                    'question': 'Are you willing to relocate?',
                    'tips': 'Be honest. If willing, express enthusiasm for new environments.',
                    'model_answer': 'Yes, I am open to relocation. I am flexible and eager to move to wherever the team and opportunity are located.',
                    'mistakes': 'Being hesitant or vague.',
                    'star': False,
                }
            ]
        }
    ]
    return render(request, 'interview/hr_questions.html', {'categories': categories})


@login_required
def technical_questions(request):
    return render(request, 'interview/technical.html')
