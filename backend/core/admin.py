from django.contrib import admin

from .models import (
    AcademicCalendarEvent,
    AcademicTerm,
    Assignment,
    Course,
    Enrollment,
    AttendanceRecord,
    HostOrganization,
    InternshipEvaluation,
    InternshipPlacement,
    LearningMaterial,
    LogbookEntry,
    Notification,
    Program,
    Submission,
    UserProfile,
    WorkflowRecord,
)


admin.site.register(UserProfile)
admin.site.register(Program)
admin.site.register(AcademicTerm)
admin.site.register(AcademicCalendarEvent)
admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(HostOrganization)
admin.site.register(InternshipPlacement)
admin.site.register(LogbookEntry)
admin.site.register(AttendanceRecord)
admin.site.register(InternshipEvaluation)
admin.site.register(LearningMaterial)
admin.site.register(Assignment)
admin.site.register(Submission)
admin.site.register(Notification)
admin.site.register(WorkflowRecord)
