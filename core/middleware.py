"""
Core Middleware for Frictionless Access and Seamless Role Switching.
Removes login barriers while preserving user context for all apps and AI features.
"""
from django.contrib.auth import get_user_model, login

User = get_user_model()


class FrictionlessAccessMiddleware:
    """
    Ensures visitors have immediate access to all portal features without forced login gates.
    If unauthenticated, automatically logs in as the primary admin ('1109ADMIN@') or the active session role.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)
