from app.database import Base
from app.models.course import Course
from app.models.private_lesson import PrivateLesson
from app.models.reservation import Reservation
from app.models.review import Review
from app.models.user import User
from datetime import datetime, timedelta
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from unittest import TestCase


class TestModels(TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_course_creation_in_database(self):
        course = Course(
            name="Test Course",
            description="A course for testing"
        )
        retrieved_course = None
        with Session(self.engine) as session:
            session.add(course)
            session.commit()
            retrieved_course = session.get(Course, course.id)
        self.assertIsNotNone(retrieved_course)

    def test_private_lesson_creation_in_database(self):
        course = Course(
            name="Test Course",
            description="Description."
        )
        tutor = User(
            email="tutor@example.com",
            password="password",
            name="Tutor Name",
            role="tutor"
        )
        with Session(self.engine) as session:
            session.add_all([course, tutor])
            session.commit()
            course = session.get(Course, course.id)
            tutor = session.get(User, tutor.id)
        lesson_price = 10000
        lesson = PrivateLesson(
            tutor_id=tutor.id,
            course_id=course.id,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            price=lesson_price,
            description="A private lesson for testing"
        )
        retrieved_lesson = None
        with Session(self.engine) as session:
            session.add(lesson)
            session.commit()
            retrieved_lesson = session.get(PrivateLesson, lesson.id)
        self.assertIsNotNone(retrieved_lesson)

    def test_reservation_creation_in_database(self):
        course = Course(
            name="Test Course",
            description="Description."
        )
        student = User(
            email="student@example.com",
            password="password",
            name="Student Name",
            role="student"
        )
        tutor = User(
            email="tutor@example.com",
            password="password",
            name="Tutor Name",
            role="tutor"
        )
        with Session(self.engine) as session:
            session.add_all((course, student, tutor))
            session.commit()
            course = session.get(Course, course.id)
            student = session.get(User, student.id)
            tutor = session.get(User, tutor.id)
        lesson = PrivateLesson(
            tutor_id=tutor.id,
            course_id=course.id,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            price=100,
            description="A private lesson for testing"
        )
        with Session(self.engine) as session:
            session.add(lesson)
            session.commit()
            lesson = session.get(PrivateLesson, lesson.id)
        reservation = Reservation(
            student_id=student.id,
            private_lesson_id=lesson.id,
            status="pending"
        )
        retrieved_reservation = None
        with Session(self.engine) as session:
            session.add(reservation)
            session.commit()
            retrieved_reservation = session.get(Reservation, reservation.id)
        self.assertIsNotNone(retrieved_reservation)

    def test_review_creation_in_database(self):
        course = Course(
            name="Test Course",
            description="Description."
        )
        student = User(
            email="student@example.com",
            password="password",
            name="Student Name",
            role="student"
        )
        tutor = User(
            email="tutor@example.com",
            password="password",
            name="Tutor Name",
            role="tutor"
        )
        with Session(self.engine) as session:
            session.add_all([course, student, tutor])
            session.commit()
            course = session.get(Course, course.id)
            student = session.get(User, student.id)
            tutor = session.get(User, tutor.id)
        lesson = PrivateLesson(
            tutor_id=tutor.id,
            course_id=course.id,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            price=10000,
            description="A private lesson for testing"
        )
        with Session(self.engine) as session:
            session.add(lesson)
            session.commit()
            lesson = session.get(PrivateLesson, lesson.id)
        reservation = Reservation(
            student_id=student.id,
            private_lesson_id=lesson.id,
            status="accepted"
        )
        with Session(self.engine) as session:
            session.add(reservation)
            session.commit()
            reservation = session.get(Reservation, reservation.id)
        review = Review(
            reservation_id=reservation.id,
            content="Lorem ipsum dolor sit amet.",
            rating=5
        )
        retrieved_review = None
        with Session(self.engine) as session:
            session.add(review)
            session.commit()
            retrieved_review = session.get(Review, review.id)
        self.assertIsNotNone(retrieved_review)

    def test_user_creation_in_database(self):
        user = User(
            email="example@example.com",
            password="password",
            name="Steve",
            role="student"
        )
        retrieved_user = None
        with Session(self.engine) as session:
            session.add(user)
            session.commit()
            retrieved_user = session.get(User, user.id)
        self.assertIsNotNone(retrieved_user)
