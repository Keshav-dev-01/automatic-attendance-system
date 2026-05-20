from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from ..auth.utils import login_required_with_role
from ..extensions import db
from ..models.user import Student, Attendance
from datetime import datetime, timedelta
from sqlalchemy import func, desc

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@login_required
@login_required_with_role('student')
def dashboard():
    """Student dashboard - view attendance summary"""
    # Get or create student profile
    student = Student.query.filter_by(user_id=current_user.id).first()
    
    if not student:
        # Auto-create student profile if not exists
        student = Student(
            user_id=current_user.id,
            student_id=f'STU-{current_user.id}',
            photo_path=None,
            photo_embedding=None
        )
        db.session.add(student)
        db.session.commit()
    
    # Get attendance statistics
    all_attendance = Attendance.query.filter_by(student_id=student.id).all()
    
    present_count = len([a for a in all_attendance if a.status == 'present'])
    absent_count = len([a for a in all_attendance if a.status == 'absent'])
    total_days = len(all_attendance)
    
    attendance_percentage = 0
    if total_days > 0:
        attendance_percentage = (present_count / total_days) * 100
    
    # Get recent attendance (last 7 days)
    seven_days_ago = datetime.now().date() - timedelta(days=7)
    recent = Attendance.query.filter_by(student_id=student.id)\
        .filter(Attendance.date >= seven_days_ago)\
        .order_by(desc(Attendance.date)).all()
    
    return render_template('student/dashboard.html', 
                         user=current_user,
                         student=student,
                         present_count=present_count,
                         absent_count=absent_count,
                         total_days=total_days,
                         attendance_percentage=attendance_percentage,
                         recent_attendance=recent)

@student_bp.route('/attendance')
@login_required
@login_required_with_role('student')
def attendance():
    """View detailed attendance records"""
    # Get or create student profile
    student = Student.query.filter_by(user_id=current_user.id).first()
    
    if not student:
        student = Student(
            user_id=current_user.id,
            student_id=f'STU-{current_user.id}',
            photo_path=None,
            photo_embedding=None
        )
        db.session.add(student)
        db.session.commit()
    
    records = Attendance.query.filter_by(student_id=student.id)\
        .order_by(desc(Attendance.date)).all()
    
    monthly_stats = db.session.query(
        func.strftime('%Y-%m', Attendance.date).label('month'),
        func.count(Attendance.id).label('total'),
        func.sum((Attendance.status == 'present').cast(db.Integer)).label('present'),
        func.sum((Attendance.status == 'absent').cast(db.Integer)).label('absent')
    ).filter_by(student_id=student.id)\
     .group_by('month')\
     .order_by(desc('month')).all()
    
    return render_template('student/attendance.html', 
                         user=current_user,
                         student=student,
                         records=records,
                         monthly_stats=monthly_stats)

@student_bp.route('/profile')
@login_required
@login_required_with_role('student')
def profile():
    """Student self profile page"""
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        student = Student(
            user_id=current_user.id,
            student_id=f'STU-{current_user.id}',
            photo_path=None,
            photo_embedding=None
        )
        db.session.add(student)
        db.session.commit()

    attendance_records = Attendance.query.filter_by(student_id=student.id).order_by(desc(Attendance.date)).all()
    present_count = len([a for a in attendance_records if a.status == 'present'])
    absent_count = len([a for a in attendance_records if a.status == 'absent'])
    total_days = len(attendance_records)

    return render_template('student/profile.html',
                         user=current_user,
                         student=student,
                         attendance_records=attendance_records,
                         present_count=present_count,
                         absent_count=absent_count,
                         total_days=total_days)
