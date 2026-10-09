"""
Accounts Views — Registration, Login, Logout, OTP, Profile
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from .models import User, StudentProfile, FacultyProfile
from .forms import (StudentRegistrationForm, FacultyRegistrationForm,
                    CustomLoginForm, UserProfileForm, StudentProfileForm,
                    OTPVerificationForm, PasswordResetRequestForm)


def register_student(request):
    """Student registration view with direct login — zero OTP friction."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.is_email_verified = True  # Fully verified immediately
            user.email_otp = ''
            user.save()

            # Create student profile
            roll_number = form.cleaned_data.get('roll_number')
            StudentProfile.objects.get_or_create(
                user=user,
                defaults={
                    'branch': form.cleaned_data.get('branch', 'CSE'),
                    'year': int(form.cleaned_data.get('year', 3)),
                    'roll_number': roll_number or None,
                    'cgpa': form.cleaned_data.get('cgpa') or 0.00,
                }
            )

            # Log the user in directly!
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f'🎉 Welcome to PlacementPro, {user.first_name}! Your account is ready.')
            return redirect('dashboard:home')
        else:
            messages.error(request, 'Please fix the errors highlighted below.')
    else:
        form = StudentRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form, 'role': 'student'})


def register_faculty(request):
    """Faculty registration view with direct login."""
    if request.user.is_authenticated:
        return redirect('dashboard:faculty')

    if request.method == 'POST':
        form = FacultyRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.is_email_verified = True
            user.role = 'faculty'
            user.save()

            FacultyProfile.objects.get_or_create(
                user=user,
                defaults={
                    'department': form.cleaned_data.get('department', ''),
                    'designation': form.cleaned_data.get('designation', ''),
                    'employee_id': form.cleaned_data.get('employee_id', ''),
                }
            )

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f'🎉 Welcome, Professor {user.first_name}! Faculty account created.')
            return redirect('dashboard:faculty')
    else:
        form = FacultyRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form, 'role': 'faculty'})


def verify_otp(request):
    """Bypasses OTP verification and logs in directly if pending, or redirects to dashboard."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    user_id = request.session.get('verify_user_id')
    if user_id:
        try:
            user = User.objects.get(id=user_id)
            user.is_email_verified = True
            user.is_active = True
            user.email_otp = ''
            user.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            if 'verify_user_id' in request.session:
                del request.session['verify_user_id']
            messages.success(request, f'Welcome, {user.first_name}! Logged in successfully.')
            return redirect('dashboard:home')
        except User.DoesNotExist:
            pass

    return redirect('accounts:login')


def resend_otp(request):
    """Redirects to login/dashboard directly."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    return redirect('accounts:login')


def user_login(request):
    """Login view — supports username OR email OR roll number with case-insensitivity."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        login_input = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        remember_me = request.POST.get('remember_me', '') == 'on'

        user = None

        if login_input and password:
            # 1) Direct username match
            user = authenticate(request, username=login_input, password=password)

            # 2) Case-insensitive username match
            if user is None:
                matched_user = User.objects.filter(username__iexact=login_input).first()
                if matched_user:
                    user = authenticate(request, username=matched_user.username, password=password)

            # 3) Case-insensitive email match
            if user is None:
                matched_user = User.objects.filter(email__iexact=login_input).first()
                if matched_user:
                    user = authenticate(request, username=matched_user.username, password=password)

            # 4) Roll number match (via StudentProfile)
            if user is None:
                student_prof = StudentProfile.objects.filter(roll_number__iexact=login_input).select_related('user').first()
                if student_prof and student_prof.user:
                    user = authenticate(request, username=student_prof.user.username, password=password)

        if user is not None:
            if not user.is_active:
                messages.error(request, '❌ Your account is currently disabled. Please contact support.')
            else:
                # Ensure student profile exists
                if user.role == 'student':
                    StudentProfile.objects.get_or_create(user=user)

                login(request, user)
                if not remember_me:
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(1209600)  # 2 weeks

                messages.success(request, f'Welcome back, {user.first_name or user.username}! 👋')
                next_url = request.GET.get('next', '').strip()
                if next_url and not next_url.startswith('/'):
                    next_url = ''

                if not next_url:
                    if user.role == 'admin' or user.is_staff or user.is_superuser:
                        next_url = '/dashboard/admin/'
                    else:
                        next_url = '/dashboard/'
                return redirect(next_url)
        else:
            messages.error(request, '❌ Invalid credentials. Check your username/email/roll number and password, or use 1-click Demo login below.')

        form = CustomLoginForm(request)
    else:
        form = CustomLoginForm(request)

    return render(request, 'accounts/login.html', {'form': form})


def reset_password(request):
    """Direct instant password reset — zero OTP friction."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if not identifier or not new_password:
            messages.error(request, 'Please provide your username or email and a new password.')
            return render(request, 'accounts/reset_password.html')

        if len(new_password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return render(request, 'accounts/reset_password.html', {'identifier': identifier})

        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match. Please try again.')
            return render(request, 'accounts/reset_password.html', {'identifier': identifier})

        user = User.objects.filter(username__iexact=identifier).first() or \
               User.objects.filter(email__iexact=identifier).first()

        if not user:
            student_prof = StudentProfile.objects.filter(roll_number__iexact=identifier).select_related('user').first()
            if student_prof and student_prof.user:
                user = student_prof.user

        if user:
            user.set_password(new_password)
            user.is_active = True
            user.is_email_verified = True
            user.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f'🎉 Password reset successfully! Logged in as {user.first_name or user.username}.')
            return redirect('dashboard:home')
        else:
            messages.error(request, f'No account found matching "{identifier}". Please check or create a new account.')
            return render(request, 'accounts/reset_password.html', {'identifier': identifier})

    return render(request, 'accounts/reset_password.html')



def user_logout(request):
    """Logout view."""
    name = request.user.first_name if request.user.is_authenticated else ''
    logout(request)
    messages.info(request, f'You have been logged out. Goodbye, {name}! 👋')
    return redirect('core:landing')


@login_required
def profile(request):
    """User profile view and edit."""
    user = request.user
    student_profile = None
    faculty_profile = None

    if user.is_student:
        student_profile = getattr(user, 'student_profile', None)
    elif user.is_faculty:
        faculty_profile = getattr(user, 'faculty_profile', None)

    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, request.FILES, instance=user)
        if user_form.is_valid():
            user_form.save()

            # Update student profile if applicable
            if user.is_student and student_profile:
                student_form = StudentProfileForm(request.POST, instance=student_profile)
                if student_form.is_valid():
                    student_form.save()
                    student_profile.calculate_profile_completion()

            messages.success(request, '✅ Profile updated successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please fix the errors.')
    else:
        user_form = UserProfileForm(instance=user)
        student_form = StudentProfileForm(instance=student_profile) if student_profile else None

    context = {
        'user_form': user_form,
        'student_form': student_form,
        'student_profile': student_profile,
        'faculty_profile': faculty_profile,
    }
    return render(request, 'accounts/profile.html', context)


def _send_otp_email(email, name, otp):
    """Helper: Send OTP email to user."""
    subject = '🔑 Your OTP for AI Placement Portal'
    message = f"""
    Dear {name},

    Your One-Time Password (OTP) for email verification is:

    ████  {otp}  ████

    This OTP is valid for 10 minutes only.

    If you did not register, please ignore this email.

    Regards,
    AI Placement Preparation Portal Team
    """
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=True)
    except Exception:
        pass  # Email sending failure should not break registration
