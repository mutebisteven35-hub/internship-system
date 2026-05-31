from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

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


User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["role", "department", "student_number"]


class UserSummarySerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "display_name", "role"]

    def get_role(self, obj):
        if obj.is_superuser:
            return UserProfile.ROLE_ADMIN
        profile = getattr(obj, "profile", None)
        return profile.role if profile else UserProfile.ROLE_STUDENT

    def get_display_name(self, obj):
        full_name = obj.get_full_name().strip()
        return full_name or obj.username


class UserAdminSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False)
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "password",
            "profile",
        ]

    def create(self, validated_data):
        profile_data = validated_data.pop("profile", {})
        password = validated_data.pop("password", None) or "Passw0rd!"
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        UserProfile.objects.update_or_create(user=user, defaults=profile_data)
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", None)
        password = validated_data.pop("password", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if password:
            instance.set_password(password)
        instance.save()
        if profile_data is not None:
            UserProfile.objects.update_or_create(user=instance, defaults=profile_data)
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError({"current_password": "Current password is incorrect."})
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        validate_password(attrs["new_password"], user)
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    reset_code = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs


class ProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = Program
        fields = ["id", "code", "name", "description"]


class AcademicTermSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicTerm
        fields = ["id", "name", "start_date", "end_date", "is_active"]


class AcademicCalendarEventSerializer(serializers.ModelSerializer):
    term_detail = AcademicTermSerializer(source="term", read_only=True)

    class Meta:
        model = AcademicCalendarEvent
        fields = ["id", "title", "term", "term_detail", "event_type", "starts_on", "ends_on", "notes"]


class CourseSerializer(serializers.ModelSerializer):
    program_detail = ProgramSerializer(source="program", read_only=True)
    term_detail = AcademicTermSerializer(source="term", read_only=True)
    instructor_detail = UserSummarySerializer(source="instructor", read_only=True)
    enrollment_status = serializers.SerializerMethodField()
    enrollment_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "code",
            "title",
            "description",
            "program",
            "program_detail",
            "term",
            "term_detail",
            "instructor",
            "instructor_detail",
            "capacity",
            "status",
            "created_at",
            "enrollment_status",
            "enrollment_count",
        ]
        extra_kwargs = {"instructor": {"required": False}}

    def get_enrollment_status(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        enrollment = obj.enrollments.filter(student=request.user).first()
        return enrollment.status if enrollment else None


class EnrollmentSerializer(serializers.ModelSerializer):
    student_detail = UserSummarySerializer(source="student", read_only=True)
    course_detail = CourseSerializer(source="course", read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "student",
            "student_detail",
            "course",
            "course_detail",
            "status",
            "registered_at",
            "decided_at",
        ]
        read_only_fields = ["status", "registered_at", "decided_at"]


class HostOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostOrganization
        fields = [
            "id",
            "name",
            "organization_type",
            "sector",
            "address",
            "contact_person",
            "contact_email",
            "contact_phone",
            "website",
            "notes",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class InternshipPlacementSerializer(serializers.ModelSerializer):
    student_detail = UserSummarySerializer(source="student", read_only=True)
    instructor_detail = UserSummarySerializer(source="instructor", read_only=True)
    host_organization_detail = HostOrganizationSerializer(source="host_organization", read_only=True)
    program_detail = ProgramSerializer(source="program", read_only=True)
    term_detail = AcademicTermSerializer(source="term", read_only=True)
    logbook_count = serializers.IntegerField(read_only=True)
    evaluation_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = InternshipPlacement
        fields = [
            "id",
            "student",
            "student_detail",
            "instructor",
            "instructor_detail",
            "host_organization",
            "host_organization_detail",
            "program",
            "program_detail",
            "term",
            "term_detail",
            "position_title",
            "department",
            "start_date",
            "end_date",
            "status",
            "workplace_supervisor_name",
            "workplace_supervisor_email",
            "workplace_supervisor_phone",
            "learning_objectives",
            "created_at",
            "logbook_count",
            "evaluation_count",
        ]
        read_only_fields = ["created_at"]


class LogbookEntrySerializer(serializers.ModelSerializer):
    placement_detail = InternshipPlacementSerializer(source="placement", read_only=True)
    student_detail = UserSummarySerializer(source="student", read_only=True)
    reviewed_by_detail = UserSummarySerializer(source="reviewed_by", read_only=True)

    class Meta:
        model = LogbookEntry
        fields = [
            "id",
            "placement",
            "placement_detail",
            "student",
            "student_detail",
            "entry_date",
            "hours_worked",
            "activities",
            "skills_learned",
            "challenges",
            "next_plan",
            "status",
            "instructor_feedback",
            "reviewed_by",
            "reviewed_by_detail",
            "submitted_at",
            "reviewed_at",
            "created_at",
        ]
        read_only_fields = [
            "student",
            "status",
            "instructor_feedback",
            "reviewed_by",
            "submitted_at",
            "reviewed_at",
            "created_at",
        ]
        validators = []

    def validate(self, attrs):
        placement = attrs.get("placement") or getattr(self.instance, "placement", None)
        entry_date = attrs.get("entry_date") or getattr(self.instance, "entry_date", None)
        queryset = LogbookEntry.objects.filter(placement=placement, entry_date=entry_date)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if placement and entry_date and queryset.exists():
            raise serializers.ValidationError(
                {"entry_date": "A logbook entry already exists for this placement and date."}
            )
        return attrs


class ReviewLogbookSerializer(serializers.Serializer):
    instructor_feedback = serializers.CharField(required=False, allow_blank=True)


class AttendanceRecordSerializer(serializers.ModelSerializer):
    placement_detail = InternshipPlacementSerializer(source="placement", read_only=True)
    student_detail = UserSummarySerializer(source="student", read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = [
            "id",
            "placement",
            "placement_detail",
            "student",
            "student_detail",
            "date",
            "status",
            "check_in",
            "check_out",
            "notes",
            "created_at",
        ]
        read_only_fields = ["student", "created_at"]
        validators = []

    def validate(self, attrs):
        placement = attrs.get("placement") or getattr(self.instance, "placement", None)
        date = attrs.get("date") or getattr(self.instance, "date", None)
        queryset = AttendanceRecord.objects.filter(placement=placement, date=date)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if placement and date and queryset.exists():
            raise serializers.ValidationError(
                {"date": "An attendance record already exists for this placement and date."}
            )
        return attrs


class InternshipEvaluationSerializer(serializers.ModelSerializer):
    placement_detail = InternshipPlacementSerializer(source="placement", read_only=True)
    evaluator_detail = UserSummarySerializer(source="evaluator", read_only=True)
    total_score = serializers.IntegerField(read_only=True)

    class Meta:
        model = InternshipEvaluation
        fields = [
            "id",
            "placement",
            "placement_detail",
            "evaluator",
            "evaluator_detail",
            "evaluator_role",
            "technical_score",
            "professionalism_score",
            "communication_score",
            "attendance_score",
            "total_score",
            "comments",
            "recommendation",
            "created_at",
        ]
        read_only_fields = ["evaluator", "created_at"]

    def validate(self, attrs):
        for field in ["technical_score", "professionalism_score", "communication_score", "attendance_score"]:
            score = attrs.get(field, 0)
            if score < 0 or score > 25:
                raise serializers.ValidationError({field: "Score must be between 0 and 25."})
        return attrs


class LearningMaterialSerializer(serializers.ModelSerializer):
    course_detail = CourseSerializer(source="course", read_only=True)
    uploaded_by_detail = UserSummarySerializer(source="uploaded_by", read_only=True)

    class Meta:
        model = LearningMaterial
        fields = [
            "id",
            "course",
            "course_detail",
            "title",
            "material_type",
            "url",
            "body",
            "uploaded_by",
            "uploaded_by_detail",
            "created_at",
        ]
        read_only_fields = ["uploaded_by", "created_at"]


class AssignmentSerializer(serializers.ModelSerializer):
    course_detail = CourseSerializer(source="course", read_only=True)
    created_by_detail = UserSummarySerializer(source="created_by", read_only=True)
    submission_status = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = [
            "id",
            "course",
            "course_detail",
            "title",
            "instructions",
            "due_at",
            "max_score",
            "created_by",
            "created_by_detail",
            "created_at",
            "submission_status",
        ]
        read_only_fields = ["created_by", "created_at"]

    def get_submission_status(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        submission = obj.submissions.filter(student=request.user).first()
        return submission.status if submission else None


class SubmissionSerializer(serializers.ModelSerializer):
    assignment_detail = AssignmentSerializer(source="assignment", read_only=True)
    student_detail = UserSummarySerializer(source="student", read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id",
            "assignment",
            "assignment_detail",
            "student",
            "student_detail",
            "text",
            "file_url",
            "status",
            "score",
            "feedback",
            "submitted_at",
            "graded_at",
        ]
        read_only_fields = ["student", "status", "score", "feedback", "submitted_at", "graded_at"]


class GradeSubmissionSerializer(serializers.Serializer):
    score = serializers.DecimalField(max_digits=6, decimal_places=2)
    feedback = serializers.CharField(required=False, allow_blank=True)


class NotificationSerializer(serializers.ModelSerializer):
    recipient_detail = UserSummarySerializer(source="recipient", read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "recipient", "recipient_detail", "title", "message", "kind", "is_read", "created_at"]
        read_only_fields = ["created_at"]


class WorkflowRecordSerializer(serializers.ModelSerializer):
    actor_detail = UserSummarySerializer(source="actor", read_only=True)

    class Meta:
        model = WorkflowRecord
        fields = ["id", "actor", "actor_detail", "action", "target_type", "target_id", "details", "created_at"]
        read_only_fields = ["actor", "created_at"]
