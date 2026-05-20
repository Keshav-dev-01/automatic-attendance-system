from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db, login_manager
from enum import Enum
from datetime import datetime

class UserRole(Enum):
    ADMIN = 'admin'
    TEACHER = 'teacher'
    STUDENT = 'student'

class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default=UserRole.STUDENT.value, nullable=False)
    full_name = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role):
        """Check if user has a specific role"""
        return self.role == role
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID"""
    return User.query.get(int(user_id))

class Student(db.Model):
    """Student model for storing student information"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    photo_embedding = db.Column(db.String(128))  # Store headshot perceptual hash (hex string)
    photo_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='student_profile')
    photos = db.relationship('StudentPhoto', back_populates='student', cascade='all, delete-orphan')
    attendances = db.relationship('Attendance', back_populates='student')
    
    def __repr__(self):
        return f'<Student {self.student_id}>'

class StudentPhoto(db.Model):
    """Store multiple student face photos and embeddings."""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    photo_path = db.Column(db.String(255), nullable=False)
    photo_embedding = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', back_populates='photos')

    def __repr__(self):
        return f'<StudentPhoto {self.student_id} {self.photo_path}>'

class Attendance(db.Model):
    """Attendance record model"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time_in = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='absent')  # present, absent, late
    photo_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('Student', back_populates='attendances')
    teacher = db.relationship('User', backref='attendance_records')
    
    def __repr__(self):
        return f'<Attendance {self.student_id} - {self.date}>'
