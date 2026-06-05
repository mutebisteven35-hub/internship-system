from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    AcademicCalendarEvent,
    AcademicTerm,
    Assignment,
    AttendanceRecord,
    Course,
    Enrollment,
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
from .serializers import (
    AcademicCalendarEventSerializer,
    AcademicTermSerializer,
    AssignmentSerializer,
    AttendanceRecordSerializer,
    ChangePasswordSerializer,
    CourseSerializer,
    EnrollmentSerializer,
    GradeSubmissionSerializer,
    HostOrganizationSerializer,
    InternshipEvaluationSerializer,
    InternshipPlacementSerializer,
    LearningMaterialSerializer,
    LogbookEntrySerializer,
    NotificationSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProgramSerializer,
    RegistrationSerializer,
    ReviewLogbookSerializer,
    SubmissionSerializer,
    UserAdminSerializer,
    UserSummarySerializer,
    WorkflowRecordSerializer,
)


User = get_user_model()


def role_for(user):
    if user.is_superuser:
        return UserProfile.ROLE_ADMIN
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile.role


def is_admin(user):
    return role_for(user) == UserProfile.ROLE_ADMIN


def is_instructor(user):
    return role_for(user) == UserProfile.ROLE_INSTRUCTOR


def is_student(user):
    return role_for(user) == UserProfile.ROLE_STUDENT


def audit(actor, action, target, details=None):
    WorkflowRecord.objects.create(
        actor=actor if actor and actor.is_authenticated else None,
        action=action,
        target_type=target.__class__.__name__,
        target_id=str(getattr(target, "id", "")),
        details=details or {},
    )


def find_user_by_identifier(identifier):
    return (
        User.objects.select_related("profile")
        .filter(Q(username__iexact=identifier) | Q(email__iexact=identifier))
        .order_by("id")
        .first()
    )


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and is_admin(request.user)


class AdminWriteAuthenticatedRead(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and is_admin(request.user)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        username = request.data.get("username", "")
        password = request.data.get("password", "")
        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({"detail": "Invalid username or password."}, status=status.HTTP_400_BAD_REQUEST)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": UserSummarySerializer(user).data})


class RegistrationView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        audit(None, "auth.registered", user)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": UserSummarySerializer(user).data}, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        Token.objects.filter(user=request.user).delete()
        audit(request.user, "password.changed", request.user)
        return Response({"detail": "Password changed. Please sign in again."})


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data["identifier"].strip()
        user = find_user_by_identifier(identifier)
        if not user:
            return Response({"detail": "No account was found for that username or email."}, status=404)
        reset_code = default_token_generator.make_token(user)
        audit(None, "password.reset_requested", user)
        return Response(
            {
                "detail": "Use this reset code to set a new password.",
                "identifier": user.username,
                "reset_code": reset_code,
            }
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = find_user_by_identifier(data["identifier"].strip())
        if not user or not default_token_generator.check_token(user, data["reset_code"]):
            return Response({"detail": "The reset code is invalid or expired."}, status=400)
        try:
            validate_password(data["new_password"], user)
        except DjangoValidationError as exc:
            return Response({"new_password": list(exc.messages)}, status=400)
        user.set_password(data["new_password"])
        user.save(update_fields=["password"])
        Token.objects.filter(user=user).delete()
        audit(None, "password.reset_confirmed", user)
        return Response({"detail": "Password reset. Please sign in with the new password."})


class CurrentUserView(APIView):
    def get(self, request):
        return Response(UserSummarySerializer(request.user).data)


class DashboardView(APIView):
    def get(self, request):
        role = role_for(request.user)
        if is_admin(request.user):
            data = {
                "courses": Course.objects.count(),
                "students": UserProfile.objects.filter(role=UserProfile.ROLE_STUDENT).count(),
                "instructors": UserProfile.objects.filter(role=UserProfile.ROLE_INSTRUCTOR).count(),
                "host_organizations": HostOrganization.objects.count(),
                "active_placements": InternshipPlacement.objects.filter(status=InternshipPlacement.STATUS_ACTIVE).count(),
                "submitted_logbooks": LogbookEntry.objects.filter(status=LogbookEntry.STATUS_SUBMITTED).count(),
                "pending_registrations": Enrollment.objects.filter(status=Enrollment.STATUS_PENDING).count(),
                "workflow_records": WorkflowRecord.objects.count(),
            }
        elif is_instructor(request.user):
            courses = Course.objects.filter(instructor=request.user)
            placements = InternshipPlacement.objects.filter(instructor=request.user)
            data = {
                "courses": courses.count(),
                "active_placements": placements.filter(status=InternshipPlacement.STATUS_ACTIVE).count(),
                "submitted_logbooks": LogbookEntry.objects.filter(
                    placement__in=placements, status=LogbookEntry.STATUS_SUBMITTED
                ).count(),
                "evaluations": InternshipEvaluation.objects.filter(placement__in=placements).count(),
                "pending_registrations": Enrollment.objects.filter(
                    course__in=courses, status=Enrollment.STATUS_PENDING
                ).count(),
                "assignments": Assignment.objects.filter(course__in=courses).count(),
                "submissions": Submission.objects.filter(assignment__course__in=courses).count(),
                "unread_notifications": Notification.objects.filter(recipient=request.user, is_read=False).count(),
            }
        else:
            placements = InternshipPlacement.objects.filter(student=request.user)
            data = {
                "active_placements": placements.filter(status=InternshipPlacement.STATUS_ACTIVE).count(),
                "logbook_entries": LogbookEntry.objects.filter(placement__in=placements).count(),
                "evaluations": InternshipEvaluation.objects.filter(placement__in=placements).count(),
                "enrolled_courses": Enrollment.objects.filter(
                    student=request.user, status=Enrollment.STATUS_APPROVED
                ).count(),
                "pending_registrations": Enrollment.objects.filter(
                    student=request.user, status=Enrollment.STATUS_PENDING
                ).count(),
                "assignments": Assignment.objects.filter(
                    course__enrollments__student=request.user,
                    course__enrollments__status=Enrollment.STATUS_APPROVED,
                ).distinct().count(),
                "submissions": Submission.objects.filter(student=request.user).count(),
                "unread_notifications": Notification.objects.filter(recipient=request.user, is_read=False).count(),
            }
        data["role"] = role
        return Response(data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related("profile").order_by("username")
    serializer_class = UserAdminSerializer
    permission_classes = [IsAdmin]

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def instructors(self, request):
        users = self.queryset.filter(profile__role=UserProfile.ROLE_INSTRUCTOR)
        return Response(UserSummarySerializer(users, many=True).data)


class ProgramViewSet(viewsets.ModelViewSet):
    queryset = Program.objects.all().order_by("code")
    serializer_class = ProgramSerializer
    permission_classes = [AdminWriteAuthenticatedRead]


class AcademicTermViewSet(viewsets.ModelViewSet):
    queryset = AcademicTerm.objects.all()
    serializer_class = AcademicTermSerializer
    permission_classes = [AdminWriteAuthenticatedRead]


class AcademicCalendarEventViewSet(viewsets.ModelViewSet):
    queryset = AcademicCalendarEvent.objects.select_related("term").all()
    serializer_class = AcademicCalendarEventSerializer
    permission_classes = [AdminWriteAuthenticatedRead]


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer

    def get_queryset(self):
        queryset = Course.objects.select_related("program", "term", "instructor").annotate(
            enrollment_count=Count("enrollments", filter=Q(enrollments__status=Enrollment.STATUS_APPROVED))
        )
        if is_admin(self.request.user):
            return queryset
        if is_instructor(self.request.user):
            return queryset.filter(Q(status=Course.STATUS_ACTIVE) | Q(instructor=self.request.user)).distinct()
        return queryset.filter(status=Course.STATUS_ACTIVE)

    def perform_create(self, serializer):
        instructor = serializer.validated_data.get("instructor")
        if is_instructor(self.request.user) and instructor != self.request.user:
            serializer.validated_data["instructor"] = self.request.user
        course = serializer.save()
        audit(self.request.user, "course.created", course)

    def check_write_allowed(self, course=None):
        if is_admin(self.request.user):
            return True
        return is_instructor(self.request.user) and (course is None or course.instructor_id == self.request.user.id)

    def create(self, request, *args, **kwargs):
        if not self.check_write_allowed():
            return Response({"detail": "Only admins and instructors can create courses."}, status=403)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not self.check_write_allowed(self.get_object()):
            return Response({"detail": "You cannot update this course."}, status=403)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not self.check_write_allowed(self.get_object()):
            return Response({"detail": "You cannot update this course."}, status=403)
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def register(self, request, pk=None):
        if not is_student(request.user):
            return Response({"detail": "Only student accounts can register for courses."}, status=403)
        course = self.get_object()
        enrollment, created = Enrollment.objects.get_or_create(student=request.user, course=course)
        if created:
            audit(request.user, "enrollment.requested", enrollment)
            Notification.objects.create(
                recipient=course.instructor,
                title=f"New registration for {course.code}",
                message=f"{request.user.username} requested registration in {course.title}.",
                kind=Notification.KIND_REGISTRATION,
            )
        return Response(EnrollmentSerializer(enrollment, context={"request": request}).data)


class EnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = EnrollmentSerializer

    def get_queryset(self):
        queryset = Enrollment.objects.select_related("student", "student__profile", "course", "course__instructor")
        if is_admin(self.request.user):
            return queryset
        if is_instructor(self.request.user):
            return queryset.filter(course__instructor=self.request.user)
        return queryset.filter(student=self.request.user)

    def perform_create(self, serializer):
        student = self.request.user if is_student(self.request.user) else serializer.validated_data["student"]
        enrollment = serializer.save(student=student)
        audit(self.request.user, "enrollment.created", enrollment)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        enrollment = self.get_object()
        if not (is_admin(request.user) or enrollment.course.instructor_id == request.user.id):
            return Response({"detail": "You cannot approve this enrollment."}, status=403)
        enrollment.approve()
        audit(request.user, "enrollment.approved", enrollment)
        Notification.objects.create(
            recipient=enrollment.student,
            title=f"Registration approved: {enrollment.course.code}",
            message=f"Your registration in {enrollment.course.title} has been approved.",
            kind=Notification.KIND_REGISTRATION,
        )
        return Response(self.get_serializer(enrollment).data)


class HostOrganizationViewSet(viewsets.ModelViewSet):
    queryset = HostOrganization.objects.all()
    serializer_class = HostOrganizationSerializer
    permission_classes = [AdminWriteAuthenticatedRead]

    def perform_create(self, serializer):
        organization = serializer.save()
        audit(self.request.user, "host_organization.created", organization)


class InternshipPlacementViewSet(viewsets.ModelViewSet):
    serializer_class = InternshipPlacementSerializer

    def get_queryset(self):
        queryset = InternshipPlacement.objects.select_related(
            "student",
            "student__profile",
            "instructor",
            "instructor__profile",
            "host_organization",
            "program",
            "term",
        ).annotate(
            logbook_count=Count("logbook_entries", distinct=True),
            evaluation_count=Count("evaluations", distinct=True),
        )
        if is_admin(self.request.user):
            return queryset
        if is_instructor(self.request.user):
            return queryset.filter(instructor=self.request.user)
        return queryset.filter(student=self.request.user)

    def create(self, request, *args, **kwargs):
        if not is_admin(request.user):
            return Response({"detail": "Only admins can create internship placements."}, status=403)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        placement = serializer.save()
        audit(self.request.user, "internship_placement.created", placement)
        Notification.objects.create(
            recipient=placement.student,
            title="Internship placement assigned",
            message=f"You have been assigned to {placement.host_organization.name} as {placement.position_title}.",
            kind=Notification.KIND_INFO,
        )
        Notification.objects.create(
            recipient=placement.instructor,
            title="Student placement assigned",
            message=f"{placement.student.username} has been placed at {placement.host_organization.name}.",
            kind=Notification.KIND_INFO,
        )


class LogbookEntryViewSet(viewsets.ModelViewSet):
    serializer_class = LogbookEntrySerializer

    def get_queryset(self):
        queryset = LogbookEntry.objects.select_related(
            "placement",
            "placement__host_organization",
            "placement__student",
            "placement__student__profile",
            "placement__instructor",
            "placement__instructor__profile",
            "placement__program",
            "placement__term",
            "student",
            "student__profile",
            "reviewed_by",
            "reviewed_by__profile",
        )
        if is_admin(self.request.user):
            return queryset
        if is_instructor(self.request.user):
            return queryset.filter(placement__instructor=self.request.user)
        return queryset.filter(student=self.request.user)

    def create(self, request, *args, **kwargs):
        placement_id = request.data.get("placement")
        if is_student(request.user):
            allowed = InternshipPlacement.objects.filter(id=placement_id, student=request.user).exists()
        elif is_instructor(request.user):
            allowed = InternshipPlacement.objects.filter(id=placement_id, instructor=request.user).exists()
        else:
            allowed = True
        if not allowed:
            return Response({"detail": "You cannot create a logbook entry for this placement."}, status=403)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        placement = serializer.validated_data["placement"]
        student = placement.student if not is_student(self.request.user) else self.request.user
        entry = serializer.save(student=student)
        audit(self.request.user, "logbook.created", entry)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        entry = self.get_object()
        if entry.student_id != request.user.id and not is_admin(request.user):
            return Response({"detail": "You cannot submit this logbook entry."}, status=403)
        entry.status = LogbookEntry.STATUS_SUBMITTED
        entry.submitted_at = timezone.now()
        entry.save(update_fields=["status", "submitted_at"])
        audit(request.user, "logbook.submitted", entry)
        Notification.objects.create(
            recipient=entry.placement.instructor,
            title="Logbook submitted",
            message=f"{entry.student.username} submitted a logbook entry for {entry.entry_date}.",
            kind=Notification.KIND_INFO,
        )
        return Response(self.get_serializer(entry).data)

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        entry = self.get_object()
        if not (is_admin(request.user) or entry.placement.instructor_id == request.user.id):
            return Response({"detail": "You cannot review this logbook entry."}, status=403)
        serializer = ReviewLogbookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry.instructor_feedback = serializer.validated_data.get("instructor_feedback", "")
        entry.status = LogbookEntry.STATUS_REVIEWED
        entry.reviewed_by = request.user
        entry.reviewed_at = timezone.now()
        entry.save(update_fields=["instructor_feedback", "status", "reviewed_by", "reviewed_at"])
        audit(request.user, "logbook.reviewed", entry)
        Notification.objects.create(
            recipient=entry.student,
            title="Logbook reviewed",
            message=f"Your logbook entry for {entry.entry_date} has been reviewed.",
            kind=Notification.KIND_INFO,
        )
        return Response(self.get_serializer(entry).data)


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceRecordSerializer

    def get_queryset(self):
        queryset = AttendanceRecord.objects.select_related("placement", "placement__host_organization", "student", "student__profile")
        if is_admin(self.request.user):
            return queryset
        if is_instructor(self.request.user):
            return queryset.filter(placement__instructor=self.request.user)
        return queryset.filter(student=self.request.user)

    def create(self, request, *args, **kwargs):
        placement_id = request.data.get("placement")
        allowed = is_admin(request.user) or InternshipPlacement.objects.filter(
            id=placement_id,
            student=request.user if is_student(request.user) else None,
        ).exists()
        if is_instructor(request.user):
            allowed = InternshipPlacement.objects.filter(id=placement_id, instructor=request.user).exists()
        if not allowed:
            return Response({"detail": "You cannot add attendance for this placement."}, status=403)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        placement = serializer.validated_data["placement"]
        record = serializer.save(student=placement.student)
        audit(self.request.user, "attendance.created", record)


class InternshipEvaluationViewSet(viewsets.ModelViewSet):
    serializer_class = InternshipEvaluationSerializer

    def get_queryset(self):
        queryset = InternshipEvaluation.objects.select_related(
            "placement",
            "placement__host_organization",
            "placement__student",
            "placement__student__profile",
            "placement__instructor",
            "placement__instructor__profile",
            "evaluator",
            "evaluator__profile",
        )
        if is_admin(self.request.user):
            return queryset
        if is_instructor(self.request.user):
            return queryset.filter(placement__instructor=self.request.user)
        return queryset.filter(placement__student=self.request.user)

    def create(self, request, *args, **kwargs):
        placement_id = request.data.get("placement")
        allowed = is_admin(request.user) or InternshipPlacement.objects.filter(
            id=placement_id, instructor=request.user
        ).exists()
        if not allowed:
            return Response({"detail": "Only admins and assigned instructors can create evaluations."}, status=403)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        evaluation = serializer.save(evaluator=self.request.user)
        audit(self.request.user, "internship_evaluation.created", evaluation)
        Notification.objects.create(
            recipient=evaluation.placement.student,
            title="Internship evaluation posted",
            message=f"An evaluation has been posted for your placement at {evaluation.placement.host_organization.name}.",
            kind=Notification.KIND_GRADE,
        )

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        enrollment = self.get_object()
        if not (is_admin(request.user) or enrollment.course.instructor_id == request.user.id):
            return Response({"detail": "You cannot reject this enrollment."}, status=403)
        enrollment.reject()
        audit(request.user, "enrollment.rejected", enrollment)
        return Response(self.get_serializer(enrollment).data)


class LearningMaterialViewSet(viewsets.ModelViewSet):
    serializer_class = LearningMaterialSerializer

    def get_queryset(self):
        queryset = LearningMaterial.objects.select_related("course", "uploaded_by", "uploaded_by__profile")
        if is_admin(self.request.user):
            return queryset
        if is_instructor(self.request.user):
            return queryset.filter(course__instructor=self.request.user)
        return queryset.filter(
            course__enrollments__student=self.request.user,
            course__enrollments__status=Enrollment.STATUS_APPROVED,
        ).distinct()

    def perform_create(self, serializer):
        material = serializer.save(uploaded_by=self.request.user)
        audit(self.request.user, "material.created", material)

    def create(self, request, *args, **kwargs):
        course_id = request.data.get("course")
        allowed = is_admin(request.user) or Course.objects.filter(id=course_id, instructor=request.user).exists()
        if not allowed:
            return Response({"detail": "You cannot add material to this course."}, status=403)
        return super().create(request, *args, **kwargs)


class AssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssignmentSerializer

    def get_queryset(self):
        queryset = Assignment.objects.select_related("course", "course__instructor", "created_by", "created_by__profile")
        if is_admin(self.request.user):
            return queryset
        if is_instructor(self.request.user):
            return queryset.filter(course__instructor=self.request.user)
        return queryset.filter(
            course__enrollments__student=self.request.user,
            course__enrollments__status=Enrollment.STATUS_APPROVED,
        ).distinct()

    def perform_create(self, serializer):
        assignment = serializer.save(created_by=self.request.user)
        audit(self.request.user, "assignment.created", assignment)

    def create(self, request, *args, **kwargs):
        course_id = request.data.get("course")
        allowed = is_admin(request.user) or Course.objects.filter(id=course_id, instructor=request.user).exists()
        if not allowed:
            return Response({"detail": "You cannot create assignments for this course."}, status=403)
        return super().create(request, *args, **kwargs)


class SubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = SubmissionSerializer

    def get_queryset(self):
        queryset = Submission.objects.select_related(
            "assignment",
            "assignment__course",
            "assignment__course__instructor",
            "student",
            "student__profile",
        )
        if is_admin(self.request.user):
            return queryset
        if is_instructor(self.request.user):
            return queryset.filter(assignment__course__instructor=self.request.user)
        return queryset.filter(student=self.request.user)

    def perform_create(self, serializer):
        submission = serializer.save(student=self.request.user)
        audit(self.request.user, "submission.created", submission)
        Notification.objects.create(
            recipient=submission.assignment.course.instructor,
            title=f"Submission received: {submission.assignment.title}",
            message=f"{self.request.user.username} submitted work for {submission.assignment.title}.",
            kind=Notification.KIND_ASSIGNMENT,
        )

    def create(self, request, *args, **kwargs):
        if not is_student(request.user):
            return Response({"detail": "Only students can submit assignments."}, status=403)
        assignment_id = request.data.get("assignment")
        enrolled = Enrollment.objects.filter(
            student=request.user,
            course__assignments__id=assignment_id,
            status=Enrollment.STATUS_APPROVED,
        ).exists()
        if not enrolled:
            return Response({"detail": "You must be approved in the course before submitting."}, status=403)
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def grade(self, request, pk=None):
        submission = self.get_object()
        if not (is_admin(request.user) or submission.assignment.course.instructor_id == request.user.id):
            return Response({"detail": "You cannot grade this submission."}, status=403)
        serializer = GradeSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission.score = serializer.validated_data["score"]
        submission.feedback = serializer.validated_data.get("feedback", "")
        submission.status = Submission.STATUS_GRADED
        submission.graded_at = timezone.now()
        submission.save(update_fields=["score", "feedback", "status", "graded_at"])
        audit(request.user, "submission.graded", submission, {"score": str(submission.score)})
        Notification.objects.create(
            recipient=submission.student,
            title=f"Grade posted: {submission.assignment.title}",
            message=f"Your grade is {submission.score}/{submission.assignment.max_score}.",
            kind=Notification.KIND_GRADE,
        )
        return Response(self.get_serializer(submission).data)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        queryset = Notification.objects.select_related("recipient", "recipient__profile")
        if is_admin(self.request.user):
            return queryset
        return queryset.filter(recipient=self.request.user)

    def create(self, request, *args, **kwargs):
        if not is_admin(request.user):
            return Response({"detail": "Only admins can create broadcast notifications."}, status=403)
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        if notification.recipient_id != request.user.id and not is_admin(request.user):
            return Response({"detail": "You cannot update this notification."}, status=403)
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(self.get_serializer(notification).data)


class WorkflowRecordViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = WorkflowRecordSerializer

    def get_queryset(self):
        queryset = WorkflowRecord.objects.select_related("actor", "actor__profile")
        if is_admin(self.request.user):
            return queryset
        return queryset.filter(actor=self.request.user)
