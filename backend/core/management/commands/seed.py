from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import (
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
PASSWORD = "Passw0rd!"


class Command(BaseCommand):
    help = "Seed the ILES MVP with sample academic data and demo accounts."

    def handle(self, *args, **options):
        admin = self.user("admin", "admin@iles.local", "System", "Administrator", UserProfile.ROLE_ADMIN, True, True)
        instructor = self.user(
            "instructor",
            "instructor@iles.local",
            "Amina",
            "Nalukwago",
            UserProfile.ROLE_INSTRUCTOR,
            department="Computer Science",
        )
        instructor2 = self.user(
            "instructor2",
            "instructor2@iles.local",
            "Daniel",
            "Okello",
            UserProfile.ROLE_INSTRUCTOR,
            department="Information Systems",
        )
        student = self.user(
            "student",
            "student@iles.local",
            "Grace",
            "Atim",
            UserProfile.ROLE_STUDENT,
            department="Computing",
            student_number="ILES-2026-001",
        )
        student2 = self.user(
            "student2",
            "student2@iles.local",
            "Brian",
            "Kato",
            UserProfile.ROLE_STUDENT,
            department="Computing",
            student_number="ILES-2026-002",
        )

        program, _ = Program.objects.update_or_create(
            code="BIS",
            defaults={
                "name": "Bachelor of Information Systems",
                "description": "A practical program focused on software, systems analysis, and digital learning.",
            },
        )
        program2, _ = Program.objects.update_or_create(
            code="BCS",
            defaults={
                "name": "Bachelor of Computer Science",
                "description": "Core computing foundations, programming, and systems design.",
            },
        )

        term, _ = AcademicTerm.objects.update_or_create(
            name="Semester 1 2026",
            defaults={
                "start_date": date(2026, 2, 2),
                "end_date": date(2026, 6, 12),
                "is_active": True,
            },
        )
        AcademicCalendarEvent.objects.update_or_create(
            title="Registration Window",
            term=term,
            defaults={
                "event_type": "registration",
                "starts_on": date(2026, 2, 2),
                "ends_on": date(2026, 2, 16),
                "notes": "Students request enrollment and instructors approve registrations.",
            },
        )
        AcademicCalendarEvent.objects.update_or_create(
            title="Continuous Assessment Deadline",
            term=term,
            defaults={
                "event_type": "assessment",
                "starts_on": date(2026, 4, 20),
                "ends_on": date(2026, 4, 24),
                "notes": "Assignment and coursework checkpoint week.",
            },
        )

        course1, _ = Course.objects.update_or_create(
            code="ILES101",
            defaults={
                "title": "Foundations of Integrated Learning Environments",
                "description": "Learning systems, learner records, roles, registrations, and academic workflows.",
                "program": program,
                "term": term,
                "instructor": instructor,
                "capacity": 80,
                "status": Course.STATUS_ACTIVE,
            },
        )
        course2, _ = Course.objects.update_or_create(
            code="SDP201",
            defaults={
                "title": "Software Development Project",
                "description": "Requirements, design, implementation, testing, deployment, and project documentation.",
                "program": program2,
                "term": term,
                "instructor": instructor2,
                "capacity": 60,
                "status": Course.STATUS_ACTIVE,
            },
        )

        Enrollment.objects.update_or_create(
            student=student,
            course=course1,
            defaults={"status": Enrollment.STATUS_APPROVED, "decided_at": timezone.now()},
        )
        Enrollment.objects.update_or_create(
            student=student2,
            course=course1,
            defaults={"status": Enrollment.STATUS_PENDING},
        )
        Enrollment.objects.update_or_create(
            student=student,
            course=course2,
            defaults={"status": Enrollment.STATUS_PENDING},
        )

        LearningMaterial.objects.update_or_create(
            course=course1,
            title="Course Orientation Notes",
            defaults={
                "material_type": LearningMaterial.TYPE_NOTE,
                "body": "Overview of ILES actors, dashboards, content delivery, assignments, submissions, and audit trails.",
                "uploaded_by": instructor,
            },
        )
        LearningMaterial.objects.update_or_create(
            course=course1,
            title="Learning Systems Reference Link",
            defaults={
                "material_type": LearningMaterial.TYPE_LINK,
                "url": "https://www.django-rest-framework.org/",
                "body": "Reference material for building API-driven learning platforms.",
                "uploaded_by": instructor,
            },
        )

        assignment, _ = Assignment.objects.update_or_create(
            course=course1,
            title="Design an ILES Workflow",
            defaults={
                "instructions": "Map the student registration, instructor approval, submission, grading, and notification workflow.",
                "due_at": timezone.now() + timedelta(days=10),
                "max_score": 100,
                "created_by": instructor,
            },
        )
        Submission.objects.update_or_create(
            assignment=assignment,
            student=student,
            defaults={
                "text": "Draft workflow: registration request -> instructor approval -> material access -> submission -> grade notification.",
                "status": Submission.STATUS_SUBMITTED,
            },
        )

        host, _ = HostOrganization.objects.update_or_create(
            name="Kampala Digital Services Ltd",
            defaults={
                "organization_type": HostOrganization.TYPE_COMPANY,
                "sector": "Technology and Business Systems",
                "address": "Plot 12 Innovation Drive, Kampala",
                "contact_person": "Patricia Nansubuga",
                "contact_email": "placements@kampaladigital.local",
                "contact_phone": "+256 700 000 100",
                "website": "https://example.com",
                "notes": "Accepts students for software support, IT operations, and business analysis attachments.",
            },
        )
        host2, _ = HostOrganization.objects.update_or_create(
            name="Central Community Health Office",
            defaults={
                "organization_type": HostOrganization.TYPE_GOVERNMENT,
                "sector": "Public Administration",
                "address": "Municipal Road, Kampala",
                "contact_person": "Michael Ocen",
                "contact_email": "internships@healthoffice.local",
                "contact_phone": "+256 700 000 200",
                "notes": "Public-sector placement for records, reporting, and information systems exposure.",
            },
        )
        placement, _ = InternshipPlacement.objects.update_or_create(
            student=student,
            host_organization=host,
            term=term,
            defaults={
                "instructor": instructor,
                "program": program,
                "position_title": "Systems Support Intern",
                "department": "IT Operations",
                "start_date": date(2026, 2, 16),
                "end_date": date(2026, 5, 29),
                "status": InternshipPlacement.STATUS_ACTIVE,
                "workplace_supervisor_name": "Patricia Nansubuga",
                "workplace_supervisor_email": "placements@kampaladigital.local",
                "workplace_supervisor_phone": "+256 700 000 100",
                "learning_objectives": "Maintain a daily logbook, support users, document issues, and demonstrate professional communication.",
            },
        )
        InternshipPlacement.objects.update_or_create(
            student=student2,
            host_organization=host2,
            term=term,
            defaults={
                "instructor": instructor2,
                "program": program2,
                "position_title": "Records Systems Intern",
                "department": "Data and Records",
                "start_date": date(2026, 2, 16),
                "end_date": date(2026, 5, 29),
                "status": InternshipPlacement.STATUS_PLANNED,
                "workplace_supervisor_name": "Michael Ocen",
                "workplace_supervisor_email": "internships@healthoffice.local",
                "workplace_supervisor_phone": "+256 700 000 200",
                "learning_objectives": "Learn records workflows, data quality checks, and weekly reporting procedures.",
            },
        )
        log_entry, _ = LogbookEntry.objects.update_or_create(
            placement=placement,
            entry_date=date(2026, 3, 2),
            defaults={
                "student": student,
                "hours_worked": 8,
                "activities": "Configured user accounts, logged support tickets, and observed the help desk escalation process.",
                "skills_learned": "User support, ticket classification, and professional communication.",
                "challenges": "Some issue descriptions were incomplete and needed follow-up.",
                "next_plan": "Document common support issues and propose a short troubleshooting guide.",
                "status": LogbookEntry.STATUS_REVIEWED,
                "instructor_feedback": "Good detail. Add evidence of the tools used in the next entry.",
                "reviewed_by": instructor,
                "submitted_at": timezone.now(),
                "reviewed_at": timezone.now(),
            },
        )
        AttendanceRecord.objects.update_or_create(
            placement=placement,
            date=date(2026, 3, 2),
            defaults={
                "student": student,
                "status": AttendanceRecord.STATUS_PRESENT,
                "check_in": "08:15",
                "check_out": "17:00",
                "notes": "Full day at the host organization.",
            },
        )
        InternshipEvaluation.objects.update_or_create(
            placement=placement,
            evaluator=instructor,
            evaluator_role=InternshipEvaluation.EVALUATOR_INSTRUCTOR,
            defaults={
                "technical_score": 20,
                "professionalism_score": 22,
                "communication_score": 21,
                "attendance_score": 23,
                "comments": "The student is settling into the host organization and recording useful work evidence.",
                "recommendation": "Continue weekly reviews and include supervisor sign-off notes.",
            },
        )

        Notification.objects.update_or_create(
            recipient=student,
            title="Welcome to ILES101",
            defaults={
                "message": "Your enrollment is approved. Review the orientation notes and upcoming assignment.",
                "kind": Notification.KIND_INFO,
            },
        )
        Notification.objects.update_or_create(
            recipient=instructor,
            title="Pending registration requests",
            defaults={
                "message": "Review pending course registrations from your instructor dashboard.",
                "kind": Notification.KIND_REGISTRATION,
            },
        )

        WorkflowRecord.objects.get_or_create(
            actor=admin,
            action="seed.loaded",
            target_type="System",
            target_id="iles-mvp",
            defaults={"details": {"summary": "Initial MVP sample data loaded."}},
        )

        self.stdout.write(self.style.SUCCESS("Seed data loaded. Password for all demo accounts: Passw0rd!"))

    def user(
        self,
        username,
        email,
        first_name,
        last_name,
        role,
        is_staff=False,
        is_superuser=False,
        department="",
        student_number="",
    ):
        user, created = User.objects.get_or_create(username=username, defaults={"email": email})
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.is_staff = is_staff or is_superuser or role == UserProfile.ROLE_ADMIN
        user.is_superuser = is_superuser
        user.is_active = True
        if created or not user.has_usable_password():
            user.set_password(PASSWORD)
        else:
            user.set_password(PASSWORD)
        user.save()
        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "role": role,
                "department": department,
                "student_number": student_number,
            },
        )
        return user
