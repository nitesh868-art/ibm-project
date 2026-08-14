from django.contrib import admin
from .models import Subject, Question, MockTest, TestAttempt, QuestionAnswer, Bookmark

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category')
    search_fields = ('name', 'code')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'subject', 'difficulty', 'language', 'is_active')
    list_filter = ('subject', 'difficulty', 'language', 'is_active')
    search_fields = ('question_text',)

@admin.register(MockTest)
class MockTestAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'test_type', 'duration_minutes', 'passing_marks', 'is_active', 'is_published')
    list_filter = ('test_type', 'is_active', 'is_published', 'subject')
    search_fields = ('title',)

@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'test', 'score', 'percentage', 'is_completed', 'started_at')
    list_filter = ('is_completed',)

admin.site.register(QuestionAnswer)
admin.site.register(Bookmark)
