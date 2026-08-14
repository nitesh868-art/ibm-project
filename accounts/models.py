"""
Accounts Models — Custom User Model with Role-based Access
===========================================================
Supports: Student, Faculty, Admin roles
Features: Profile picture, email verification, OTP
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import random
import string


class User(AbstractUser):
    """
    Custom User Model extending Django's AbstractUser.
    Adds role-based access control and profile fields.
    """

    ROLE_CHOICES = [
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('admin', 'Administrator'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    is_email_verified = models.BooleanField(default=False)
    email_otp = models.CharField(max_length=6, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)
    last_active = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    @property
    def is_student(self):
        return self.role == 'student'

    @property
    def is_faculty(self):
        return self.role == 'faculty'

    @property
    def is_admin_user(self):
        return self.role == 'admin' or self.is_superuser

    def generate_otp(self):
        """Generate a 6-digit OTP and save it."""
        self.email_otp = ''.join(random.choices(string.digits, k=6))
        self.otp_created_at = timezone.now()
        self.save()
        return self.email_otp

    def is_otp_valid(self, otp):
        """Check OTP validity (expires in 10 minutes)."""
        if self.email_otp != otp:
            return False
        if not self.otp_created_at:
            return False
        expiry = self.otp_created_at + timezone.timedelta(minutes=10)
        return timezone.now() <= expiry

    def get_profile_picture_url(self):
        """Return profile picture URL or default avatar."""
        if self.profile_picture:
            return self.profile_picture.url
        return '/static/images/default_avatar.png'


class StudentProfile(models.Model):
    """Extended profile for students."""

    YEAR_CHOICES = [(i, f'{i}{"st" if i==1 else "nd" if i==2 else "rd" if i==3 else "th"} Year')
                    for i in range(1, 5)]

    BRANCH_CHOICES = [
        ('CSE', 'Computer Science & Engineering'),
        ('ECE', 'Electronics & Communication'),
        ('ME', 'Mechanical Engineering'),
        ('CE', 'Civil Engineering'),
        ('EEE', 'Electrical & Electronics Engineering'),
        ('IT', 'Information Technology'),
        ('AIDS', 'AI & Data Science'),
        ('CSBS', 'Computer Science & Business Systems'),
        ('OTHER', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    roll_number = models.CharField(max_length=20, unique=True, blank=True, null=True, default=None)
    branch = models.CharField(max_length=10, choices=BRANCH_CHOICES, default='CSE')
    year = models.IntegerField(choices=YEAR_CHOICES, default=3)
    semester = models.IntegerField(default=5)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    skills = models.TextField(blank=True, help_text='Comma-separated skills')
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    placement_status = models.CharField(
        max_length=20,
        choices=[('not_placed', 'Not Placed'), ('placed', 'Placed'), ('not_eligible', 'Not Eligible')],
        default='not_placed'
    )
    study_streak = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    last_study_date = models.DateField(null=True, blank=True)
    profile_completion = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.branch} Year {self.year}"

    def calculate_profile_completion(self):
        """Calculate and update profile completion percentage."""
        fields = [
            self.roll_number, self.branch, self.cgpa,
            self.skills, self.linkedin_url, self.github_url,
            self.user.profile_picture, self.user.phone, self.user.bio,
        ]
        filled = sum(1 for f in fields if f)
        self.profile_completion = int((filled / len(fields)) * 100)
        self.save()
        return self.profile_completion

    def get_skills_list(self):
        """Return skills as a Python list."""
        return [s.strip() for s in self.skills.split(',') if s.strip()]


class FacultyProfile(models.Model):
    """Extended profile for faculty members."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='faculty_profile')
    employee_id = models.CharField(max_length=20, unique=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    specialization = models.CharField(max_length=200, blank=True)
    experience_years = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Faculty Profile'
        verbose_name_plural = 'Faculty Profiles'

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.designation}"
