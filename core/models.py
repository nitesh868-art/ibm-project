from django.db import models

"""
Core Models — Curriculum Content System & Activity Audit Logging
"""
from django.db import models
from django.conf import settings


class CurriculumUnit(models.Model):
    """Unit within a Subject curriculum."""
    subject = models.ForeignKey('quiz.Subject', on_delete=models.CASCADE, related_name='units')
    unit_number = models.IntegerField(default=1)
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['subject', 'unit_number']
        unique_together = ('subject', 'unit_number')

    def __str__(self):
        return f"Unit {self.unit_number}: {self.title} [{self.subject.name}]"


class CurriculumTopic(models.Model):
    """Topic within a Curriculum Unit."""
    unit = models.ForeignKey(CurriculumUnit, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=250)
    summary = models.TextField(blank=True)
    key_points = models.TextField(blank=True, help_text="One point per line")
    target_year = models.IntegerField(default=3, choices=[(1,'1st Year'), (2,'2nd Year'), (3,'3rd Year'), (4,'4th Year')])

    class Meta:
        ordering = ['unit', 'id']

    def __str__(self):
        return f"{self.title} ({self.unit.subject.name} - Unit {self.unit.unit_number})"


class StudyMaterial(models.Model):
    """Uploaded or curated study materials (Notes, PDFs, DOCs, Links)."""
    MATERIAL_TYPES = [
        ('pdf', 'PDF Document'),
        ('doc', 'Word Document'),
        ('notes', 'Text Notes'),
        ('link', 'Web Resource / Link'),
        ('video', 'Video Lecture'),
    ]

    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    unit = models.ForeignKey(CurriculumUnit, on_delete=models.SET_NULL, null=True, blank=True, related_name='materials')
    topic = models.ForeignKey(CurriculumTopic, on_delete=models.SET_NULL, null=True, blank=True, related_name='materials')
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPES, default='pdf')
    file = models.FileField(upload_to='study_materials/', null=True, blank=True)
    extracted_text = models.TextField(blank=True, help_text="Extracted text for AI processing")
    page_count = models.IntegerField(default=1, help_text="Total number of document pages")
    is_scanned = models.BooleanField(default=False, help_text="True if scanned/image-only PDF requiring OCR")
    extraction_quality = models.CharField(max_length=50, default='success', help_text="Extraction status")
    external_url = models.URLField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    is_demo = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ActivityLog(models.Model):
    """Audit log for system activities and tracking."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=20, default='student')
    action = models.CharField(max_length=200)
    module = models.CharField(max_length=50, default='General')
    details = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='success')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {user_str} - {self.action} ({self.status})"


def log_activity(user, action, module='General', details='', status='success', request=None):
    """Helper function to log system activity."""
    ip = None
    role = 'anonymous'
    if request:
        ip = request.META.get('REMOTE_ADDR')
        if hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user
            role = getattr(user, 'role', 'student')
    elif user and getattr(user, 'is_authenticated', False):
        role = getattr(user, 'role', 'student')

    try:
        ActivityLog.objects.create(
            user=user if getattr(user, 'is_authenticated', False) else None,
            role=role,
            action=action,
            module=module,
            details=details,
            status=status,
            ip_address=ip,
        )
    except Exception:
        pass
