"""
Resume Builder Models
"""
from django.db import models
from django.conf import settings


class Resume(models.Model):
    """Student's resume."""

    TEMPLATE_CHOICES = [
        ('modern', 'Modern'),
        ('classic', 'Classic'),
        ('minimal', 'Minimal'),
        ('professional', 'Professional'),
        ('creative', 'Creative'),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='resumes')
    title = models.CharField(max_length=200, default='My Resume')
    template = models.CharField(max_length=20, choices=TEMPLATE_CHOICES, default='modern')

    # Personal Info
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True)
    location = models.CharField(max_length=200, blank=True)
    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)
    portfolio = models.URLField(blank=True)
    summary = models.TextField(blank=True, help_text='Professional summary / objective')

    # Scores
    ats_score = models.IntegerField(default=0)
    ai_feedback = models.TextField(blank=True)

    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} — {self.student.username}"


class Education(models.Model):
    """Education section of resume."""
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='educations')
    degree = models.CharField(max_length=200)
    institution = models.CharField(max_length=300)
    field_of_study = models.CharField(max_length=200, blank=True)
    start_year = models.IntegerField()
    end_year = models.IntegerField(null=True, blank=True)
    grade = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['-end_year', '-start_year']


class WorkExperience(models.Model):
    """Work experience section."""
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='experiences')
    job_title = models.CharField(max_length=200)
    company = models.CharField(max_length=300)
    location = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['-start_date']


class Project(models.Model):
    """Projects section."""
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=300)
    description = models.TextField()
    technologies = models.CharField(max_length=500, blank=True)
    github_link = models.URLField(blank=True)
    live_link = models.URLField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']


class Skill(models.Model):
    """Skills section."""
    SKILL_TYPE_CHOICES = [
        ('technical', 'Technical'),
        ('soft', 'Soft Skills'),
        ('language', 'Programming Language'),
        ('tool', 'Tools & Technologies'),
        ('framework', 'Frameworks'),
        ('database', 'Databases'),
        ('other', 'Other'),
    ]

    LEVEL_CHOICES = [
        (1, 'Beginner'),
        (2, 'Elementary'),
        (3, 'Intermediate'),
        (4, 'Advanced'),
        (5, 'Expert'),
    ]

    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    skill_type = models.CharField(max_length=20, choices=SKILL_TYPE_CHOICES, default='technical')
    level = models.IntegerField(choices=LEVEL_CHOICES, default=3)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['skill_type', 'order']


class Certification(models.Model):
    """Certifications section."""
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=300)
    issuing_org = models.CharField(max_length=200)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    credential_id = models.CharField(max_length=200, blank=True)
    credential_url = models.URLField(blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['-issue_date']


class Achievement(models.Model):
    """Achievements/Awards section."""
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE,
                               related_name='resume_achievements', null=True, blank=True)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='achievements')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    date = models.DateField(null=True, blank=True)
    badge_icon = models.CharField(max_length=50, default='bi-trophy')
    badge_color = models.CharField(max_length=20, default='warning')
    points = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.student.username}"
