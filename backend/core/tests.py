from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import (
    AcademicTerm,
    Assignment,
    Course,
    Enrollment,
    HostOrganization,
    InternshipEvaluation,
    InternshipPlacement,
    LogbookEntry,
    Program,
    Submission,
    UserProfile,
)


User = get_user_model()


class IlesApiTests(APITestCase):
    def setUp(self):
        self.admin = self.make_user("admin", UserProfile.ROLE_ADMIN, is_staff=True, is_superuser=True)
        self.instructor = self.make_user("instructor", UserProfile.ROLE_INSTRUCTOR)
        self.student = self.make_user("student", UserProfile.ROLE_STUDENT)
        self.program = Program.objects.create(code="TST", name="Test Program")
        self.term = AcademicTerm.objects.create(
            name="Test Term",
            start_date="2026-01-01",
            end_date="2026-05-01",
            is_active=True,
        )
        self.course = Course.objects.create(
            code="TST101",
            title="Test Course",
            program=self.program,
            term=self.term,
            instructor=self.instructor,
            status=Course.STATUS_ACTIVE,
        )
        self.assignment = Assignment.objects.create(
            course=self.course,
            title="Test Assignment",
            instructions="Submit a short response.",
            due_at=timezone.now(),
            created_by=self.instructor,
        )
        self.host = HostOrganization.objects.create(
            name="Test Host Organization",
            organization_type=HostOrganization.TYPE_COMPANY,
            contact_person="Host Supervisor",
        )
        self.placement = InternshipPlacement.objects.create(
            student=self.student,
            instructor=self.instructor,
            host_organization=self.host,
            program=self.program,
            term=self.term,
            position_title="IT Support Intern",
            start_date="2026-01-15",
            end_date="2026-04-30",
            status=InternshipPlacement.STATUS_ACTIVE,
        )

    def make_user(self, username, role, is_staff=False, is_superuser=False):
        user = User.objects.create_user(
            username=username,
            email=f"{username}@iles.local",
            password="Passw0rd!",
            is_staff=is_staff,
            is_superuser=is_superuser,
        )
        UserProfile.objects.update_or_create(user=user, defaults={"role": role})
        return user

    def auth(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_login_and_current_user(self):
        response = self.client.post(reverse("login"), {"username": "student", "password": "Passw0rd!"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
        me = self.client.get(reverse("current-user"))
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data["role"], UserProfile.ROLE_STUDENT)

    def test_public_registration_creates_student_account(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newstudent",
                "email": "newstudent@iles.local",
                "first_name": "New",
                "last_name": "Student",
                "student_number": "S1001",
                "department": "Computing",
                "password": "NewStudentPassw0rd!",
                "confirm_password": "NewStudentPassw0rd!",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["role"], UserProfile.ROLE_STUDENT)

        user = User.objects.get(username="newstudent")
        self.assertTrue(user.check_password("NewStudentPassw0rd!"))
        self.assertEqual(user.profile.role, UserProfile.ROLE_STUDENT)
        self.assertEqual(user.profile.student_number, "S1001")

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
        me = self.client.get(reverse("current-user"))
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data["username"], "newstudent")

    def test_registration_rejects_duplicate_username_or_email(self):
        duplicate_username = self.client.post(
            reverse("register"),
            {
                "username": "student",
                "email": "another@iles.local",
                "password": "NewStudentPassw0rd!",
                "confirm_password": "NewStudentPassw0rd!",
            },
        )
        self.assertEqual(duplicate_username.status_code, 400)

        duplicate_email = self.client.post(
            reverse("register"),
            {
                "username": "anotherstudent",
                "email": "student@iles.local",
                "password": "NewStudentPassw0rd!",
                "confirm_password": "NewStudentPassw0rd!",
            },
        )
        self.assertEqual(duplicate_email.status_code, 400)

    def test_logged_in_user_can_change_password_and_old_token_is_invalid(self):
        self.auth(self.student)
        old_token = Token.objects.get(user=self.student)

        bad_response = self.client.post(
            reverse("change-password"),
            {
                "current_password": "wrong-password",
                "new_password": "StudentNewPassw0rd!",
                "confirm_password": "StudentNewPassw0rd!",
            },
        )
        self.assertEqual(bad_response.status_code, 400)

        response = self.client.post(
            reverse("change-password"),
            {
                "current_password": "Passw0rd!",
                "new_password": "StudentNewPassw0rd!",
                "confirm_password": "StudentNewPassw0rd!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Token.objects.filter(key=old_token.key).exists())

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {old_token.key}")
        me = self.client.get(reverse("current-user"))
        self.assertEqual(me.status_code, 401)

        self.client.credentials()
        old_login = self.client.post(reverse("login"), {"username": "student", "password": "Passw0rd!"})
        new_login = self.client.post(reverse("login"), {"username": "student", "password": "StudentNewPassw0rd!"})
        self.assertEqual(old_login.status_code, 400)
        self.assertEqual(new_login.status_code, 200)

    def test_password_reset_flow_works_for_each_existing_role(self):
        cases = [
            (self.admin, "AdminResetPassw0rd!"),
            (self.instructor, "InstructorResetPassw0rd!"),
            (self.student, "StudentResetPassw0rd!"),
        ]

        for user, new_password in cases:
            with self.subTest(username=user.username):
                token, _ = Token.objects.get_or_create(user=user)
                request_response = self.client.post(
                    reverse("password-reset-request"),
                    {"identifier": user.email},
                )
                self.assertEqual(request_response.status_code, 200)
                self.assertIn("reset_code", request_response.data)

                confirm_response = self.client.post(
                    reverse("password-reset-confirm"),
                    {
                        "identifier": user.username,
                        "reset_code": request_response.data["reset_code"],
                        "new_password": new_password,
                        "confirm_password": new_password,
                    },
                )
                self.assertEqual(confirm_response.status_code, 200)
                self.assertFalse(Token.objects.filter(key=token.key).exists())

                old_login = self.client.post(reverse("login"), {"username": user.username, "password": "Passw0rd!"})
                new_login = self.client.post(reverse("login"), {"username": user.username, "password": new_password})
                self.assertEqual(old_login.status_code, 400)
                self.assertEqual(new_login.status_code, 200)

    def test_student_can_request_course_registration(self):
        self.auth(self.student)
        response = self.client.post(f"/api/courses/{self.course.id}/register/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], Enrollment.STATUS_PENDING)
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course).exists())

    def test_instructor_can_approve_registration(self):
        enrollment = Enrollment.objects.create(student=self.student, course=self.course)
        self.auth(self.instructor)
        response = self.client.post(f"/api/enrollments/{enrollment.id}/approve/")
        self.assertEqual(response.status_code, 200)
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, Enrollment.STATUS_APPROVED)

    def test_student_can_submit_and_instructor_can_grade(self):
        Enrollment.objects.create(student=self.student, course=self.course, status=Enrollment.STATUS_APPROVED)
        self.auth(self.student)
        response = self.client.post(
            "/api/submissions/",
            {"assignment": self.assignment.id, "text": "Here is my work."},
        )
        self.assertEqual(response.status_code, 201)
        submission_id = response.data["id"]

        self.auth(self.instructor)
        grade = self.client.post(
            f"/api/submissions/{submission_id}/grade/",
            {"score": "88.50", "feedback": "Good workflow coverage."},
        )
        self.assertEqual(grade.status_code, 200)
        submission = Submission.objects.get(id=submission_id)
        self.assertEqual(submission.status, Submission.STATUS_GRADED)
        self.assertEqual(str(submission.score), "88.50")

    def test_student_can_submit_logbook_and_instructor_can_review(self):
        self.auth(self.student)
        response = self.client.post(
            "/api/logbook-entries/",
            {
                "placement": self.placement.id,
                "entry_date": "2026-02-01",
                "hours_worked": "8.0",
                "activities": "Configured accounts and documented support issues.",
                "skills_learned": "Ticket handling and user communication.",
            },
        )
        self.assertEqual(response.status_code, 201)
        entry_id = response.data["id"]

        submit = self.client.post(f"/api/logbook-entries/{entry_id}/submit/")
        self.assertEqual(submit.status_code, 200)

        self.auth(self.instructor)
        review = self.client.post(
            f"/api/logbook-entries/{entry_id}/review/",
            {"instructor_feedback": "Good detail. Add screenshots next time."},
        )
        self.assertEqual(review.status_code, 200)
        entry = LogbookEntry.objects.get(id=entry_id)
        self.assertEqual(entry.status, LogbookEntry.STATUS_REVIEWED)
        self.assertEqual(entry.reviewed_by, self.instructor)

    def test_instructor_can_create_internship_evaluation(self):
        self.auth(self.instructor)
        response = self.client.post(
            "/api/internship-evaluations/",
            {
                "placement": self.placement.id,
                "evaluator_role": InternshipEvaluation.EVALUATOR_INSTRUCTOR,
                "technical_score": 20,
                "professionalism_score": 22,
                "communication_score": 21,
                "attendance_score": 23,
                "comments": "Strong progress.",
                "recommendation": "Continue weekly logbook reviews.",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["total_score"], 86)
