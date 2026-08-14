"""
Resume Builder Views — Create, Edit, Preview, PDF download, ATS Score
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import Resume, Education, WorkExperience, Project, Skill, Certification
from core.ai_service import review_resume as ai_review_resume
import json


@login_required
def resume_home(request):
    """List all resumes."""
    resumes = Resume.objects.filter(student=request.user)
    return render(request, 'resume/home.html', {'resumes': resumes})


@login_required
def create_resume(request):
    """Create a new resume."""
    if request.method == 'POST':
        resume = Resume.objects.create(
            student=request.user,
            title=request.POST.get('title', 'My Resume'),
            template=request.POST.get('template', 'modern'),
            full_name=request.POST.get('full_name', request.user.get_full_name()),
            email=request.POST.get('email', request.user.email),
            phone=request.POST.get('phone', ''),
            location=request.POST.get('location', ''),
            linkedin=request.POST.get('linkedin', ''),
            github=request.POST.get('github', ''),
            portfolio=request.POST.get('portfolio', ''),
            summary=request.POST.get('summary', ''),
        )
        messages.success(request, '✅ Resume created! Now add your details.')
        return redirect('resume_builder:edit', pk=resume.pk)

    return render(request, 'resume/create.html', {'templates': Resume.TEMPLATE_CHOICES})


@login_required
def edit_resume(request, pk):
    """Edit resume and all sections."""
    resume = get_object_or_404(Resume, pk=pk, student=request.user)

    if request.method == 'POST':
        resume.title = request.POST.get('title', resume.title)
        resume.full_name = request.POST.get('full_name', resume.full_name)
        resume.email = request.POST.get('email', resume.email)
        resume.phone = request.POST.get('phone', resume.phone)
        resume.location = request.POST.get('location', resume.location)
        resume.linkedin = request.POST.get('linkedin', resume.linkedin)
        resume.github = request.POST.get('github', resume.github)
        resume.portfolio = request.POST.get('portfolio', resume.portfolio)
        resume.summary = request.POST.get('summary', resume.summary)
        resume.template = request.POST.get('template', resume.template)
        resume.save()
        messages.success(request, '✅ Resume updated!')
        return redirect('resume_builder:edit', pk=pk)

    context = {
        'resume': resume,
        'educations': resume.educations.all(),
        'experiences': resume.experiences.all(),
        'projects': resume.projects.all(),
        'skills': resume.skills.all(),
        'certifications': resume.certifications.all(),
        'templates': Resume.TEMPLATE_CHOICES,
        'skill_types': Skill.SKILL_TYPE_CHOICES,
        'skill_levels': Skill.LEVEL_CHOICES,
    }
    return render(request, 'resume/edit.html', context)


@login_required
def preview_resume(request, pk):
    """Preview resume in selected template."""
    resume = get_object_or_404(Resume, pk=pk, student=request.user)
    context = {
        'resume': resume,
        'educations': resume.educations.all(),
        'experiences': resume.experiences.all(),
        'projects': resume.projects.all(),
        'skills': resume.skills.all(),
        'certifications': resume.certifications.all(),
    }
    return render(request, f'resume/templates/{resume.template}.html', context)


@login_required
def download_resume_pdf(request, pk):
    """Generate and download resume as PDF using ReportLab."""
    resume = get_object_or_404(Resume, pk=pk, student=request.user)

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        import io

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)

        styles = getSampleStyleSheet()
        story = []

        # Title style
        name_style = ParagraphStyle('Name', parent=styles['Title'],
                                     fontSize=22, textColor=colors.HexColor('#1e293b'),
                                     alignment=TA_CENTER, spaceAfter=6)
        contact_style = ParagraphStyle('Contact', parent=styles['Normal'],
                                        fontSize=9, textColor=colors.HexColor('#64748b'),
                                        alignment=TA_CENTER, spaceAfter=12)
        section_style = ParagraphStyle('Section', parent=styles['Heading2'],
                                        fontSize=12, textColor=colors.HexColor('#6366f1'),
                                        spaceBefore=12, spaceAfter=4)
        body_style = ParagraphStyle('Body', parent=styles['Normal'],
                                     fontSize=10, textColor=colors.HexColor('#374151'), spaceAfter=4)

        # Name
        story.append(Paragraph(resume.full_name, name_style))

        # Contact line
        contact_parts = []
        if resume.email: contact_parts.append(resume.email)
        if resume.phone: contact_parts.append(resume.phone)
        if resume.location: contact_parts.append(resume.location)
        if resume.linkedin: contact_parts.append(f'LinkedIn: {resume.linkedin}')
        if resume.github: contact_parts.append(f'GitHub: {resume.github}')
        story.append(Paragraph(' | '.join(contact_parts), contact_style))
        story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#6366f1')))

        # Summary
        if resume.summary:
            story.append(Paragraph('PROFESSIONAL SUMMARY', section_style))
            story.append(Paragraph(resume.summary, body_style))

        # Education
        if resume.educations.exists():
            story.append(Paragraph('EDUCATION', section_style))
            story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#e2e8f0')))
            for edu in resume.educations.all():
                story.append(Paragraph(
                    f'<b>{edu.degree}</b> — {edu.institution} ({edu.start_year}–{edu.end_year or "Present"})',
                    body_style
                ))
                if edu.grade:
                    story.append(Paragraph(f'Grade: {edu.grade}', body_style))

        # Experience
        if resume.experiences.exists():
            story.append(Paragraph('EXPERIENCE', section_style))
            story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#e2e8f0')))
            for exp in resume.experiences.all():
                end = 'Present' if exp.is_current else str(exp.end_date)
                story.append(Paragraph(f'<b>{exp.job_title}</b> at {exp.company} ({exp.start_date} – {end})', body_style))
                if exp.description:
                    story.append(Paragraph(exp.description, body_style))

        # Projects
        if resume.projects.exists():
            story.append(Paragraph('PROJECTS', section_style))
            story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#e2e8f0')))
            for proj in resume.projects.all():
                story.append(Paragraph(f'<b>{proj.title}</b>', body_style))
                story.append(Paragraph(proj.description, body_style))
                if proj.technologies:
                    story.append(Paragraph(f'Tech: {proj.technologies}', body_style))

        # Skills
        if resume.skills.exists():
            story.append(Paragraph('SKILLS', section_style))
            story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#e2e8f0')))
            skill_text = ' • '.join([f'{s.name}' for s in resume.skills.all()])
            story.append(Paragraph(skill_text, body_style))

        # Certifications
        if resume.certifications.exists():
            story.append(Paragraph('CERTIFICATIONS', section_style))
            story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#e2e8f0')))
            for cert in resume.certifications.all():
                story.append(Paragraph(f'<b>{cert.name}</b> — {cert.issuing_org}', body_style))

        doc.build(story)
        buffer.seek(0)

        response = HttpResponse(buffer.read(), content_type='application/pdf')
        filename = f"{resume.full_name.replace(' ', '_')}_Resume.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        messages.error(request, f'PDF generation failed: {e}')
        return redirect('resume_builder:preview', pk=pk)


@login_required
def ats_score(request, pk):
    """Calculate and display ATS score with optional Job Description matching."""
    resume = get_object_or_404(Resume, pk=pk, student=request.user)
    job_description = request.POST.get('job_description', '').strip() or request.GET.get('jd', '').strip()

    resume_data = {
        'full_name': resume.full_name,
        'summary': resume.summary,
        'skills': [s.name for s in resume.skills.all()],
        'education': ' '.join([f'{e.degree} {e.institution}' for e in resume.educations.all()]),
        'experience': ' '.join([f'{e.job_title} {e.company}' for e in resume.experiences.all()]),
        'projects': ' '.join([f'{p.title} {p.technologies}' for p in resume.projects.all()]),
        'certifications': ' '.join([c.name for c in resume.certifications.all()]),
    }

    result = ai_review_resume(resume_data, job_description=job_description)
    review = result.get('review', {})

    # Update ATS score in database
    if 'ats_score' in review:
        resume.ats_score = review['ats_score']
        resume.ai_feedback = json.dumps(review)
        resume.save()

    return render(request, 'resume/ats_score.html', {
        'resume': resume, 'review': review, 'job_description': job_description
    })


@login_required
def ai_suggestions(request, pk):
    """Get AI suggestions for improving resume."""
    resume = get_object_or_404(Resume, pk=pk, student=request.user)
    feedback = {}
    if resume.ai_feedback:
        try:
            feedback = json.loads(resume.ai_feedback)
        except json.JSONDecodeError:
            pass
    return render(request, 'resume/ai_suggestions.html', {'resume': resume, 'feedback': feedback})


@login_required
def delete_resume(request, pk):
    resume = get_object_or_404(Resume, pk=pk, student=request.user)
    resume.delete()
    messages.success(request, '🗑️ Resume deleted.')
    return redirect('resume_builder:home')


# Section CRUD views
@login_required
def add_education(request, resume_pk):
    resume = get_object_or_404(Resume, pk=resume_pk, student=request.user)
    if request.method == 'POST':
        Education.objects.create(
            resume=resume,
            degree=request.POST.get('degree', ''),
            institution=request.POST.get('institution', ''),
            field_of_study=request.POST.get('field_of_study', ''),
            start_year=int(request.POST.get('start_year', 2020)),
            end_year=request.POST.get('end_year') or None,
            grade=request.POST.get('grade', ''),
            description=request.POST.get('description', ''),
        )
        messages.success(request, '✅ Education added!')
    return redirect('resume_builder:edit', pk=resume_pk)


@login_required
def add_experience(request, resume_pk):
    resume = get_object_or_404(Resume, pk=resume_pk, student=request.user)
    if request.method == 'POST':
        WorkExperience.objects.create(
            resume=resume,
            job_title=request.POST.get('job_title', ''),
            company=request.POST.get('company', ''),
            location=request.POST.get('location', ''),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date') or None,
            is_current='is_current' in request.POST,
            description=request.POST.get('description', ''),
        )
        messages.success(request, '✅ Experience added!')
    return redirect('resume_builder:edit', pk=resume_pk)


@login_required
def add_project(request, resume_pk):
    resume = get_object_or_404(Resume, pk=resume_pk, student=request.user)
    if request.method == 'POST':
        Project.objects.create(
            resume=resume,
            title=request.POST.get('title', ''),
            description=request.POST.get('description', ''),
            technologies=request.POST.get('technologies', ''),
            github_link=request.POST.get('github_link', ''),
            live_link=request.POST.get('live_link', ''),
        )
        messages.success(request, '✅ Project added!')
    return redirect('resume_builder:edit', pk=resume_pk)


@login_required
def add_skill(request, resume_pk):
    resume = get_object_or_404(Resume, pk=resume_pk, student=request.user)
    if request.method == 'POST':
        skill_names = request.POST.get('skills', '').split(',')
        skill_type = request.POST.get('skill_type', 'technical')
        for name in skill_names:
            name = name.strip()
            if name:
                Skill.objects.create(resume=resume, name=name, skill_type=skill_type)
        messages.success(request, '✅ Skills added!')
    return redirect('resume_builder:edit', pk=resume_pk)


@login_required
def add_certification(request, resume_pk):
    resume = get_object_or_404(Resume, pk=resume_pk, student=request.user)
    if request.method == 'POST':
        Certification.objects.create(
            resume=resume,
            name=request.POST.get('name', ''),
            issuing_org=request.POST.get('issuing_org', ''),
            issue_date=request.POST.get('issue_date') or None,
            expiry_date=request.POST.get('expiry_date') or None,
            credential_id=request.POST.get('credential_id', ''),
            credential_url=request.POST.get('credential_url', ''),
        )
        messages.success(request, '✅ Certification added!')
    return redirect('resume_builder:edit', pk=resume_pk)
