"""
AI Service — OpenRouter (NVIDIA Nemotron) Integration
======================================================
All AI features are centralised here.
The public API (function signatures) is unchanged from before,
so all callers (chatbot, studyplanner, placement, dashboard) continue
to work without modification.

Architecture:
    Browser → Django view → ai_service._generate(prompt)
           → OpenRouter API → NVIDIA Nemotron
           → response → Django view → Browser

API keys are read ONLY from environment variables.
They are NEVER sent to the browser or written to logs.
"""

import os
import json
import logging
import requests
from django.conf import settings

logger = logging.getLogger('django')

# ---------------------------------------------------------------------------
# Provider configuration
# ---------------------------------------------------------------------------
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_TIMEOUT = 12          # seconds per request
MAX_TOKENS_NORMAL = 500          # reasonably short responses to save free quota & speed up fallbacks
MAX_TOKENS_JSON = 800            # reasonably concise JSON responses to ensure fast completion
TEMPERATURE = 0.4


def _get_api_key() -> str:
    """Return the OpenRouter API key from environment. Never log it."""
    key = getattr(settings, 'OPENROUTER_API_KEY', '') or os.getenv('OPENROUTER_API_KEY', '')
    return key.strip()


def _get_model() -> str:
    """Return the configured model name."""
    return (
        getattr(settings, 'OPENROUTER_MODEL', '')
        or os.getenv('OPENROUTER_MODEL', '')
        or 'nvidia/nemotron-3-super-120b-a12b:free'
    )


def is_ai_available() -> bool:
    """Return True if an API key is configured."""
    return bool(_get_api_key())


def get_user_friendly_ai_error(error_str: str = '') -> str:
    """Categorise raw technical errors into safe, clean user-facing messages."""
    if not error_str:
        return "AI service is temporarily unavailable. Please try again."

    err = str(error_str).lower()

    if '401' in err or 'unauthorized' in err or 'unauthenticated' in err:
        return "AI configuration needs attention. Please contact the administrator."
    if '403' in err or 'forbidden' in err:
        return "AI service access is restricted. Please contact the administrator."
    if '429' in err or 'rate' in err or 'quota' in err or 'resource_exhausted' in err:
        return "AI usage limit reached. Please try again in a few moments."
    if '500' in err or '502' in err or '503' in err or 'unavailable' in err:
        return "AI service is temporarily unavailable. Please try again."
    if 'timeout' in err or 'timed out' in err:
        return "AI request timed out. Please try again."
    if 'connection' in err or 'network' in err:
        return "Could not reach AI service. Check your internet connection."

    return "AI service is temporarily unavailable. Please try again."


# ---------------------------------------------------------------------------
# Core transport — Multi-model fallback chain for OpenRouter
# ---------------------------------------------------------------------------
FALLBACK_MODELS = [
    'nvidia/nemotron-3-super-120b-a12b:free',
    'meta-llama/llama-3.3-70b-instruct:free',
    'deepseek/deepseek-r1:free',
    'qwen/qwen-2.5-coder-32b-instruct:free',
    'openrouter/auto',
]


def _generate(prompt: str, max_tokens: int = MAX_TOKENS_NORMAL,
              system_prompt: str = "You are PlacementPro AI, a helpful academic and career tutor for Indian B.Tech students.",
              temperature: float = TEMPERATURE) -> str | None:
    """
    Send a chat completion request to OpenRouter with automatic multi-model fallback.
    Primary model: nvidia/nemotron-3-super-120b-a12b:free
    Falls back to other free OpenRouter models if primary fails with 429, 5xx, timeout, or empty response.
    Returns the response text string, or None on failure.
    The API key is NEVER logged or exposed.
    """
    api_key = _get_api_key()
    if not api_key:
        logger.warning("[OpenRouter] API key not configured. Set OPENROUTER_API_KEY in .env")
        return None

    primary_model = _get_model()
    # Build models to try, ensuring primary model is first
    models_to_try = [primary_model]
    for m in FALLBACK_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://placementpro.local",
        "X-Title": "PlacementPro AI",
    }

    last_error = None

    for model in models_to_try:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            resp = requests.post(
                OPENROUTER_BASE_URL,
                headers=headers,
                json=payload,
                timeout=OPENROUTER_TIMEOUT,
            )
        except requests.Timeout as exc:
            last_error = f"timeout ({model})"
            logger.warning("[OpenRouter] Model %s timed out, trying fallback...", model)
            continue
        except requests.ConnectionError as exc:
            last_error = f"connection error ({model})"
            logger.warning("[OpenRouter] Model %s connection error, trying fallback...", model)
            continue

        status = resp.status_code

        # Auth failures — do not retry other models as key is bad
        if status in (401, 403):
            logger.error("[OpenRouter] HTTP %d — API key invalid or unauthorized", status)
            return None

        # Rate limit, server errors, or not found — switch to fallback model
        if status in (404, 429, 500, 502, 503):
            last_error = f"HTTP {status} ({model})"
            logger.warning("[OpenRouter] Model %s returned HTTP %d, trying fallback...", model, status)
            continue

        if status != 200:
            last_error = f"HTTP {status} ({model})"
            logger.warning("[OpenRouter] Model %s returned unexpected HTTP %d, trying fallback...", model, status)
            continue

        # Parse response
        try:
            data = resp.json()
        except (ValueError, TypeError) as exc:
            last_error = f"invalid JSON ({model})"
            logger.warning("[OpenRouter] Model %s returned invalid JSON, trying fallback...", model)
            continue

        try:
            text = data['choices'][0]['message']['content'].strip()
            if text:
                logger.info("[OpenRouter] Successfully generated response using model: %s", model)
                return text
            logger.warning("[OpenRouter] Model %s returned empty text, trying fallback...", model)
            last_error = f"empty text ({model})"
        except (KeyError, IndexError, TypeError) as exc:
            logger.warning("[OpenRouter] Model %s returned malformed response structure, trying fallback...", model)
            last_error = f"malformed response ({model})"

    logger.error("[OpenRouter] All fallback models failed. Last error: %s", last_error)
    return None


def _json_extract(text: str | None) -> dict | None:
    """Extract JSON from a response that may contain markdown fences or surrounding text."""
    if not text:
        return None
    t = text.strip()
    if '```json' in t:
        t = t.split('```json')[1].split('```')[0].strip()
    elif '```' in t:
        t = t.split('```')[1].split('```')[0].strip()

    try:
        return json.loads(t)
    except (json.JSONDecodeError, TypeError):
        pass

    # Try finding the first '{' and last '}'
    start = t.find('{')
    end = t.rfind('}')
    if start != -1 and end != -1 and end > start:
        snippet = t[start:end+1]
        try:
            return json.loads(snippet)
        except (json.JSONDecodeError, TypeError):
            pass

    return None


# ===========================================================================
# 1. STUDY PLAN GENERATOR
# ===========================================================================
def generate_study_plan(subjects, days_available, daily_hours, exam_date=None, extra_context=""):
    """
    Generate a personalised AI study plan.
    Args:
        subjects       : list of dicts {name, topics_count, priority}
        days_available : int
        daily_hours    : float
    Returns:
        dict {success, plan}
    """
    subjects_text = "\n".join([
        f"- {s.get('name', 'Subject')}: {s.get('topics_count', 0)} topics, priority: {s.get('priority', 'medium')}"
        for s in subjects
    ])

    prompt = f"""Create a realistic study plan for a B.Tech student.

SUBJECTS:
{subjects_text}

CONSTRAINTS:
- Days available: {days_available}
- Daily study hours: {daily_hours}
- Exam date: {exam_date or "Not specified"}
{extra_context}

Output ONLY valid JSON (no extra text):
{{
  "title": "Personalised Study Plan",
  "overview": "2-3 sentence overview",
  "daily_plan": [
    {{"time_slot": "09:00 - 11:00 AM", "activity": "High-priority Subject Focus", "topic": "Core concepts"}},
    {{"time_slot": "02:00 - 04:00 PM", "activity": "Practice & Problem Solving", "topic": "Exercises"}}
  ],
  "weekly_schedule": [
    {{
      "week": 1,
      "theme": "Foundation & Core Concepts",
      "focus_subjects": ["Subject 1"],
      "days": [
        {{"day": "Monday", "subjects": ["DSA - Arrays (2hrs)", "DBMS - ER Model (1hr)"], "total_hours": 3}}
      ]
    }}
  ],
  "priority_topics": ["Critical Topic 1", "High Priority Topic 2"],
  "breaks_and_rest": ["Take a 10-minute break after every 50-minute Pomodoro session.", "Ensure 7-8 hours sleep for memory consolidation."],
  "revision_plan": "Final 3 days allocated for mock test revision & active recall.",
  "estimated_completion": "90%"
}}"""

    text = _generate(prompt, max_tokens=MAX_TOKENS_JSON)
    data = _json_extract(text)
    if data:
        return {"success": True, "plan": data}
    if text:
        return {"success": True, "plan": {"raw_text": text, "title": "Your Study Plan"}}
    return {"success": False, "plan": _fallback_study_plan(subjects, days_available, daily_hours)}


# ===========================================================================
# 2. SKILL GAP ANALYZER
# ===========================================================================
def analyze_skill_gap(student_data):
    """Analyse student skills vs industry requirements."""
    prompt = f"""Analyse the skill gap for this B.Tech student targeting placement in India.

Student:
- Branch: {student_data.get('branch', 'CSE')}
- Year: {student_data.get('year', 3)}
- CGPA: {student_data.get('cgpa', 0)}
- Skills: {student_data.get('skills', 'Not specified')}
- Target Role: {student_data.get('target_role', 'Software Engineer')}

Output ONLY valid JSON:
{{
  "overall_readiness": 65,
  "skill_categories": [
    {{"name": "DSA & Problem Solving", "current_level": 60, "required_level": 85, "gap": 25, "status": "needs_work", "resources": ["LeetCode medium problems"]}},
    {{"name": "DBMS", "current_level": 70, "required_level": 75, "gap": 5, "status": "near_target", "resources": ["Practice SQL on HackerRank"]}},
    {{"name": "OS", "current_level": 55, "required_level": 70, "gap": 15, "status": "needs_work", "resources": ["Galvin OS book"]}},
    {{"name": "Aptitude", "current_level": 65, "required_level": 80, "gap": 15, "status": "needs_work", "resources": ["IndiaBix"]}}
  ],
  "strong_areas": ["Programming basics"],
  "critical_gaps": ["DSA advanced topics"],
  "learning_path": [
    {{"priority": 1, "skill": "DSA", "timeline": "4 weeks", "action": "Solve 3 LeetCode problems daily"}}
  ],
  "placement_companies": ["TCS", "Infosys", "Wipro"],
  "estimated_weeks_to_ready": 12
}}"""

    text = _generate(prompt, max_tokens=MAX_TOKENS_JSON)
    data = _json_extract(text)
    if data:
        return {"success": True, "analysis": data}
    return {"success": False, "analysis": _fallback_skill_gap()}


# ===========================================================================
# 3. CAREER ADVISOR
# ===========================================================================
def get_career_guidance(student_data):
    """AI career guidance based on student profile."""
    prompt = f"""Give career guidance to this B.Tech student in India.

Profile:
- Branch: {student_data.get('branch', 'CSE')}
- CGPA: {student_data.get('cgpa', 0)}
- Skills: {student_data.get('skills', 'Not specified')}
- Year: {student_data.get('year', 3)}

Output ONLY valid JSON:
{{
  "career_paths": [
    {{
      "title": "Software Development Engineer",
      "match_percentage": 85,
      "description": "Build scalable software systems",
      "required_skills": ["DSA", "System Design", "OOP", "SQL"],
      "salary_range": "8-30 LPA",
      "companies": ["Google", "Microsoft", "Amazon"],
      "preparation_tips": ["Solve 200+ LeetCode", "Learn system design basics"]
    }}
  ],
  "immediate_actions": ["Solve 2 DSA problems daily"],
  "skill_gaps": ["System Design"],
  "recommended_certifications": ["AWS Cloud Practitioner"],
  "placement_readiness_score": 70,
  "overall_advice": "Personalised paragraph of advice"
}}"""

    text = _generate(prompt, max_tokens=MAX_TOKENS_JSON)
    data = _json_extract(text)
    if data:
        return {"success": True, "guidance": data}
    return {"success": False, "guidance": None, "error": "AI not available"}


# ===========================================================================
# 4. RESUME REVIEWER
# ===========================================================================
def review_resume(resume_data, job_description=""):
    """AI-powered ATS resume analysis with optional job description matching."""
    jd_prompt = f"\nTARGET JOB DESCRIPTION:\n{job_description[:1500]}\n" if job_description else ""

    prompt = f"""You are an ATS recruiter reviewing a student resume for Indian tech companies.

Resume:
Name: {resume_data.get('full_name', 'Student')}
Summary: {resume_data.get('summary', '')}
Skills: {", ".join(resume_data.get('skills', []))}
Education: {resume_data.get('education', '')}
Projects: {resume_data.get('projects', '')}
Certifications: {resume_data.get('certifications', '')}
{jd_prompt}
Output ONLY valid JSON:
{{
  "ats_score": 78,
  "grade": "B+",
  "job_match_score": 82,
  "strengths": ["Good project descriptions", "Relevant tech stack"],
  "weaknesses": ["Missing quantified metrics"],
  "suggestions": [
    {{"section": "Projects", "suggestion": "Add metrics e.g. Improved query performance by 35%"}}
  ],
  "keywords_missing": ["REST API", "Agile", "Docker"],
  "overall_feedback": "Solid baseline. Optimize key section bullet points.",
  "improvement_priority": "medium"
}}"""

    text = _generate(prompt, max_tokens=MAX_TOKENS_JSON)
    data = _json_extract(text)
    if data:
        return {"success": True, "review": data}
    return {"success": False, "review": _fallback_resume_review()}


# ===========================================================================
# 5. AI CHATBOT — Academic & Career Tutor
# ===========================================================================
def ai_chat(message: str, conversation_history=None, student_profile=None,
            mode: str = "tutor", notes_content: str = "") -> dict:
    """
    Intelligent AI tutor that adapts by year, branch and mode.

    Args:
        message              : student's question
        conversation_history : list of {role, content} dicts (last 6 used)
        student_profile      : dict {year, branch, skills, weak_areas, semester}
        mode                 : 'tutor' | 'teach_me' | 'exam_prep' | 'notes' | 'placement' | 'interview'
        notes_content        : extracted text from uploaded notes (for 'notes' mode)

    Returns:
        dict {success: bool, response: str}
    """
    prof = student_profile or {}
    year = prof.get('year', 3)
    branch = prof.get('branch', 'CSE')
    skills = prof.get('skills', 'General Programming')
    weak_areas = prof.get('weak_areas', '')
    semester = prof.get('semester', '')

    # ── Year-adaptive instruction ─────────────────────────────────────────
    if year == 1:
        level_instruction = (
            "STUDENT LEVEL: 1st Year (Beginner). Use real-world analogies, "
            "step-by-step simple explanations. Avoid heavy jargon. "
            "Focus on fundamentals: programming basics, maths, communication."
        )
    elif year == 2:
        level_instruction = (
            "STUDENT LEVEL: 2nd Year. Balance fundamentals with practical code. "
            "Focus: DSA basics, OOP, DBMS intro, OS concepts."
        )
    elif year == 3:
        level_instruction = (
            "STUDENT LEVEL: 3rd Year (Placement-track). Focus on algorithm complexity, "
            "system design basics, placement interview expectations, industry standards."
        )
    else:
        level_instruction = (
            "STUDENT LEVEL: 4th Year (Placement-critical). Focus heavily on "
            "placement prep, HR & technical interviews, DSA mastery, resume, "
            "real company questions and final project guidance."
        )

    # ── Mode instruction ──────────────────────────────────────────────────
    mode_instruction = ""
    if mode == "teach_me":
        mode_instruction = (
            "MODE: Teach Me. Explain one sub-concept, give a simple example, "
            "then ask a follow-up question to test understanding."
        )
    elif mode == "notes" and notes_content:
        excerpt = notes_content[:2500]
        mode_instruction = (
            f"MODE: Notes Assistant. Use ONLY the notes below to answer. "
            f"If the answer is not in the notes, say clearly: "
            f"'I couldn't find this in your uploaded notes, but I can explain it using general knowledge.'\n"
            f"--- NOTES ---\n{excerpt}\n--- END NOTES ---"
        )
    elif mode == "exam_prep":
        mode_instruction = (
            "MODE: Exam Prep. Structure answers:\n"
            "• 2-mark: concise 2-line definition\n"
            "• 7-mark: Definition → Working → Diagram/example → Key points → Conclusion\n"
            "• MCQ: 4 options with correct answer marked\n"
            "• Important questions: list the most likely exam questions on the topic"
        )
    elif mode == "placement":
        mode_instruction = (
            "MODE: Placement Prep. Focus on company-level DSA, aptitude, "
            "system design, HR questions, and STAR format answers."
        )
    elif mode == "interview":
        mode_instruction = (
            "MODE: Interview Practice. Give detailed model answers, mention "
            "edge cases, time/space complexity for coding questions."
        )

    # ── Conversation history (last 6 turns) ───────────────────────────────
    history_text = ""
    if conversation_history:
        for item in (conversation_history[-6:]):
            role = item.get("role", "user")
            content = item.get("content", "")[:400]  # truncate long entries
            history_text += f"{role.upper()}: {content}\n"

    system_prompt = (
        "You are PlacementPro AI — an intelligent Academic & Career Tutor "
        "for Indian B.Tech students. Be helpful, concise and accurate. "
        "Do not hallucinate. Do not invent content from uploaded notes."
    )

    prompt = f"""STUDENT PROFILE:
- Year: Year {year} B.Tech | Semester: {semester} | Branch: {branch}
- Skills: {skills}
- Weak Areas: {weak_areas}

{level_instruction}
{mode_instruction}

CONVERSATION HISTORY:
{history_text}
STUDENT: {message}
ANSWER:"""

    text = _generate(prompt, max_tokens=MAX_TOKENS_NORMAL, system_prompt=system_prompt)
    if text:
        return {"success": True, "response": text}

    return {
        "success": False,
        "response": "AI service is temporarily unavailable. Please try again in a moment.",
    }


# ===========================================================================
# 6. NOTES EXPLAINER
# ===========================================================================
def explain_uploaded_notes(notes_text: str, question: str = "Explain this in simple terms") -> dict:
    """Analyse uploaded notes and return JSON with summary, questions, MCQs."""
    prompt = f"""You are an AI Academic Tutor analysing uploaded study notes.

NOTES CONTENT:
---
{notes_text[:3500]}
---

STUDENT REQUEST: {question}

Return ONLY valid JSON:
{{
  "summary": "2-3 sentence overview of the notes",
  "simple_explanation": "Simplified step-by-step breakdown",
  "key_definitions": ["Term 1: Definition", "Term 2: Definition"],
  "two_mark_questions": [
    {{"question": "Define ...", "answer": "Concise 2-line answer"}},
    {{"question": "What is ...", "answer": "Concise 2-line answer"}}
  ],
  "seven_mark_questions": [
    {{"question": "Explain ... with example", "hints": "1. Definition 2. Working 3. Example"}}
  ],
  "mcqs": [
    {"question": "...", "options": ["A. ..", "B. ..", "C. ..", "D. .."], "correct": "A"}
  ],
  "flashcards": [
    {"front": "Key Term / Question", "back": "Concise explanation / answer"}
  ],
  "important_topics": ["Topic 1", "Topic 2", "Topic 3"]
}}"""

    text = _generate(prompt, max_tokens=MAX_TOKENS_JSON)
    data = _json_extract(text)
    if data:
        return {"success": True, "analysis": data}
    return {"success": False, "analysis": None, "error": "AI not available"}


# ===========================================================================
# 7. INTERVIEW QUESTION GENERATOR
# ===========================================================================
def generate_interview_questions(role, company_type, difficulty="medium", topics=None, student_profile=None, **kwargs):
    """Generate interview questions for practice utilizing student profile."""
    topics_text = ", ".join(topics) if topics else "general CS"
    profile_info = ""
    if student_profile:
        profile_info = f"\nStudent Profile: Year {student_profile.get('year', 3)}, Branch {student_profile.get('branch', 'CSE')}, Weak Areas: {student_profile.get('weak_areas', 'None')}."

    prompt = f"""Generate 6 interview questions for a {role} at a {company_type} company.{profile_info}
Difficulty: {difficulty}. Topics: {topics_text}.

Output ONLY valid JSON:
{{
  "technical": [
    {{"question": "...", "expected_answer": "...", "tips": "...", "difficulty": "medium"}}
  ],
  "hr": [
    {{"question": "...", "expected_answer": "...", "tips": "..."}}
  ],
  "coding": [
    {{"question": "...", "expected_answer": "...", "example": "...", "time_complexity": "O(n)"}}
  ]
}}"""

    text = _generate(prompt, max_tokens=MAX_TOKENS_JSON)
    data = _json_extract(text)
    if data:
        return {"success": True, "questions": data}
    return {"success": False, "questions": _get_sample_interview_questions()}


# ===========================================================================
# 8. INTERVIEW ANSWER EVALUATOR
# ===========================================================================
def evaluate_interview_answer(question, answer, role="Software Engineer", student_context=None, **kwargs):
    """Evaluate a student's interview answer."""
    prompt = f"""You are a senior {role} interviewer at a top tech company.
Evaluate this answer:

QUESTION: {question}
ANSWER: {answer[:1000]}


Output ONLY valid JSON:
{{
  "score": 7,
  "max_score": 10,
  "technical_accuracy": 8,
  "completeness": 7,
  "clarity": 6,
  "overall_feedback": "Good attempt, but missing key concepts...",
  "what_was_good": ["Correct understanding of basic concept"],
  "what_to_improve": ["Missing time complexity analysis"],
  "model_answer_hints": ["Consider mentioning..."],
  "follow_up_question": "Can you explain the time complexity?"
}}"""

    text = _generate(prompt, max_tokens=MAX_TOKENS_JSON)
    data = _json_extract(text)
    if data:
        return {"success": True, "evaluation": data}
    return {"success": False, "evaluation": {"score": 0, "overall_feedback": "Could not evaluate. Please try again."}}


# ===========================================================================
# 9. DAILY RECOMMENDATIONS  (called on explicit request only — NOT on page load)
# ===========================================================================
def get_daily_recommendations(student_data: dict) -> dict:
    """Generate personalised daily study recommendations."""
    prompt = f"""You are an AI study coach for a B.Tech student.
Generate personalised daily recommendations.

Student:
- Branch: {student_data.get('branch', 'CSE')}
- Weak areas: {student_data.get('weak_areas', 'DSA, DBMS')}
- Study streak: {student_data.get('streak', 0)} days
- Target: {student_data.get('target_company', 'Product companies')}

Output ONLY valid JSON:
{{
  "greeting": "Here is your plan for today.",
  "focus_topic": "Dynamic Programming - Knapsack",
  "daily_tasks": [
    {{"task": "Solve 2 DP problems on LeetCode", "time": "45 min", "priority": "high", "resource": "LeetCode"}},
    {{"task": "Revise DBMS transactions", "time": "30 min", "priority": "medium", "resource": "GeeksforGeeks"}},
    {{"task": "Practice 10 aptitude questions", "time": "20 min", "priority": "medium", "resource": "IndiaBix"}}
  ],
  "motivation_quote": "Consistency beats perfection.",
  "tip_of_day": "When solving DP, identify: state, transition, base case.",
  "progress_insight": "Keep your streak going!",
  "placement_update": "Focus on DSA every day."
}}"""

    text = _generate(prompt, max_tokens=MAX_TOKENS_JSON)
    data = _json_extract(text)
    if data:
        return {"success": True, "recommendations": data}
    return {"success": False, "recommendations": _fallback_recommendations()}


# ===========================================================================
# 10. PLACEMENT READINESS ANALYSIS
# ===========================================================================
def analyze_placement_readiness(student_data: dict) -> dict:
    """AI-powered placement readiness breakdown."""
    prompt = f"""Analyse this student's placement readiness for Indian tech companies.

Student:
- Branch: {student_data.get('branch', 'CSE')}
- CGPA: {student_data.get('cgpa', 0)}
- DSA Score: {student_data.get('dsa_score', 50)}/100
- Aptitude Score: {student_data.get('aptitude_score', 50)}/100
- Resume ATS: {student_data.get('resume_ats', 0)}/100
- Projects: {student_data.get('projects_count', 0)}

Output ONLY valid JSON:
{{
  "overall_score": 72,
  "grade": "B+",
  "components": [
    {{"name": "DSA & Problem Solving", "score": 65, "weight": 30, "weighted_score": 19.5, "status": "needs_work"}},
    {{"name": "Resume Quality", "score": 60, "weight": 25, "weighted_score": 15, "status": "needs_work"}},
    {{"name": "Aptitude", "score": 75, "weight": 20, "weighted_score": 15, "status": "good"}},
    {{"name": "Projects", "score": 50, "weight": 15, "weighted_score": 7.5, "status": "needs_work"}},
    {{"name": "Communication", "score": 65, "weight": 10, "weighted_score": 6.5, "status": "good"}}
  ],
  "why_this_score": "Your CGPA is an asset. DSA and resume need more work.",
  "target_companies": ["TCS", "Infosys", "Capgemini"],
  "top_priority": "Focus on DSA — solve 3 LeetCode problems daily"
}}"""

    text = _generate(prompt, max_tokens=MAX_TOKENS_JSON)
    data = _json_extract(text)
    if data:
        return {"success": True, "analysis": data}
    return {"success": False, "analysis": None}


# ===========================================================================
# CENTRAL CONVENIENCE WRAPPER
# ===========================================================================
def generate_ai_response(prompt: str, context: dict = None) -> dict:
    """
    Simple central wrapper used by any view that wants a plain AI response.
    context dict is optional; if provided it is prepended to the prompt.
    """
    full_prompt = prompt
    if context:
        ctx_lines = "\n".join(f"{k}: {v}" for k, v in context.items())
        full_prompt = f"Context:\n{ctx_lines}\n\nQuestion:\n{prompt}"

    text = _generate(full_prompt)
    if text:
        return {"success": True, "response": text}
    return {"success": False, "response": get_user_friendly_ai_error('')}


# ===========================================================================
# FALLBACK DATA (when AI is unavailable — NOT fake AI responses)
# ===========================================================================

def _fallback_study_plan(subjects, days_available, daily_hours):
    return {
        "title": "Standard Study Plan (AI Unavailable)",
        "overview": f"A balanced {days_available}-day plan with {daily_hours} hours/day.",
        "weekly_schedule": [],
        "priority_topics": ["DSA", "DBMS", "OS", "CN", "Aptitude"],
        "tips": [
            "Start with the most difficult subjects when energy is highest",
            "Use the Pomodoro technique: 25 min study, 5 min break",
            "Review notes before sleeping for better retention",
            "Practice previous year questions 2 weeks before exams",
        ],
        "revision_plan": "Spend the last 3 days doing rapid revision.",
        "estimated_completion": "70%",
    }


def _fallback_skill_gap():
    return {
        "overall_readiness": 50,
        "skill_categories": [
            {"name": "DSA", "current_level": 50, "required_level": 80, "gap": 30,
             "status": "needs_work", "resources": ["LeetCode", "GeeksforGeeks"]},
            {"name": "DBMS", "current_level": 60, "required_level": 75, "gap": 15,
             "status": "needs_work", "resources": ["GATE DBMS notes"]},
        ],
        "strong_areas": ["Basic programming"],
        "critical_gaps": ["DSA", "Aptitude"],
        "learning_path": [
            {"priority": 1, "skill": "DSA", "timeline": "6 weeks", "action": "Solve 3 LeetCode problems daily"},
        ],
        "placement_companies": ["TCS", "Infosys", "Wipro"],
        "estimated_weeks_to_ready": 16,
    }


def _fallback_resume_review():
    return {
        "ats_score": 60,
        "grade": "C+",
        "strengths": ["Basic structure present"],
        "weaknesses": ["AI review unavailable — set OPENROUTER_API_KEY in .env to enable"],
        "suggestions": [{"section": "All", "suggestion": "Configure AI to get detailed review"}],
        "keywords_missing": [],
        "overall_feedback": "Configure the AI API key to get detailed AI feedback.",
        "improvement_priority": "high",
    }


def _fallback_recommendations():
    return {
        "greeting": "Here are your study tasks for today.",
        "focus_topic": "Data Structures — Arrays and Strings",
        "daily_tasks": [
            {"task": "Solve 2 LeetCode easy problems", "time": "30 min", "priority": "high", "resource": "LeetCode"},
            {"task": "Read DBMS chapter on normalisation", "time": "45 min", "priority": "medium", "resource": "GATE notes"},
            {"task": "Practice 10 aptitude questions", "time": "20 min", "priority": "medium", "resource": "IndiaBix"},
        ],
        "motivation_quote": "Every expert was once a beginner. Keep going!",
        "tip_of_day": "Review yesterday's topics for 10 minutes before starting new ones.",
        "progress_insight": "You are making progress! Stay consistent.",
        "placement_update": "Focus on DSA every day. It is the most tested topic.",
    }


def _get_sample_interview_questions():
    return {
        "technical": [
            {"question": "What is the time complexity of binary search?",
             "expected_answer": "O(log n)", "tips": "Explain why with a tree analogy", "difficulty": "easy"},
            {"question": "Explain the 4 pillars of OOP.",
             "expected_answer": "Encapsulation, Inheritance, Polymorphism, Abstraction with examples",
             "tips": "Give real-world analogies", "difficulty": "easy"},
        ],
        "hr": [
            {"question": "Tell me about yourself.",
             "expected_answer": "Academic background, projects, skills, career goal (under 2 minutes)",
             "tips": "Practice until fluent"},
        ],
        "coding": [
            {"question": "Reverse a string without using built-in functions.",
             "expected_answer": "Two-pointer approach O(n) time O(1) space",
             "example": "Input: hello → Output: olleh",
             "time_complexity": "O(n)"},
        ],
    }
