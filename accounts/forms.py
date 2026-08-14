"""
Accounts Forms — Registration, Login, Profile Update
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML
from .models import User, StudentProfile, FacultyProfile


class StudentRegistrationForm(UserCreationForm):
    """Student Registration Form with all required fields."""

    first_name = forms.CharField(max_length=50, required=True,
                                  widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=50, required=True,
                                 widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    email = forms.EmailField(required=True,
                              widget=forms.EmailInput(attrs={'placeholder': 'Email Address'}))
    phone = forms.CharField(max_length=15, required=False,
                             widget=forms.TextInput(attrs={'placeholder': 'Phone Number'}))
    branch = forms.ChoiceField(choices=StudentProfile.BRANCH_CHOICES)
    year = forms.ChoiceField(choices=StudentProfile.YEAR_CHOICES)
    roll_number = forms.CharField(max_length=20, required=False,
                                   widget=forms.TextInput(attrs={'placeholder': 'Roll Number'}))
    cgpa = forms.DecimalField(max_digits=4, decimal_places=2, required=False,
                               widget=forms.NumberInput(attrs={'placeholder': 'CGPA (e.g. 8.5)', 'step': '0.01'}))
    terms_accepted = forms.BooleanField(required=True, label='I accept the Terms & Conditions')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('first_name', css_class='col-md-6'), Column('last_name', css_class='col-md-6')),
            'username', 'email', 'phone',
            Row(Column('branch', css_class='col-md-6'), Column('year', css_class='col-md-6')),
            Row(Column('roll_number', css_class='col-md-6'), Column('cgpa', css_class='col-md-6')),
            'password1', 'password2',
            'terms_accepted',
            Submit('submit', 'Create Account', css_class='btn btn-primary w-100 mt-3'),
        )
        # Add Bootstrap classes
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})

    def clean_roll_number(self):
        """Validate that roll number is unique if provided."""
        roll_number = self.cleaned_data.get('roll_number', '').strip()
        if not roll_number:
            return None  # Store as NULL, not empty string
        # Check uniqueness
        from .models import StudentProfile
        if StudentProfile.objects.filter(roll_number=roll_number).exists():
            raise forms.ValidationError(
                f'A student with roll number "{roll_number}" is already registered. '
                'Please check your roll number or contact your administrator.'
            )
        return roll_number

    def clean_email(self):
        """Validate that email is unique."""
        email = self.cleaned_data.get('email', '').strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                'This email address is already registered. Please use a different email or sign in.'
            )
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'
        user.phone = self.cleaned_data.get('phone', '')
        if commit:
            user.save()
            # NOTE: StudentProfile is created in the VIEW via get_or_create
            # Do NOT create it here to avoid IntegrityError on duplicate calls
        return user



class FacultyRegistrationForm(UserCreationForm):
    """Faculty Registration Form."""

    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)
    department = forms.CharField(max_length=100, required=False)
    designation = forms.CharField(max_length=100, required=False)
    employee_id = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'faculty'
        if commit:
            user.save()
            FacultyProfile.objects.create(
                user=user,
                department=self.cleaned_data.get('department', ''),
                designation=self.cleaned_data.get('designation', ''),
                employee_id=self.cleaned_data.get('employee_id', ''),
            )
        return user


class CustomLoginForm(AuthenticationForm):
    """Custom login form with Bootstrap styling."""
    remember_me = forms.BooleanField(required=False, label='Remember Me')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Username or Email'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Password'
        })


class UserProfileForm(forms.ModelForm):
    """Form to update basic user profile."""

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'bio', 'profile_picture')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control'})


class StudentProfileForm(forms.ModelForm):
    """Form to update student-specific profile."""

    class Meta:
        model = StudentProfile
        fields = ('roll_number', 'branch', 'year', 'semester', 'cgpa',
                  'skills', 'linkedin_url', 'github_url')
        widgets = {
            'skills': forms.TextInput(attrs={'placeholder': 'Python, Django, React, SQL...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class OTPVerificationForm(forms.Form):
    """OTP verification form."""
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center fs-3 letter-spacing-wide',
            'placeholder': '------',
            'maxlength': '6',
        }),
        label='Enter OTP'
    )


class PasswordResetRequestForm(forms.Form):
    """Form to request password reset via email."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your registered email'
        })
    )
