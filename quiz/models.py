"""
Quiz Models — Questions, Mock Tests, Results
"""
from django.db import models
from django.conf import settings


class Subject(models.Model):
    """Academic subject model."""
    SUBJECT_CATEGORIES = [
        ('core', 'Core CS'),
        ('aptitude', 'Aptitude'),
        ('verbal', 'Verbal'),
        ('reasoning', 'Logical Reasoning'),
        ('programming', 'Programming'),
        ('database', 'Database'),
        ('networking', 'Networking'),
        ('os', 'Operating Systems'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, blank=True)
    category = models.CharField(max_length=30, choices=SUBJECT_CATEGORIES, default='core')
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-book')
    color = models.CharField(max_length=20, default='primary')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Question(models.Model):
    """MCQ Question for quiz, mock test, or practice."""

    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('java', 'Java'),
        ('c', 'C'),
        ('cpp', 'C++'),
        ('javascript', 'JavaScript'),
        ('sql', 'SQL'),
        ('general', 'General'),
    ]

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='questions')
    company = models.ForeignKey('companies.Company', on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    correct_answer = models.CharField(
        max_length=1,
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]
    )
    explanation = models.TextField(blank=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='general')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['subject', 'difficulty']

    def __str__(self):
        return f"[{self.subject.name}] {self.question_text[:80]}"

    def get_options(self):
        return {
            'A': self.option_a,
            'B': self.option_b,
            'C': self.option_c,
            'D': self.option_d,
        }

    @property
    def text(self):
        """Alias for question_text (backward compatibility)."""
        return self.question_text

    @property
    def marks(self):
        return 1

    @property
    def code_snippet(self):
        return None


class MockTest(models.Model):
    """Mock test / quiz created by faculty or auto-generated."""

    TEST_TYPE_CHOICES = [
        ('mock', 'Mock Test'),
        ('practice', 'Practice Quiz'),
        ('aptitude', 'Aptitude Test'),
        ('coding', 'Coding Challenge'),
        ('placement', 'Placement Test'),
    ]

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    company = models.ForeignKey('companies.Company', on_delete=models.SET_NULL, null=True, blank=True)
    questions = models.ManyToManyField(Question, blank=True)
    test_type = models.CharField(max_length=20, choices=TEST_TYPE_CHOICES, default='mock')
    duration_minutes = models.IntegerField(default=60)
    total_marks = models.IntegerField(default=100)
    passing_marks = models.IntegerField(default=40)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def question_count(self):
        return self.questions.count()


class TestAttempt(models.Model):
    """Student's attempt at a mock test."""

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='test_attempts')
    test = models.ForeignKey(MockTest, on_delete=models.CASCADE, related_name='attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    wrong_answers = models.IntegerField(default=0)
    skipped = models.IntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    time_taken_seconds = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-started_at']
        unique_together = ('student', 'test')

    def __str__(self):
        return f"{self.student.username} — {self.test.title}"

    def calculate_result(self):
        """Calculate and store test results."""
        total = self.test.question_count
        if total > 0:
            self.percentage = (self.correct_answers / total) * 100
        self.is_completed = True
        self.save()


class QuestionAnswer(models.Model):
    """Student's answer for each question in an attempt."""

    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=1, blank=True)
    is_correct = models.BooleanField(default=False)
    time_taken_seconds = models.IntegerField(default=0)

    class Meta:
        unique_together = ('attempt', 'question')

    def save(self, *args, **kwargs):
        self.is_correct = (self.selected_answer == self.question.correct_answer)
        super().save(*args, **kwargs)


class Bookmark(models.Model):
    """Bookmarked questions by students."""
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'question')
