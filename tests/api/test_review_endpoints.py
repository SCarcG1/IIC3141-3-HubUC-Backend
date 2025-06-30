from app.api.routes import get_db
from app.database import Base
from app.main import app
from app.models.course import Course
from app.models.private_lesson import PrivateLesson
from app.models.reservation import Reservation
from app.models.review import Review
from app.models.user import User
from app.models.weekly_timeblock import WeeklyTimeblock
from app.schemas.reservation import ReservationCreate, ReservationStatus
from app.schemas.review import ReviewCreate
from app.schemas.user import UserRole
from app.schemas.weekday import Weekday
from app.schemas.weekly_timeblock import WeeklyTimeblockCreate
from datetime import datetime, time
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import select
from tests.auth_for_tests import get_auth_header_for_tests
from tests.db_for_tests import db_engine, get_db_for_tests, SessionLocal
from unittest import IsolatedAsyncioTestCase
import os


app.dependency_overrides[get_db] = get_db_for_tests
SECRET_KEY = os.getenv("JWT_SECRET", "test_secret")

def generate_token(user_id: int, role: str):
    return jwt.encode({"user_id": user_id, "role": role, "sub": f"{role}@test.com"}, SECRET_KEY, algorithm="HS256")


class TestReviewEndpoints(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Initialize test client and database
        self.app = TestClient(app)
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Create example course, student, and tutor
        self.course = Course(name="Test Course", description="Course desc")
        self.student = User(email="student@test.com", password="pw", name="Student", role="student")
        self.tutor = User(email="tutor@test.com", password="pw", name="Tutor", role="tutor")
        
        async with SessionLocal() as session:
            session.add_all([self.course, self.student, self.tutor])
            await session.commit()
            await session.refresh(self.course)
            await session.refresh(self.student)
            await session.refresh(self.tutor)
        
        # Create example lesson and weekly timeblock
        self.lesson = PrivateLesson(
            tutor_id=self.tutor.id,
            course_id=self.course.id,
            price=10000
        )
        self.weekly_timeblock = WeeklyTimeblock(
            user_id=self.tutor.id,
            **WeeklyTimeblockCreate(
                weekday=Weekday.MONDAY,
                start_hour=time(9),
                end_hour=time(17),
                valid_from=datetime(2025, 6, 1),
                valid_until=datetime(2025, 6, 30),
            ).model_dump()
        )
        
        async with SessionLocal() as session:
            session.add_all([self.lesson, self.weekly_timeblock])
            await session.commit()
            await session.refresh(self.lesson)
            await session.refresh(self.weekly_timeblock)
        
        # Create a reservation for testing
        self.reservation = Reservation(
            private_lesson_id=self.lesson.id,
            student_id=self.student.id,
            status=ReservationStatus.ACCEPTED,
            start_time=datetime(2025, 6, 2, 10, 0, 0),
            end_time=datetime(2025, 6, 2, 11, 0, 0)
        )
        
        async with SessionLocal() as session:
            session.add(self.reservation)
            await session.commit()
            await session.refresh(self.reservation)

    async def asyncTearDown(self):
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def test_create_review(self):
        """Test creating a new review"""
        review_data = {
            "reservation_id": self.reservation.id,
            "content": "Excelente tutor, muy recomendado",
            "rating": 5
        }
        
        response = self.app.post(
            "/reviews",
            json=review_data,
            headers=get_auth_header_for_tests(
                email=self.student.email,
                role=UserRole.student,
                user_id=self.student.id
            ),
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["reservation_id"], self.reservation.id)
        self.assertEqual(data["content"], review_data["content"])
        self.assertEqual(data["rating"], review_data["rating"])
        self.assertIn("created_at", data)
        self.assertIn("id", data)

    async def test_create_review_duplicate(self):
        """Test that only one review can be created per reservation"""
        review_data = {
            "reservation_id": self.reservation.id,
            "content": "Excelente tutor, muy recomendado",
            "rating": 5
        }
        
        # Create first review
        response1 = self.app.post(
            "/reviews",
            json=review_data,
            headers=get_auth_header_for_tests(
                email=self.student.email,
                role=UserRole.student,
                user_id=self.student.id
            ),
        )
        self.assertEqual(response1.status_code, 201)
        
        # Try to create second review for same reservation
        response2 = self.app.post(
            "/reviews",
            json=review_data,
            headers=get_auth_header_for_tests(
                email=self.student.email,
                role=UserRole.student,
                user_id=self.student.id
            ),
        )
        self.assertEqual(response2.status_code, 400)
        self.assertIn("already exists", response2.json()["detail"])

    async def test_create_review_only_students(self):
        """Test that only students can create reviews"""
        review_data = {
            "reservation_id": self.reservation.id,
            "content": "Excelente tutor, muy recomendado",
            "rating": 5
        }
        
        response = self.app.post(
            "/reviews",
            json=review_data,
            headers=get_auth_header_for_tests(
                email=self.tutor.email,
                role=UserRole.tutor,
                user_id=self.tutor.id
            ),
        )
        
        self.assertEqual(response.status_code, 403)
        self.assertIn("Only students can create reviews", response.json()["detail"])

    async def test_get_all_reviews(self):
        """Test getting all reviews"""
        # Create a review first
        review_data = {
            "reservation_id": self.reservation.id,
            "content": "Excelente tutor, muy recomendado",
            "rating": 5
        }
        
        self.app.post(
            "/reviews",
            json=review_data,
            headers=get_auth_header_for_tests(
                email=self.student.email,
                role=UserRole.student,
                user_id=self.student.id
            ),
        )
        
        response = self.app.get(
            "/reviews",
            headers=get_auth_header_for_tests(
                email=self.student.email,
                role=UserRole.student,
                user_id=self.student.id
            ),
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    async def test_get_review_by_id(self):
        """Test getting a specific review by ID"""
        # Create a review first
        review_data = {
            "reservation_id": self.reservation.id,
            "content": "Excelente tutor, muy recomendado",
            "rating": 5
        }
        
        create_response = self.app.post(
            "/reviews",
            json=review_data,
            headers=get_auth_header_for_tests(
                email=self.student.email,
                role=UserRole.student,
                user_id=self.student.id
            ),
        )
        review_id = create_response.json()["id"]
        
        response = self.app.get(
            f"/reviews/{review_id}",
            headers=get_auth_header_for_tests(
                email=self.student.email,
                role=UserRole.student,
                user_id=self.student.id
            ),
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], review_id)
        self.assertEqual(data["content"], review_data["content"])

    async def test_update_review(self):
        """Test updating a review"""
        # Create a review first
        review_data = {
            "reservation_id": self.reservation.id,
            "content": "Excelente tutor, muy recomendado",
            "rating": 5
        }
        
        create_response = self.app.post(
            "/reviews",
            json=review_data,
            headers=get_auth_header_for_tests(
                email=self.student.email,
                role=UserRole.student,
                user_id=self.student.id
            ),
        )
        review_id = create_response.json()["id"]
        
        # Update the review
        update_data = {
            "content": "Muy buen tutor, aprendí mucho",
            "rating": 4
        }
        
        response = self.app.patch(
            f"/reviews/{review_id}",
            json=update_data,
            headers=get_auth_header_for_tests(
                email=self.student.email,
                role=UserRole.student,
                user_id=self.student.id
            ),
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["content"], update_data["content"])
        self.assertEqual(data["rating"], update_data["rating"])

    async def test_delete_review(self):
        """Test deleting a review"""
        # Create a review first
        review_data = {
            "reservation_id": self.reservation.id,
            "content": "Excelente tutor, muy recomendado",
            "rating": 5
        }
        
        create_response = self.app.post(
            "/reviews",
            json=review_data,
            headers=get_auth_header_for_tests(
                email=self.student.email,
                role=UserRole.student,
                user_id=self.student.id
            ),
        )
        review_id = create_response.json()["id"]
        
        # Delete the review
        response = self.app.delete(
            f"/reviews/{review_id}",
            headers=get_auth_header_for_tests(
                email=self.student.email,
                role=UserRole.student,
                user_id=self.student.id
            ),
        )
        
        self.assertEqual(response.status_code, 204)
        
        # Verify the review is deleted
        get_response = self.app.get(
            f"/reviews/{review_id}",
            headers=get_auth_header_for_tests(
                email=self.student.email,
                role=UserRole.student,
                user_id=self.student.id
            ),
        )
        self.assertEqual(get_response.status_code, 404) 