"""
Notifications Models
"""
from django.db import models
from django.conf import settings


class Notification(models.Model):
    """System notification for users."""

    TYPE_CHOICES = [
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('danger', 'Alert'),
        ('assignment', 'Assignment'),
        ('test', 'Test'),
        ('placement', 'Placement'),
        ('achievement', 'Achievement'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'

    def __str__(self):
        return f"{self.title} → {self.user.username}"

    @classmethod
    def create_for_user(cls, user, title, message, notification_type='info', link=''):
        """Helper method to create a notification."""
        return cls.objects.create(
            user=user, title=title, message=message,
            notification_type=notification_type, link=link
        )
