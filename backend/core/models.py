from django.conf import settings
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    ROLE_ADMIN = "admin"
    ROLE_INSTRUCTOR = "instructor"
    ROLE_STUDENT = "student"
    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_INSTRUCTOR, "Instructor"),
        (ROLE_STUDENT, "Student"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    department = models.CharField(max_length=120, blank=True)
    student_number = models.CharField(max_length=40, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Program(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class AcademicTerm(models.Model):
    name = models.CharField(max_length=120)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return self.name


class AcademicCalendarEvent(models.Model):
    title = models.CharField(max_length=160)
    term = models.ForeignKey(AcademicTerm, on_delete=models.CASCADE, related_name="calendar_events")
    event_type = models.CharField(max_length=80, default="academic")
    starts_on = models.DateField()
    ends_on = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["starts_on", "title"]

    def __str__(self):
        return self.title


class Course(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_ACTIVE = "active"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_ARCHIVED, "Archived"),
    ]

    code = models.CharField(max_length=30, unique=True)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    program = models.ForeignKey(Program, on_delete=models.PROTECT, related_name="courses")
    term = models.ForeignKey(AcademicTerm, on_delete=models.PROTECT, related_name="courses")
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="teaching_courses",
    )
    capacity = models.PositiveIntegerField(default=60)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.title}"


class Enrollment(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    registered_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ["student", "course"]
        ordering = ["-registered_at"]

    def approve(self):
        self.status = self.STATUS_APPROVED
        self.decided_at = timezone.now()
        self.save(update_fields=["status", "decided_at"])

    def reject(self):
        self.status = self.STATUS_REJECTED
        self.decided_at = timezone.now()
        self.save(update_fields=["status", "decided_at"])

    def __str__(self):
        return f"{self.student.username} -> {self.course.code}"


class HostOrganization(models.Model):
    TYPE_COMPANY = "company"
    TYPE_NGO = "ngo"
    TYPE_GOVERNMENT = "government"
    TYPE_SCHOOL = "school"
    TYPE_HEALTH = "health"
    TYPE_OTHER = "other"
    TYPE_CHOICES = [
        (TYPE_COMPANY, "Company"),
        (TYPE_NGO, "NGO"),
        (TYPE_GOVERNMENT, "Government Office"),
        (TYPE_SCHOOL, "School or Institution"),
        (TYPE_HEALTH, "Health Facility"),
        (TYPE_OTHER, "Other"),
    ]

    name = models.CharField(max_length=180, unique=True)
    organization_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default=TYPE_COMPANY)
    sector = models.CharField(max_length=120, blank=True)
    address = models.TextField(blank=True)
    contact_person = models.CharField(max_length=140, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=40, blank=True)
    website = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class InternshipPlacement(models.Model):
    STATUS_PLANNED = "planned"
    STATUS_ACTIVE = "active"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PLANNED, "Planned"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="internship_placements")
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="supervised_placements",
    )
    host_organization = models.ForeignKey(
        HostOrganization,
        on_delete=models.PROTECT,
        related_name="placements",
    )
    program = models.ForeignKey(Program, on_delete=models.PROTECT, related_name="internship_placements")
    term = models.ForeignKey(AcademicTerm, on_delete=models.PROTECT, related_name="internship_placements")
    position_title = models.CharField(max_length=160)
    department = models.CharField(max_length=140, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PLANNED)
    workplace_supervisor_name = models.CharField(max_length=140, blank=True)
    workplace_supervisor_email = models.EmailField(blank=True)
    workplace_supervisor_phone = models.CharField(max_length=40, blank=True)
    learning_objectives = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date", "student__username"]
        unique_together = ["student", "host_organization", "term"]

    def __str__(self):
        return f"{self.student.username} at {self.host_organization.name}"


class LogbookEntry(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_SUBMITTED = "submitted"
    STATUS_REVIEWED = "reviewed"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_SUBMITTED, "Submitted"),
        (STATUS_REVIEWED, "Reviewed"),
    ]

    placement = models.ForeignKey(InternshipPlacement, on_delete=models.CASCADE, related_name="logbook_entries")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="logbook_entries")
    entry_date = models.DateField()
    hours_worked = models.DecimalField(max_digits=4, decimal_places=1, default=8)
    activities = models.TextField()
    skills_learned = models.TextField(blank=True)
    challenges = models.TextField(blank=True)
    next_plan = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    instructor_feedback = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_logbook_entries",
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-entry_date", "-created_at"]
        unique_together = ["placement", "entry_date"]

    def __str__(self):
        return f"{self.student.username} - {self.entry_date}"


class AttendanceRecord(models.Model):
    STATUS_PRESENT = "present"
    STATUS_ABSENT = "absent"
    STATUS_LATE = "late"
    STATUS_REMOTE = "remote"
    STATUS_CHOICES = [
        (STATUS_PRESENT, "Present"),
        (STATUS_ABSENT, "Absent"),
        (STATUS_LATE, "Late"),
        (STATUS_REMOTE, "Remote"),
    ]

    placement = models.ForeignKey(InternshipPlacement, on_delete=models.CASCADE, related_name="attendance_records")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PRESENT)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        unique_together = ["placement", "date"]

    def __str__(self):
        return f"{self.student.username} - {self.date} - {self.status}"


class InternshipEvaluation(models.Model):
    EVALUATOR_INSTRUCTOR = "instructor"
    EVALUATOR_HOST = "host_supervisor"
    EVALUATOR_CHOICES = [
        (EVALUATOR_INSTRUCTOR, "Instructor"),
        (EVALUATOR_HOST, "Host Supervisor"),
    ]

    placement = models.ForeignKey(InternshipPlacement, on_delete=models.CASCADE, related_name="evaluations")
    evaluator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    evaluator_role = models.CharField(max_length=30, choices=EVALUATOR_CHOICES, default=EVALUATOR_INSTRUCTOR)
    technical_score = models.PositiveSmallIntegerField(default=0)
    professionalism_score = models.PositiveSmallIntegerField(default=0)
    communication_score = models.PositiveSmallIntegerField(default=0)
    attendance_score = models.PositiveSmallIntegerField(default=0)
    comments = models.TextField(blank=True)
    recommendation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def total_score(self):
        return (
            self.technical_score
            + self.professionalism_score
            + self.communication_score
            + self.attendance_score
        )

    def __str__(self):
        return f"Evaluation for {self.placement}"


class LearningMaterial(models.Model):
    TYPE_NOTE = "note"
    TYPE_LINK = "link"
    TYPE_VIDEO = "video"
    TYPE_FILE = "file"
    TYPE_CHOICES = [
        (TYPE_NOTE, "Note"),
        (TYPE_LINK, "Link"),
        (TYPE_VIDEO, "Video"),
        (TYPE_FILE, "File"),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="materials")
    title = models.CharField(max_length=180)
    material_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_NOTE)
    url = models.URLField(blank=True)
    body = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="materials")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=180)
    instructions = models.TextField()
    due_at = models.DateTimeField()
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="assignments_created")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_at"]

    def __str__(self):
        return self.title


class Submission(models.Model):
    STATUS_SUBMITTED = "submitted"
    STATUS_GRADED = "graded"
    STATUS_RETURNED = "returned"
    STATUS_CHOICES = [
        (STATUS_SUBMITTED, "Submitted"),
        (STATUS_GRADED, "Graded"),
        (STATUS_RETURNED, "Returned"),
    ]

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submissions")
    text = models.TextField(blank=True)
    file_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUBMITTED)
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ["assignment", "student"]
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"


class Notification(models.Model):
    KIND_INFO = "info"
    KIND_ASSIGNMENT = "assignment"
    KIND_REGISTRATION = "registration"
    KIND_GRADE = "grade"
    KIND_CHOICES = [
        (KIND_INFO, "Info"),
        (KIND_ASSIGNMENT, "Assignment"),
        (KIND_REGISTRATION, "Registration"),
        (KIND_GRADE, "Grade"),
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=180)
    message = models.TextField()
    kind = models.CharField(max_length=30, choices=KIND_CHOICES, default=KIND_INFO)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class WorkflowRecord(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=120)
    target_type = models.CharField(max_length=80)
    target_id = models.CharField(max_length=80, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} {self.target_type}"
