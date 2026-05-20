from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, Response
from flask_login import login_required, current_user, logout_user
from ..auth.utils import login_required_with_role
from ..auth.forms import RegisterForm
from ..extensions import db
from ..models.user import User, Student, Attendance, UserRole
from sqlalchemy import func
from datetime import datetime, date, timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@login_required_with_role('admin')
def dashboard():
    """Admin dashboard with system statistics"""
    # Count users by role
    total_users = User.query.count()
    admin_count = User.query.filter_by(role=UserRole.ADMIN.value).count()
    teacher_count = User.query.filter_by(role=UserRole.TEACHER.value).count()
    student_count = User.query.filter_by(role=UserRole.STUDENT.value).count()
    
    # Attendance statistics
    total_records = Attendance.query.count()
    today = date.today()
    today_records = Attendance.query.filter_by(date=today).count()
    
    # Get recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         user=current_user,
                         total_users=total_users,
                         admin_count=admin_count,
                         teacher_count=teacher_count,
                         student_count=student_count,
                         total_records=total_records,
                         today_records=today_records,
                         recent_users=recent_users)

@admin_bp.route('/users')
@login_required
@login_required_with_role('admin')
def manage_users():
    """Manage all users in the system"""
    page = request.args.get('page', 1, type=int)
    role_filter = request.args.get('role', None)
    
    query = User.query
    
    if role_filter:
        query = query.filter_by(role=role_filter)
    
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=10)
    
    return render_template('admin/users.html', 
                         user=current_user,
                         users=users,
                         selected_role=role_filter)

@admin_bp.route('/user/add', methods=['GET', 'POST'])
@login_required
@login_required_with_role('admin')
def add_user():
    """Add a new user from the admin panel"""
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User created successfully.', 'success')
        return redirect(url_for('admin.manage_users'))

    return render_template('admin/add_user.html', user=current_user, form=form)

@admin_bp.route('/users/delete-all', methods=['POST'])
@login_required
@login_required_with_role('admin')
def delete_all_users():
    """Remove all other users, student profiles, and attendance records."""
    # Delete all attendance records first
    Attendance.query.delete()
    # Delete all student profiles
    Student.query.delete()
    # Delete all users except the currently logged-in admin
    User.query.filter(User.id != current_user.id).delete()
    db.session.commit()

    return jsonify({'success': True, 'message': 'All other users have been deleted. Your admin account remains active.'})

@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
@login_required_with_role('admin')
def delete_user(user_id):
    """Delete a user"""
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Delete related student profile
    Student.query.filter_by(user_id=user_id).delete()

    return jsonify({'success': True, 'message': f'User {user.username} deleted'})

@admin_bp.route('/user/<int:user_id>/toggle', methods=['POST'])
@login_required
@login_required_with_role('admin')
def toggle_user_status(user_id):
    """Toggle user active status"""
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot deactivate your own account'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user.is_active = not user.is_active
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': f'User {user.username} {"activated" if user.is_active else "deactivated"}'
    })

@admin_bp.route('/reports')
@login_required
@login_required_with_role('admin')
def reports():
    """System reports and analytics"""
    # Attendance statistics
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Daily attendance
    today_attendance = Attendance.query.filter_by(date=today).count()
    
    # Weekly attendance
    weekly_attendance = Attendance.query.filter(
        Attendance.date >= week_ago
    ).count()
    
    # Monthly attendance
    monthly_attendance = Attendance.query.filter(
        Attendance.date >= month_ago
    ).count()
    
    # Get top present students
    top_present = db.session.query(
        Student.student_id,
        User.full_name,
        func.count(Attendance.id).label('present_days')
    ).join(User, Student.user_id == User.id)\
     .join(Attendance, Student.id == Attendance.student_id)\
     .filter(Attendance.status == 'present')\
     .group_by(Student.id)\
     .order_by(func.count(Attendance.id).desc())\
     .limit(10).all()
    
    # Get system overview
    system_stats = {
        'total_students': Student.query.count(),
        'total_teachers': User.query.filter_by(role=UserRole.TEACHER.value).count(),
        'total_attendance_records': Attendance.query.count(),
        'today_attendance': today_attendance,
        'weekly_attendance': weekly_attendance,
        'monthly_attendance': monthly_attendance
    }
    
    return render_template('admin/reports.html', 
                         user=current_user,
                         system_stats=system_stats,
                         top_present=top_present)

@admin_bp.route('/reports/export')
@login_required
@login_required_with_role('admin')
def export_reports():
    """Export reports as CSV"""
    import csv
    from io import StringIO
    from flask import send_file
    
    # Get all attendance records
    records = Attendance.query.join(Student).join(User).all()
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Student ID', 'Student Name', 'Status', 'Time In', 'Teacher'])
    
    for record in records:
        writer.writerow([
            record.date,
            record.student.student_id,
            record.student.user.full_name,
            record.status,
            record.time_in.strftime('%H:%M:%S') if record.time_in else 'N/A',
            record.teacher.full_name
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=attendance_reports.csv'
        }
    )

@admin_bp.route('/system-settings')
@login_required
@login_required_with_role('admin')
def system_settings():
    """System configuration and settings"""
    return render_template('admin/settings.html', user=current_user)
