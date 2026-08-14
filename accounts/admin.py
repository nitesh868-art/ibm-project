"""
Accounts Admin Registration
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, StudentProfile, FacultyProfile


class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = 'Student Profile'


class FacultyProfileInline(admin.StackedInline):
    model = FacultyProfile
    can_delete = False
    verbose_name_plural = 'Faculty Profile'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_email_verified', 'is_active')
    list_filter = ('role', 'is_email_verified', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'profile_picture', 'phone', 'bio', 'is_email_verified')}),
    )

    def get_inlines(self, request, obj=None):
        if obj:
            if obj.role == 'student':
                return [StudentProfileInline]
            elif obj.role == 'faculty':
                return [FacultyProfileInline]
        return []


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'roll_number', 'branch', 'year', 'cgpa', 'placement_status', 'study_streak')
    list_filter = ('branch', 'year', 'placement_status')
    search_fields = ('user__username', 'user__email', 'roll_number')


@admin.register(FacultyProfile)
class FacultyProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'department', 'designation')
    search_fields = ('user__username', 'employee_id')
