"""
Study Planner Models — Subject, Topic, StudyPlan, Pomodoro
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class Semester(models.Model):
    """Student's semester with subjects."""
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='semesters')
    number = models.IntegerField()
    name = models.CharField(max_length=100, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'number')
        ordering = ['-number']

    def __str__(self):
        return f"Semester {self.number} — {self.student.username}"


class StudySubject(models.Model):
    """Subject added by student for study planning."""

    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Critical'),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='study_subjects')
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='subjects')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, blank=True)
    credits = models.IntegerField(default=3)
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)
    exam_date = models.DateField(null=True, blank=True)
    difficulty_level = models.IntegerField(default=3, help_text='1-5 scale')
    color = models.CharField(max_length=20, default='#6366f1')
    completion_percentage = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-priority', 'name']

    def __str__(self):
        return f"{self.name} — {self.student.username}"

    def calculate_completion(self):
        total_topics = self.topics.count()
        if total_topics == 0:
            return 0
        completed = self.topics.filter(status='completed').count()
        self.completion_percentage = int((completed / total_topics) * 100)
        self.save()
        return self.completion_percentage


class Topic(models.Model):
    """Topic within a study subject."""

    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('revision', 'Needs Revision'),
    ]

    subject = models.ForeignKey(StudySubject, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=1, default=1.0)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=1, default=0.0)
    deadline = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    resources = models.TextField(blank=True, help_text='Links to resources (one per line)')
    order = models.IntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} [{self.subject.name}]"

    def mark_complete(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        self.subject.calculate_completion()


class StudyPlan(models.Model):
    """AI-generated or manual study plan."""

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='study_plans')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    plan_content = models.TextField(blank=True, help_text='AI-generated or manual plan in JSON/text')
    start_date = models.DateField()
    end_date = models.DateField()
    is_ai_generated = models.BooleanField(default=False)
    ai_prompt = models.TextField(blank=True, help_text='The prompt used to generate this plan')
    subjects = models.ManyToManyField(StudySubject, blank=True)
    daily_study_hours = models.DecimalField(max_digits=4, decimal_places=1, default=4.0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.student.username}"


class DailyStudyLog(models.Model):
    """Daily study time log for analytics."""

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='study_logs')
    date = models.DateField(default=timezone.now)
    subject = models.ForeignKey(StudySubject, on_delete=models.SET_NULL, null=True, blank=True)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    duration_minutes = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        unique_together = ('student', 'date', 'subject', 'topic')

    def __str__(self):
        return f"{self.student.username} — {self.date} — {self.duration_minutes}min"


class PomodoroSession(models.Model):
    """Pomodoro timer session record."""

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    work_minutes = models.IntegerField(default=25)
    break_minutes = models.IntegerField(default=5)
    sessions_completed = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']


class Goal(models.Model):
    """Student's learning goals."""

    GOAL_TYPE_CHOICES = [
        ('daily', 'Daily Goal'),
        ('weekly', 'Weekly Goal'),
        ('monthly', 'Monthly Goal'),
        ('placement', 'Placement Goal'),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='goals')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPE_CHOICES, default='daily')
    target_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} [{self.goal_type}]"


class TopicMastery(models.Model):
    """
    Calculated topic mastery score (0-100%) for each student per topic.
    Updated from:
      - topic completion status (40%)
      - quiz performance on related subject/questions (40%)
      - study log hours (20%)
    """
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='topic_masteries')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='masteries')
    subject = models.ForeignKey(StudySubject, on_delete=models.CASCADE, related_name='topic_masteries')
    mastery_score = models.IntegerField(default=0, help_text='0-100 percentage score')
    quiz_accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    study_minutes = models.IntegerField(default=0)
    is_weak = models.BooleanField(default=False, help_text='True if mastery < 50%')
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'topic')
        ordering = ['mastery_score', 'topic__name']

    def __str__(self):
        return f"{self.student.username} — {self.topic.name}: {self.mastery_score}%"

    def update_mastery(self):
        """Re-calculate mastery score based on status, quiz scores & logs."""
        status_pts = 0
        if self.topic.status == 'completed':
            status_pts = 40
        elif self.topic.status == 'in_progress':
            status_pts = 20
        elif self.topic.status == 'revision':
            status_pts = 10

        from quiz.models import QuestionAnswer
        answers = QuestionAnswer.objects.filter(
            attempt__student=self.student,
            attempt__is_completed=True,
            question__subject__name__iexact=self.subject.name
        )
        if answers.exists():
            correct = answers.filter(is_correct=True).count()
            total = answers.count()
            acc = (correct / total) * 100
            self.quiz_accuracy = round(acc, 1)
            quiz_pts = int((acc / 100) * 40)
        else:
            self.quiz_accuracy = 0
            quiz_pts = 10 if self.topic.status == 'completed' else 0

        logs = DailyStudyLog.objects.filter(student=self.student, subject=self.subject)
        total_mins = sum(l.duration_minutes for l in logs)
        self.study_minutes = total_mins
        study_pts = min(20, int((total_mins / 120) * 20))

        self.mastery_score = min(100, status_pts + quiz_pts + study_pts)
        self.is_weak = (self.mastery_score < 50)
        self.save()
        return self.mastery_score

