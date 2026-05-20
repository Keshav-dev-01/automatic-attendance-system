#!/usr/bin/env python
"""
Database initialization script for the Attendance Application.

This script creates all tables in the database and optionally adds test data.
Run this after making any changes to models.

Usage:
    python setup_db.py              # Initialize database
    python setup_db.py --reset      # Reset and reinitialize database
"""

import os
import sys
from attendance_app.app import create_app
from attendance_app.extensions import db
from attendance_app.models.user import User, Student, Attendance, UserRole

def init_db():
    """Initialize database with all models"""
    app = create_app()
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✓ Database tables created successfully!")
        
        # Check if tables have data
        user_count = User.query.count()
        student_count = Student.query.count()
        
        print(f"\nDatabase Status:")
        print(f"  Users: {user_count}")
        print(f"  Students: {student_count}")
        print(f"  Attendance Records: {Attendance.query.count()}")

def reset_db():
    """Reset database (WARNING: This will delete all data!)"""
    app = create_app()
    with app.app_context():
        print("WARNING: This will delete ALL data in the database!")
        confirm = input("Are you sure you want to reset the database? (yes/no): ")
        
        if confirm.lower() == 'yes':
            print("Dropping all tables...")
            db.drop_all()
            print("✓ All tables dropped")
            
            print("Creating new tables...")
            db.create_all()
            print("✓ Database reset successfully!")
        else:
            print("Database reset cancelled.")

def add_test_data():
    """Add sample test data"""
    app = create_app()
    with app.app_context():
        # Check if admin user already exists
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("Test data already exists. Skipping.")
            return
        
        print("Adding test data...")
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@attendance.local',
            full_name='Administrator',
            role=UserRole.ADMIN.value,
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Create teacher user
        teacher = User(
            username='teacher1',
            email='teacher1@attendance.local',
            full_name='John Teacher',
            role=UserRole.TEACHER.value,
            is_active=True
        )
        teacher.set_password('teacher123')
        db.session.add(teacher)
        
        # Create student users
        students_data = [
            ('student1', 'STU001', 'Alice Johnson'),
            ('student2', 'STU002', 'Bob Smith'),
            ('student3', 'STU003', 'Charlie Brown'),
        ]
        
        for username, student_id, full_name in students_data:
            user = User(
                username=username,
                email=f'{username}@attendance.local',
                full_name=full_name,
                role=UserRole.STUDENT.value,
                is_active=True
            )
            user.set_password('student123')
            db.session.add(user)
            db.session.flush()
            
            # Create student profile
            student = Student(
                user_id=user.id,
                student_id=student_id,
                photo_path=None,
                photo_embedding=None
            )
            db.session.add(student)
        
        db.session.commit()
        print("✓ Test data added successfully!")
        print("\nTest Credentials:")
        print("  Admin: admin / admin123")
        print("  Teacher: teacher1 / teacher123")
        print("  Student: student1 / student123")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--reset':
            reset_db()
        elif sys.argv[1] == '--test':
            init_db()
            add_test_data()
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Usage: python setup_db.py [--reset | --test]")
    else:
        init_db()
