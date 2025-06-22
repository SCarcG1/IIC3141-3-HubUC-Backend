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
            price=lesson_price,
            description="A private lesson for testing"
        )
        retrieved_lesson = None
        with Session(self.engine) as session:
            session.add(lesson)
            session.commit()
            retrieved_lesson = session.get(PrivateLesson, lesson.id)
        self.assertIsNotNone(retrieved_lesson)

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
