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
    """Student registration view with OTP email verification."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True  # Active; email verification is optional flow
            user.save()

            # Create student profile ONCE — here, using get_or_create to be safe
            roll_number = form.cleaned_data.get('roll_number')  # None if blank
            StudentProfile.objects.get_or_create(
                user=user,
                defaults={
                    'branch': form.cleaned_data.get('branch', 'CSE'),
                    'year': int(form.cleaned_data.get('year', 3)),
                    'roll_number': roll_number or None,
                    'cgpa': form.cleaned_data.get('cgpa') or 0.00,
                }
            )

            # Generate and send OTP (non-blocking)
            otp = user.generate_otp()
            _send_otp_email(user.email, user.first_name, otp)

            # Store user ID in session for OTP verification
            request.session['verify_user_id'] = user.id

            messages.success(request, f'✅ Account created! We sent a 6-digit OTP to {user.email}. '
                                       f'(If email is not configured, you can still log in directly.)')
            return redirect('accounts:verify_otp')
        else:
            # Show a top-level error summary
            messages.error(request, 'Please fix the errors highlighted below.')
    else:
        form = StudentRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form, 'role': 'student'})



def register_faculty(request):
    """Faculty registration view."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = FacultyRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            otp = user.generate_otp()
            _send_otp_email(user.email, user.first_name, otp)
            request.session['verify_user_id'] = user.id
            messages.success(request, f'Faculty account created! OTP sent to {user.email}')
            return redirect('accounts:verify_otp')
    else:
        form = FacultyRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form, 'role': 'faculty'})


def verify_otp(request):
    """Email OTP verification view."""
    user_id = request.session.get('verify_user_id')
    if not user_id:
        return redirect('accounts:login')

    user = get_object_or_404(User, id=user_id)

    # Allow skipping OTP in development / when email not configured
    if request.GET.get('skip') == '1':
        user.is_email_verified = True
        user.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        if 'verify_user_id' in request.session:
            del request.session['verify_user_id']
        messages.info(request, '👋 Welcome! Email verification skipped (development mode).')
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            if user.is_otp_valid(otp):
                user.is_email_verified = True
                user.email_otp = ''
                user.save()
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                del request.session['verify_user_id']
                messages.success(request, '✅ Email verified successfully! Welcome aboard!')
                return redirect('dashboard:home')
            else:
                messages.error(request, '❌ Invalid or expired OTP. Please try again.')
    else:
        form = OTPVerificationForm()

    return render(request, 'accounts/verify_otp.html', {'form': form, 'email': user.email})


def resend_otp(request):
    """Resend OTP to user's email."""
    user_id = request.session.get('verify_user_id')
    if not user_id:
        return redirect('accounts:login')

    user = get_object_or_404(User, id=user_id)
    otp = user.generate_otp()
    _send_otp_email(user.email, user.first_name, otp)
    messages.success(request, f'New OTP sent to {user.email}')
    return redirect('accounts:verify_otp')


def user_login(request):
    """Login view with remember me functionality."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me')

            user = authenticate(request, username=username, password=password)
            if user:
                # Ensure student profile exists (safety net)
                if user.role == 'student':
                    StudentProfile.objects.get_or_create(user=user)

                login(request, user)
                # Set session expiry based on remember_me
                if not remember_me:
                    request.session.set_expiry(0)  # Browser close
                else:
                    request.session.set_expiry(1209600)  # 2 weeks

                messages.success(request, f'Welcome back, {user.first_name or user.username}! 👋')
                next_url = request.GET.get('next', '')
                if next_url and not next_url.startswith('/'):
                    # Safety: ignore non-path next values
                    next_url = ''
                return redirect(next_url or 'dashboard:home')
            else:
                messages.error(request, '❌ Invalid username or password. Please try again.')
        else:
            messages.error(request, 'Please check your credentials.')
    else:
        form = CustomLoginForm(request)

    return render(request, 'accounts/login.html', {'form': form})



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
