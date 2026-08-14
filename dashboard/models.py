import uuid
from django.db import models
from django.conf import settings


class PortalCertificate(models.Model):
    """Legitimate PlacementPro Portal Achievement / Completion Certificate."""
    ACHIEVEMENT_TYPES = [
        ('test_excellence', 'Mock Test Excellence'),
        ('study_plan', 'Study Plan Completion'),
        ('placement_readiness', 'Placement Readiness Achievement'),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='portal_certificates')
    certificate_id = models.CharField(max_length=50, unique=True, editable=False)
    title = models.CharField(max_length=250)
    achievement_type = models.CharField(max_length=50, choices=ACHIEVEMENT_TYPES, default='test_excellence')
    description = models.TextField(blank=True)
    score_percentage = models.FloatField(default=0.0)
    issued_date = models.DateField(auto_now_add=True)
    is_valid = models.BooleanField(default=True)

    class Meta:
        ordering = ['-issued_date']

    def save(self, *args, **kwargs):
        if not self.certificate_id:
            self.certificate_id = f"PP-CERT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} — {self.student.get_full_name() or self.student.username} ({self.certificate_id})"
