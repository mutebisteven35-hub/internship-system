from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AcademicCalendarEventViewSet,
    AcademicTermViewSet,
    AssignmentViewSet,
    AttendanceRecordViewSet,
    ChangePasswordView,
    CourseViewSet,
    CurrentUserView,
    DashboardView,
    EnrollmentViewSet,
    HostOrganizationViewSet,
    InternshipEvaluationViewSet,
    InternshipPlacementViewSet,
    LearningMaterialViewSet,
    LoginView,
    LogoutView,
    LogbookEntryViewSet,
    NotificationViewSet,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ProgramViewSet,
    SubmissionViewSet,
    UserViewSet,
    WorkflowRecordViewSet,
)


router = DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("programs", ProgramViewSet, basename="programs")
router.register("terms", AcademicTermViewSet, basename="terms")
router.register("calendar-events", AcademicCalendarEventViewSet, basename="calendar-events")
router.register("courses", CourseViewSet, basename="courses")
router.register("enrollments", EnrollmentViewSet, basename="enrollments")
router.register("host-organizations", HostOrganizationViewSet, basename="host-organizations")
router.register("internship-placements", InternshipPlacementViewSet, basename="internship-placements")
router.register("logbook-entries", LogbookEntryViewSet, basename="logbook-entries")
router.register("attendance-records", AttendanceRecordViewSet, basename="attendance-records")
router.register("internship-evaluations", InternshipEvaluationViewSet, basename="internship-evaluations")
router.register("materials", LearningMaterialViewSet, basename="materials")
router.register("assignments", AssignmentViewSet, basename="assignments")
router.register("submissions", SubmissionViewSet, basename="submissions")
router.register("notifications", NotificationViewSet, basename="notifications")
router.register("workflow-records", WorkflowRecordViewSet, basename="workflow-records")

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("auth/password-reset/request/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("auth/password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("me/", CurrentUserView.as_view(), name="current-user"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("", include(router.urls)),
]
