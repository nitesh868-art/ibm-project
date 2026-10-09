"""
Custom Authentication Backend supporting Username, Email, and Roll Number with Case-Insensitivity.
Applies to both the main application and Django Admin.
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class MultiIdentifierBackend(ModelBackend):
    """
    Authenticates against username, email, or student roll number.
    Works transparently in both standard views and Django Admin.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        clean_identifier = username.strip()

        # 1. Direct or case-insensitive match on username or email
        user = User.objects.filter(
            Q(username__iexact=clean_identifier) | Q(email__iexact=clean_identifier)
        ).first()

        # 2. Match via StudentProfile roll number
        if not user:
            from accounts.models import StudentProfile
            student = StudentProfile.objects.filter(
                roll_number__iexact=clean_identifier
            ).select_related('user').first()
            if student and student.user:
                user = student.user

        # 3. Verify password
        if user and user.check_password(password):
            return user

        return None
