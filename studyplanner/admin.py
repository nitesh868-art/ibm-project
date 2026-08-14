from django.contrib import admin
from .models import Semester, StudySubject, Topic, StudyPlan, Goal, PomodoroSession, DailyStudyLog

admin.site.register(Semester)
admin.site.register(StudySubject)
admin.site.register(Topic)
admin.site.register(StudyPlan)
admin.site.register(Goal)
admin.site.register(PomodoroSession)
admin.site.register(DailyStudyLog)
