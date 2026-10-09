"""
Generator script for PlacementPro_AI_Presentation.pptx
Built with python-pptx for IBM SkillsBuild Masterclass 5 Submission.
"""
import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

OUTPUT_FILE = os.path.abspath("PlacementPro_AI_Presentation.pptx")
USER_IMG_DIR = r"C:\Users\nitesh\.gemini\antigravity-ide\brain\c497764b-b824-4844-8213-76c95e7583c0\.user_uploaded"

# Color Palette (Professional Dark Tech / IBM Theme)
COLOR_BG_DARK = RGBColor(15, 23, 42)       # #0F172A (Deep Slate Navy)
COLOR_CARD_BG = RGBColor(30, 41, 59)      # #1E293B (Card Slate)
COLOR_CARD_BORDER = RGBColor(51, 65, 85)  # #334155
COLOR_PRIMARY = RGBColor(99, 102, 241)     # #6366F1 (Indigo / AI Brand)
COLOR_CYAN = RGBColor(56, 189, 248)        # #38BDF8 (Sky Cyan Accent)
COLOR_WHITE = RGBColor(255, 255, 255)
COLOR_TEXT_MUTED = RGBColor(148, 163, 184) # #94A3B8
COLOR_TEXT_LIGHT = RGBColor(226, 232, 240) # #E2E8F0
COLOR_EMERALD = RGBColor(16, 185, 129)     # #10B981 (Success / SDG 8)
COLOR_AMBER = RGBColor(245, 158, 11)       # #F59E0B (SDG 4 / Quality)
COLOR_RED = RGBColor(239, 68, 68)          # #EF4444 (SDG Accent)

prs = Presentation()
# Set widescreen 16:9 (13.333 x 7.5 inches)
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

blank_layout = prs.slide_layouts[6]  # Blank slide

def create_base_slide(header_pill="IBM SKILLSBUILD MASTERCLASS 5", title="", subtitle=""):
    """Creates a slide with unified dark background, header banner and title."""
    slide = prs.slides.add_slide(blank_layout)
    
    # Background rectangle
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = COLOR_BG_DARK
    bg.line.color.rgb = COLOR_BG_DARK
    
    # Top Category Pill
    pill_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.4))
    tf_pill = pill_box.text_frame
    tf_pill.word_wrap = True
    tf_pill.margin_left = tf_pill.margin_top = tf_pill.margin_right = tf_pill.margin_bottom = 0
    p_pill = tf_pill.paragraphs[0]
    p_pill.text = f"●  {header_pill.upper()}"
    p_pill.font.name = "Segoe UI"
    p_pill.font.size = Pt(10.5)
    p_pill.font.bold = True
    p_pill.font.color.rgb = COLOR_CYAN

    # Title & Subtitle box
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Inches(1.1))
    tf_t = title_box.text_frame
    tf_t.word_wrap = True
    tf_t.margin_left = tf_t.margin_top = tf_t.margin_right = tf_t.margin_bottom = 0
    p_title = tf_t.paragraphs[0]
    p_title.text = title
    p_title.font.name = "Segoe UI"
    p_title.font.size = Pt(24)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_WHITE
    
    if subtitle:
        p_sub = tf_t.add_paragraph()
        p_sub.text = subtitle
        p_sub.font.name = "Segoe UI"
        p_sub.font.size = Pt(12.5)
        p_sub.font.color.rgb = COLOR_TEXT_MUTED
        p_sub.space_before = Pt(4)

    # Footer banner
    footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.05), Inches(11.7), Inches(0.35))
    tf_f = footer_box.text_frame
    tf_f.margin_left = tf_f.margin_top = tf_f.margin_right = tf_f.margin_bottom = 0
    p_f = tf_f.paragraphs[0]
    p_f.text = "PlacementPro AI  |  Undergraduate Academic & Placement Copilot  |  IBM SkillsBuild Masterclass 5"
    p_f.font.name = "Segoe UI"
    p_f.font.size = Pt(9)
    p_f.font.color.rgb = COLOR_TEXT_MUTED

    return slide

def add_card(slide, left, top, width, height, title="", body_bullets=None, accent_color=COLOR_PRIMARY, title_badge=None):
    """Draws a modern container card with rounded rectangle appearance."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = COLOR_CARD_BG
    card.line.color.rgb = COLOR_CARD_BORDER
    card.line.width = Pt(1)

    # Inner text box
    tb = slide.shapes.add_textbox(left + Inches(0.25), top + Inches(0.2), width - Inches(0.5), height - Inches(0.4))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    if title:
        p0 = tf.paragraphs[0]
        p0.text = title
        p0.font.name = "Segoe UI"
        p0.font.size = Pt(14)
        p0.font.bold = True
        p0.font.color.rgb = accent_color
        p0.space_after = Pt(8)
    
    if body_bullets:
        for i, item in enumerate(body_bullets):
            p = tf.add_paragraph() if (title or i > 0) else tf.paragraphs[0]
            p.text = f"•  {item}" if not item.startswith("  ") else f"    - {item.strip()}"
            p.font.name = "Segoe UI"
            p.font.size = Pt(11)
            p.font.color.rgb = COLOR_TEXT_LIGHT
            p.space_after = Pt(5)

    return card

def set_speaker_notes(slide, notes_text):
    """Assigns formatted speaker notes to the slide."""
    notes_slide = slide.notes_slide
    tf = notes_slide.notes_text_frame
    tf.text = notes_text.strip()


# ==============================================================================
# SLIDE 1: Project Title and Introduction
# ==============================================================================
s1 = prs.slides.add_slide(blank_layout)
bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
bg1.fill.solid()
bg1.fill.fore_color.rgb = COLOR_BG_DARK
bg1.line.color.rgb = COLOR_BG_DARK

# Hero presentation box
tb_hero = s1.shapes.add_textbox(Inches(1.2), Inches(1.2), Inches(10.9), Inches(4.5))
tf_hero = tb_hero.text_frame
tf_hero.word_wrap = True

p_h0 = tf_hero.paragraphs[0]
p_h0.text = "IBM SKILLSBUILD MASTERCLASS 5 SUBMISSION"
p_h0.font.name = "Segoe UI"
p_h0.font.size = Pt(12)
p_h0.font.bold = True
p_h0.font.color.rgb = COLOR_CYAN
p_h0.space_after = Pt(14)

p_h1 = tf_hero.add_paragraph()
p_h1.text = "PlacementPro AI"
p_h1.font.name = "Segoe UI"
p_h1.font.size = Pt(40)
p_h1.font.bold = True
p_h1.font.color.rgb = COLOR_WHITE
p_h1.space_after = Pt(8)

p_h2 = tf_hero.add_paragraph()
p_h2.text = "Next-Generation Campus Placement & Intelligent Academic Copilot"
p_h2.font.name = "Segoe UI"
p_h2.font.size = Pt(18)
p_h2.font.bold = True
p_h2.font.color.rgb = COLOR_PRIMARY
p_h2.space_after = Pt(18)

p_h3 = tf_hero.add_paragraph()
p_h3.text = "An AI-native full-stack educational platform connecting university curriculum mastery directly to corporate tech recruitment readiness through contextual syllabus reasoning and automated skill assessment."
p_h3.font.name = "Segoe UI"
p_h3.font.size = Pt(13)
p_h3.font.color.rgb = COLOR_TEXT_LIGHT
p_h3.space_after = Pt(28)

p_h4 = tf_hero.add_paragraph()
p_h4.text = "Author / Developer: Undergraduate Engineering Candidate\nFramework: Django 6.1  •  AI Engine: NVIDIA Nemotron 30B  •  Target: B.Tech Engineering Students"
p_h4.font.name = "Segoe UI"
p_h4.font.size = Pt(11)
p_h4.font.color.rgb = COLOR_TEXT_MUTED

set_speaker_notes(s1, """Good day evaluators. Welcome to the presentation of PlacementPro AI for the IBM SkillsBuild Masterclass 5 submission.
PlacementPro AI is an enterprise-grade academic learning and placement acceleration platform built specifically for undergraduate engineering students.
Our core mission is to bridge the historical disconnect between semester coursework and competitive campus recruitment drives by turning static university syllabi into interactive AI cognitive tutors.""")


# ==============================================================================
# SLIDE 2: Problem Statement
# ==============================================================================
s2 = create_base_slide(
    header_pill="The Student Dilemma & Institutional Challenges",
    title="Problem Statement: The Dual Pressure on Engineering Students",
    subtitle="Undergraduates face two conflicting demands with fragmented, passive tools."
)
add_card(s2, Inches(0.8), Inches(2.1), Inches(3.6), Inches(4.6),
    title="1. Academic Semester Pressure",
    body_bullets=[
        "Dense theoretical coursework across 5-6 core CS subjects each semester (DSA, DBMS, OS, Networks).",
        "Rigid exam schedules demanding high CGPA benchmarks for initial placement eligibility.",
        "Static PDF syllabi provide no interactive support when students face conceptual hurdles during late-night study.",
        "Limited faculty office hours cannot scale to 1-on-1 tutoring for hundreds of cohort students."
    ],
    accent_color=COLOR_AMBER
)
add_card(s2, Inches(4.8), Inches(2.1), Inches(3.6), Inches(4.6),
    title="2. Industry Placement Bar",
    body_bullets=[
        "Tier-1 corporate recruitment requires deep algorithmic problem-solving and clean system design.",
        "Aptitude rounds eliminate up to 70% of applicants in initial screening tests.",
        "ATS resume filters reject qualified candidates due to missing industry keywords or poor bullet structure.",
        "Students only discover their readiness gaps after failing company tests when it is already too late."
    ],
    accent_color=COLOR_RED
)
add_card(s2, Inches(8.8), Inches(2.1), Inches(3.6), Inches(4.6),
    title="3. Fragmented Ecosystem",
    body_bullets=[
        "Students juggle 5 to 7 disconnected tools: YouTube for lectures, LeetCode for DSA, Canva for CVs.",
        "Zero unified data pipeline connects curriculum learning to placement assessment scores.",
        "Training & Placement Officers (TPOs) lack real-time cohort telemetry to track student readiness.",
        "High preparation anxiety and uneven access to quality personalized mentorship."
    ],
    accent_color=COLOR_CYAN
)
set_speaker_notes(s2, """Here we address the problem statement. B.Tech students in India and globally face a dual burden. On one side, they must master 5 to 6 dense subjects every semester to maintain their CGPA. On the other side, tech companies like Google, Microsoft, TCS, and Amazon evaluate them on algorithmic proficiency, aptitude, and ATS resumes.
Currently, students juggle disconnected websites—YouTube, LeetCode, PDF notes—with no unified system tracking their actual placement readiness. PlacementPro AI solves this fragmentation.""")


# ==============================================================================
# SLIDE 3: Target Users and SDG Alignment
# ==============================================================================
s3 = create_base_slide(
    header_pill="Beneficiaries & United Nations Global Goals",
    title="Target Users & Sustainable Development Goals (SDGs)",
    subtitle="Aligned with UN SDG 4 (Quality Education) and SDG 8 (Decent Work & Economic Growth)."
)
add_card(s3, Inches(0.8), Inches(2.1), Inches(5.6), Inches(2.2),
    title="Target User Archetypes",
    body_bullets=[
        "Primary Users: B.Tech / B.E. / BCA / MCA undergraduate students preparing simultaneously for university semester exams and campus placement seasons.",
        "Institutional Administrators & TPOs: Training & Placement Officers who monitor batch performance, schedule mock tests, and inspect recruitment readiness metrics."
    ],
    accent_color=COLOR_PRIMARY
)
add_card(s3, Inches(0.8), Inches(4.5), Inches(5.6), Inches(2.2),
    title="Pedagogical Philosophy",
    body_bullets=[
        "Active Cognitive Partnership: Moving away from passive PDF reading to active AI inquiry.",
        "Democratized Mentorship: Ensuring equal access to top-tier technical guidance regardless of college tier or faculty availability."
    ],
    accent_color=COLOR_CYAN
)
add_card(s3, Inches(6.8), Inches(2.1), Inches(5.7), Inches(2.2),
    title="SDG 4: Quality Education (Primary Alignment)",
    body_bullets=[
        "Target 4.4: Substantially increase the number of youth who have relevant technical and vocational skills for employment and decent jobs.",
        "AI-Powered Syllabus Tutoring: Bridges curriculum gaps with real-time, context-grounded step-by-step doubt resolution.",
        "Personalized Adaptive Learning: Tailors study timetables and practice tests to individual learning velocities."
    ],
    accent_color=COLOR_AMBER
)
add_card(s3, Inches(6.8), Inches(4.5), Inches(5.7), Inches(2.2),
    title="SDG 8: Decent Work & Economic Growth (Secondary)",
    body_bullets=[
        "Target 8.6: Substantially reduce the proportion of youth not in employment, education or training (NEET).",
        "Pre-Recruitment Diagnostic Audits: ATS resume scoring and simulated interview practice directly enhance employability.",
        "Skill Gap Analysis: Pinpoints exact missing competencies required by hiring tech companies."
    ],
    accent_color=COLOR_EMERALD
)
set_speaker_notes(s3, """Slide 3 outlines our target users and UN SDG alignment.
Our primary beneficiaries are undergraduate engineering students and college placement cells.
We directly align with UN SDG 4—Quality Education—by democratizing 24/7 AI tutoring across engineering subjects.
Secondarily, we align with SDG 8—Decent Work and Economic Growth—by giving students the practical interview readiness and ATS-optimized skills needed to secure productive, high-value employment upon graduation.""")


# ==============================================================================
# SLIDE 4: Proposed Solution
# ==============================================================================
s4 = create_base_slide(
    header_pill="Platform Architecture & Value Proposition",
    title="Proposed Solution: The PlacementPro AI Unified Ecosystem",
    subtitle="A unified AI copilot combining academic syllabus comprehension with placement pipelines."
)
add_card(s4, Inches(0.8), Inches(2.1), Inches(3.6), Inches(4.6),
    title="1. Academic Intelligence",
    body_bullets=[
        "Syllabus Document Ingestion: Upload departmental PDF, Word (.docx), or text curriculum.",
        "Hierarchical Module Indexing: Automatically extracts units, competencies, and topics.",
        "Contextual AI Doubt Solver: Grounds queries in specific course modules (e.g. Floyd's cycle detection in Module 1).",
        "Adaptive Timetable Synthesis: Mathematically allocates daily study hours using Pomodoro intervals."
    ],
    accent_color=COLOR_PRIMARY
)
add_card(s4, Inches(4.8), Inches(2.1), Inches(3.6), Inches(4.6),
    title="2. Placement Pipeline",
    body_bullets=[
        "Mock Test Assessment Engine: Timed exams covering DSA, DBMS, OS, Networks, Java, and Aptitude.",
        "ATS Resume Auditor: Evaluates CVs against recruiter standards with instant keyword gap analysis.",
        "AI Technical & HR Interviewer: Interactive conversational rounds scoring completeness, depth, and clarity.",
        "Placement Readiness Score (PRS): A dynamic 0-100 index combining assessment results."
    ],
    accent_color=COLOR_CYAN
)
add_card(s4, Inches(8.8), Inches(2.1), Inches(3.6), Inches(4.6),
    title="3. Institutional Governance",
    body_bullets=[
        "Admin Neural Command Center: High-authority control room for placement officers.",
        "Live Batch Analytics: Real-time telemetry on student participation, test completion, and company drives.",
        "Zero-Friction Role Separation: Distinct boundaries protecting student learner workspaces and admin oversight.",
        "Exportable Documentation: Built-in client-ready Concept Notes and PDF report generators."
    ],
    accent_color=COLOR_EMERALD
)
set_speaker_notes(s4, """Slide 4 presents our proposed solution: PlacementPro AI.
It combines three tightly integrated pillars:
First, Academic Intelligence: Students upload their exact syllabus PDF, and our AI indexes modules for instant, context-aware doubt solving and Pomodoro timetabling.
Second, the Placement Pipeline: Timed assessments, ATS resume auditing, and AI mock interviews that calculate a unified Placement Readiness Score.
Third, Institutional Governance: Dedicated administration dashboards providing cohort telemetry for college placement directors.""")


# ==============================================================================
# SLIDE 5: Key Features
# ==============================================================================
s5 = create_base_slide(
    header_pill="Implemented Functional Capabilities",
    title="Core Implemented Features in PlacementPro AI",
    subtitle="A tour of live modules currently functioning in the working prototype."
)
add_card(s5, Inches(0.8), Inches(2.1), Inches(3.6), Inches(2.2),
    title="Interactive Syllabus Q&A Engine",
    body_bullets=[
        "Upload PDF/DOCX or paste subject syllabi.",
        "NVIDIA Nemotron 30B reasoning responds to module queries and broader real-world tech concepts."
    ],
    accent_color=COLOR_PRIMARY
)
add_card(s5, Inches(4.8), Inches(2.1), Inches(3.6), Inches(2.2),
    title="Adaptive AI Study Planner",
    body_bullets=[
        "Synthesizes custom weekly schedules based on user deadlines and daily available hours.",
        "Built-in Pomodoro timer and active recall milestones."
    ],
    accent_color=COLOR_CYAN
)
add_card(s5, Inches(8.8), Inches(2.1), Inches(3.6), Inches(2.2),
    title="Rich Mock Exam & Assessment Suite",
    body_bullets=[
        "8 comprehensive mock tests covering Python, DBMS, Aptitude, DSA, Java, and Operating Systems.",
        "Timer countdown, instant grading, and answer breakdowns."
    ],
    accent_color=COLOR_AMBER
)
add_card(s5, Inches(0.8), Inches(4.5), Inches(3.6), Inches(2.2),
    title="ATS Resume Auditor & Builder",
    body_bullets=[
        "Parses candidate CVs and computes 0-100 ATS match score.",
        "Identifies missing technical keywords and suggests bullet improvements."
    ],
    accent_color=COLOR_EMERALD
)
add_card(s5, Inches(4.8), Inches(4.5), Inches(3.6), Inches(2.2),
    title="AI Placement Interviewer",
    body_bullets=[
        "Simulates technical and HR interview rounds with interactive AI feedback on clarity, structure, and depth.",
        "Role-specific questions tailored to software engineering."
    ],
    accent_color=COLOR_PRIMARY
)
add_card(s5, Inches(8.8), Inches(4.5), Inches(3.6), Inches(2.2),
    title="Neural Admin Command Center",
    body_bullets=[
        "Institutional analytics monitoring user rosters, subject indexing status, and test completions.",
        "High-authority authentication isolating administrative control."
    ],
    accent_color=COLOR_CYAN
)
set_speaker_notes(s5, """Slide 5 summarizes the functional modules implemented in our working code:
1. The Syllabus Q&A Engine powered by NVIDIA Nemotron 30B.
2. The Adaptive Study Planner with Pomodoro schedules.
3. The Mock Exam suite with over 8 active tests in DSA, DBMS, Java, OS, and Aptitude.
4. The ATS Resume Scanner providing keyword and formatting audits.
5. The AI Interview Simulator with structured candidate feedback.
6. The Neural Admin Command Center for batch monitoring.""")


# ==============================================================================
# SLIDE 6: System Workflow and Architecture
# ==============================================================================
s6 = create_base_slide(
    header_pill="Data Flow & System Architecture",
    title="System Workflow & End-to-End Architecture",
    subtitle="Multi-tier architecture bridging Django MVC with OpenRouter AI Inference."
)
add_card(s6, Inches(0.8), Inches(2.1), Inches(11.7), Inches(1.8),
    title="Data Ingestion & Inference Pipeline",
    body_bullets=[
        "Client Layer: Responsive HTML5/Vanilla CSS interface with dynamic theme switching and secure forms.",
        "Backend Controller (Django 6.1): Dispatches requests via MultiIdentifierBackend, validating permissions and routing.",
        "Document Parsing Engine: Ingests uploaded syllabi (PyPDF2/python-docx), cleans raw text, and extracts module boundaries.",
        "Context Assembly: Injects extracted curriculum context (up to 4,000 tokens) alongside student queries into the prompt pipeline.",
        "AI Reasoning Layer: Dispatches asynchronous requests to OpenRouter (NVIDIA Nemotron 30B) with automatic multi-model fallback.",
        "Response Delivery: Formats structured markdown/JSON outputs and streams results back to the interactive UI."
    ],
    accent_color=COLOR_CYAN
)
add_card(s6, Inches(0.8), Inches(4.2), Inches(3.6), Inches(2.5),
    title="Stage 1: Ingestion & Indexing",
    body_bullets=[
        "Student selects subject (e.g. DSA).",
        "Uploads syllabus document.",
        "System extracts units & competencies.",
        "Curriculum text stored in database."
    ],
    accent_color=COLOR_PRIMARY
)
add_card(s6, Inches(4.8), Inches(4.2), Inches(3.6), Inches(2.5),
    title="Stage 2: Continuous Learning",
    body_bullets=[
        "Student queries AI tutor.",
        "AI grounds response in syllabus.",
        "Takes topic tests and mock exams.",
        "Readiness score updates in real-time."
    ],
    accent_color=COLOR_AMBER
)
add_card(s6, Inches(8.8), Inches(4.2), Inches(3.6), Inches(2.5),
    title="Stage 3: Career Optimization",
    body_bullets=[
        "Candidate scans resume for ATS score.",
        "Practices AI mock interviews.",
        "Reviews company hiring archives.",
        "Admin monitors cohort progress."
    ],
    accent_color=COLOR_EMERALD
)
set_speaker_notes(s6, """Slide 6 details our system architecture and workflow.
When a student uploads a syllabus, our backend extracts text structures using PyPDF2 and python-docx, primes the curriculum buffer, and caches module hierarchies.
When the student asks technical questions, Django constructs an augmented prompt sent to OpenRouter's NVIDIA Nemotron 30B reasoning model.
The student simultaneously takes assessments, updating their Placement Readiness Score in real-time.""")


# ==============================================================================
# SLIDE 7: Technology Stack
# ==============================================================================
s7 = create_base_slide(
    header_pill="Underlying Engineering Stack",
    title="Technology Stack & Implementation Specifications",
    subtitle="Enterprise-grade, secure, and production-ready technologies."
)
add_card(s7, Inches(0.8), Inches(2.1), Inches(2.7), Inches(4.6),
    title="Backend Framework",
    body_bullets=[
        "Django 6.1 (Python 3.14)",
        "Enterprise MTV design pattern",
        "Robust ORM with transactional safety",
        "Cryptographic session handling",
        "Custom MultiIdentifierBackend (Username / Email / Roll No)",
        "High-performance REST API endpoints"
    ],
    accent_color=COLOR_PRIMARY
)
add_card(s7, Inches(3.8), Inches(2.1), Inches(2.7), Inches(4.6),
    title="AI Reasoning Engine",
    body_bullets=[
        "NVIDIA Nemotron 30B Reasoning model",
        "OpenRouter API gateway integration",
        "Multi-model fallback chain for high availability",
        "Context windowing with token budgeting",
        "Pure JSON extraction & markdown formatting"
    ],
    accent_color=COLOR_CYAN
)
add_card(s7, Inches(6.8), Inches(2.1), Inches(2.7), Inches(4.6),
    title="Database & Storage",
    body_bullets=[
        "SQLite (Local Development)",
        "PostgreSQL Ready (Production)",
        "Relational schema covering:",
        "  - User & Student Profiles",
        "  - Study Subjects & Syllabi",
        "  - Question Banks & Tests",
        "  - Test Attempt Telemetry",
        "WhiteNoise for static assets"
    ],
    accent_color=COLOR_AMBER
)
add_card(s7, Inches(9.8), Inches(2.1), Inches(2.7), Inches(4.6),
    title="Frontend & UI",
    body_bullets=[
        "HTML5 & Vanilla CSS3",
        "Modern Glassmorphic design system",
        "Persistent Dark/Light mode theme toggle",
        "Bootstrap Icons library",
        "Zero heavy JavaScript frameworks for maximum speed",
        "Chart.js for interactive analytics"
    ],
    accent_color=COLOR_EMERALD
)
set_speaker_notes(s7, """Slide 7 presents the technology stack.
On the backend, we run Django 6.1 on Python 3.14, utilizing a custom multi-identifier authentication backend.
For AI reasoning, we integrate NVIDIA's Nemotron 30B reasoning architecture through OpenRouter, backed by an automatic fallback chain to ensure high reliability.
The database uses a structured relational schema covering student records, syllabi, questions, and attempt analytics.
The frontend uses responsive HTML5 and Vanilla CSS3 with zero bloat.""")


# ==============================================================================
# SLIDE 8: Actual Application Screenshots and Working Prototype
# ==============================================================================
s8 = create_base_slide(
    header_pill="Live Working Prototype Demonstration",
    title="Actual Application Screenshots & Working Prototype",
    subtitle="Genuine interfaces captured directly from the running PlacementPro AI portal."
)

# Place 2 real screenshot images if available
img1_path = os.path.join(USER_IMG_DIR, "media_1791543706802.png")  # Admin Command Center
img2_path = os.path.join(USER_IMG_DIR, "media_1791539297716.png")  # Student Portal / Dashboard

if os.path.exists(img1_path) and os.path.exists(img2_path):
    # Left Image: Admin Command Center
    s8.shapes.add_picture(img1_path, Inches(0.8), Inches(2.1), width=Inches(5.7))
    cap1 = s8.shapes.add_textbox(Inches(0.8), Inches(5.6), Inches(5.7), Inches(1.1))
    tf1 = cap1.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "Figure 1: AI Placement Command Center (Admin Dashboard)"
    p1.font.bold = True
    p1.font.size = Pt(11)
    p1.font.color.rgb = COLOR_CYAN
    p1_sub = tf1.add_paragraph()
    p1_sub.text = "Features real-time active user telemetry, curriculum indexing counts, partner company tracking, and system health status."
    p1_sub.font.size = Pt(10)
    p1_sub.font.color.rgb = COLOR_TEXT_LIGHT

    # Right Image: Student Portal
    s8.shapes.add_picture(img2_path, Inches(6.8), Inches(2.1), width=Inches(5.7))
    cap2 = s8.shapes.add_textbox(Inches(6.8), Inches(5.6), Inches(5.7), Inches(1.1))
    tf2 = cap2.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.text = "Figure 2: Student Learning Portal & Study Planner Workspace"
    p2.font.bold = True
    p2.font.size = Pt(11)
    p2.font.color.rgb = COLOR_EMERALD
    p2_sub = tf2.add_paragraph()
    p2_sub.text = "Features syllabus upload & AI doubt resolution, Pomodoro session timer, assessment records, and placement readiness tracker."
    p2_sub.font.size = Pt(10)
    p2_sub.font.color.rgb = COLOR_TEXT_LIGHT
else:
    # Fallback to card summary if images are missing
    add_card(s8, Inches(0.8), Inches(2.1), Inches(5.7), Inches(4.6),
        title="Admin Command Center Prototype",
        body_bullets=[
            "Live neural telemetry monitoring student rosters.",
            "Subject syllabus indexing status indicators.",
            "Partner recruiting company directory management."
        ],
        accent_color=COLOR_CYAN
    )
    add_card(s8, Inches(6.8), Inches(2.1), Inches(5.7), Inches(4.6),
        title="Student Learning Workspace Prototype",
        body_bullets=[
            "Interactive AI Doubt Solver with syllabus file ingestion.",
            "Timed mock assessments across 6 core technical subjects.",
            "ATS resume scoring interface with actionable improvement tips."
        ],
        accent_color=COLOR_EMERALD
    )

set_speaker_notes(s8, """Slide 8 showcases genuine screenshots from our actual running application.
On the left is the AI Placement Command Center, providing administrators with live telemetry, active student counts, curriculum subject indexing status, and test completions.
On the right is the Student Learning Portal, showcasing the interactive syllabus tutor, study scheduling interface, and mock test assessment records.""")


# ==============================================================================
# SLIDE 9: Expected Impact and Evaluation Metrics
# ==============================================================================
s9 = create_base_slide(
    header_pill="Impact Measurement & Verification",
    title="Expected Impact & Evaluation Metrics",
    subtitle="Measurable outcomes and rigorous testing methodologies."
)
add_card(s9, Inches(0.8), Inches(2.1), Inches(5.6), Inches(4.6),
    title="Expected Pedagogical & Career Impact",
    body_bullets=[
        "Elevated Placement Conversion: Pre-recruitment diagnostic assessments and ATS optimization directly improve initial corporate shortlisting rates.",
        "Reduction in Exam & Interview Anxiety: Continuous 24/7 access to an intelligent academic tutor reduces dependency on scarce office hours.",
        "Balanced Academic Performance: Structured Pomodoro study plans prevent last-minute cramming and promote sustained CGPA retention.",
        "Institutional Efficiency: Automated mock exam scoring and cohort analytics save hundreds of faculty compilation hours annually.",
        "Bridging College Tier Gaps: Grants students in tier-2/3 institutions access to tier-1 quality placement coaching."
    ],
    accent_color=COLOR_AMBER
)
add_card(s9, Inches(6.8), Inches(2.1), Inches(5.7), Inches(4.6),
    title="Evaluation Metrics & Testing Verification",
    body_bullets=[
        "Functional Verification: All core routes (study planner, mock exams, syllabus Q&A, ATS builder) thoroughly tested and verified with HTTP 200 responses.",
        "Authentication Security: MultiIdentifierBackend strictly enforces role isolation—verified 403 Forbidden protection on administrative routes.",
        "AI Reasoning Accuracy: Tested with complex technical queries (e.g. Floyd's cycle detection in Module 1) with structured, contextual explanations.",
        "Zero Placeholder Architecture: All database subjects and assessments populated with genuine computer science question banks.",
        "Public Documentation Standard: Includes print-optimized executive concept notes ready for institutional review."
    ],
    accent_color=COLOR_EMERALD
)
set_speaker_notes(s9, """Slide 9 discusses expected impact and evaluation metrics.
By diagnosing skill gaps early and auditing resumes against ATS standards, we expect significantly higher corporate shortlisting rates.
Operationally, the platform automates mock test compilation and provides 24/7 tutoring support.
All functional routes have been verified with HTTP 200 responses, strict role security, and real question banks.""")


# ==============================================================================
# SLIDE 10: Conclusion and Future Scope
# ==============================================================================
s10 = create_base_slide(
    header_pill="Roadmap & Next Steps",
    title="Conclusion & Future Scope",
    subtitle="A roadmap for expanding from campus prototype to institutional scale."
)
add_card(s10, Inches(0.8), Inches(2.1), Inches(5.6), Inches(4.6),
    title="Current Accomplishments (Phase 1)",
    body_bullets=[
        "Fully working prototype running locally with Django 6.1.",
        "Real integration with OpenRouter NVIDIA Nemotron 30B reasoning model.",
        "Syllabus file upload (PDF/Word/Text) with contextual AI Q&A.",
        "Mock testing suite with instant grading and timer controls.",
        "ATS resume auditor and AI-assisted resume builder.",
        "Strict role separation isolating student learners and admin owners.",
        "Print-ready Concept Note and complete project documentation."
    ],
    accent_color=COLOR_PRIMARY
)
add_card(s10, Inches(6.8), Inches(2.1), Inches(5.7), Inches(4.6),
    title="Future Roadmap (Phases 2 & 3)",
    body_bullets=[
        "Phase 2: In-Browser Code Sandbox — Integration of WebAssembly/Docker micro-execution for live coding tests with automated test cases.",
        "Phase 3: Multi-Modal Voice & Vision AI Interviewer — WebRTC speech-to-text and facial expression analysis for realistic behavioral mock interviews.",
        "Phase 4: University LMS / ERP Integration — Bi-directional API syncing with Moodle, Canvas, and college attendance portals.",
        "Phase 5: Corporate Recruiter Portal — Dedicated interface for hiring partners to schedule campus drives and filter verified candidate scores."
    ],
    accent_color=COLOR_CYAN
)
set_speaker_notes(s10, """In conclusion, Phase 1 of PlacementPro AI delivers a working, robust educational platform combining syllabus-grounded tutoring, mock testing, and placement diagnostics.
Looking forward, our roadmap includes live WebAssembly code execution, voice-based AI interview simulations, and deeper integrations with university learning management systems.
Thank you for your consideration, and I welcome any questions from the evaluation committee.""")

# Save Presentation
prs.save(OUTPUT_FILE)
print(f"SUCCESS: Presentation successfully generated at: {OUTPUT_FILE}")
