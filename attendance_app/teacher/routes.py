from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from ..auth.utils import login_required_with_role
from ..extensions import db
from ..models.user import User, Student, StudentPhoto, Attendance, UserRole
from ..utils.photo import save_upload_file, match_faces, match_faces_with_embeddings, extract_face_embedding
from datetime import datetime, date
from sqlalchemy import func, or_

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

@teacher_bp.route('/dashboard')
@login_required
@login_required_with_role('teacher')
def dashboard():
    """Teacher dashboard"""
    today = date.today()
    
    # Get attendance statistics for today
    attendance_today = Attendance.query.filter_by(
        teacher_id=current_user.id,
        date=today
    ).all()
    
    present_count = len([a for a in attendance_today if a.status == 'present'])
    absent_count = len([a for a in attendance_today if a.status == 'absent'])
    
    # Get all students taught by this teacher
    all_students = Student.query.all()
    
    return render_template('teacher/dashboard.html', 
                         user=current_user,
                         present_count=present_count,
                         absent_count=absent_count,
                         total_students=len(all_students))

@teacher_bp.route('/mark-attendance', methods=['GET', 'POST'])
@login_required
@login_required_with_role('teacher')
def mark_attendance():
    """Auto-mark attendance with continuous face recognition"""
    if request.method == 'POST':
        # This is now used for real-time frame processing
        if 'photo' not in request.files:
            return jsonify({'error': 'No photo provided'}), 400
        
        file = request.files['photo']
        photo_path = save_upload_file(file)
        
        if not photo_path:
            return jsonify({'error': 'Invalid file format'}), 400
        
        embedding = extract_face_embedding(photo_path)
        if not embedding:
            return jsonify({'error': 'No face detected', 'matched': False}), 400
        
        # Get all students
        all_students = Student.query.all()
        best_match = None
        best_score = 0.0
        match_threshold = 0.6
        
        # Compare with all student embeddings
        for student in all_students:
            stored_embeddings = []
            if student.photo_embedding:
                stored_embeddings.append(student.photo_embedding)
            for photo in student.photos:
                stored_embeddings.append(photo.photo_embedding)
            
            if not stored_embeddings:
                continue
            
            for stored_emb in stored_embeddings:
                try:
                    score = compare_embeddings(embedding, stored_emb)
                    if score > best_score:
                        best_score = score
                        best_match = student
                except:
                    pass
        
        if best_match and best_score >= match_threshold:
            today = date.today()
            existing = Attendance.query.filter_by(
                student_id=best_match.id,
                teacher_id=current_user.id,
                date=today
            ).first()
            
            if not existing:
                attendance = Attendance(
                    student_id=best_match.id,
                    teacher_id=current_user.id,
                    date=today,
                    status='present',
                    time_in=datetime.now(),
                    photo_path=photo_path
                )
                db.session.add(attendance)
            else:
                existing.status = 'present'
                existing.time_in = datetime.now()
                existing.photo_path = photo_path
                attendance = existing
            db.session.commit()
            
            return jsonify({
                'matched': True,
                'success': True,
                'student_id': best_match.student_id,
                'student_name': best_match.user.full_name or best_match.student_id,
                'student_email': best_match.user.email,
                'score': best_score,
                'message': f'✓ {best_match.student_id} marked present'
            })
        else:
            # Return best attempt even if below threshold (for debugging)
            return jsonify({
                'matched': False,
                'score': best_score,
                'best_student': best_match.student_id if best_match else None,
                'threshold': match_threshold,
                'message': f'Face not clearly recognized (score: {best_score:.2f}, threshold: {match_threshold})'
            }), 400
    
    all_students = Student.query.all()
    return render_template('teacher/mark_attendance_auto.html', 
                         user=current_user,
                         total_students=len(all_students))

def compare_embeddings(emb1, emb2):
    """Compare two perceptual hash embeddings for similarity (0-1 score)"""
    try:
        import imagehash
        
        if not emb1 or not emb2:
            return 0.0
        
        # Use the same proven method from photo.py
        h1 = imagehash.hex_to_hash(emb1)
        h2 = imagehash.hex_to_hash(emb2)
        
        # Hamming distance (0-64 for 64-bit hash)
        distance = h1 - h2
        # Convert to similarity score (1.0 = identical, 0.0 = completely different)
        similarity = 1.0 - (distance / 64.0)
        return max(0.0, min(1.0, similarity))
    except Exception as e:
        print(f"Error comparing embeddings: {e}")
        return 0.0

@teacher_bp.route('/mark-attendance-old', methods=['GET', 'POST'])
@login_required
@login_required_with_role('teacher')
def mark_attendance_old():
    """Old manual attendance marking (kept for reference)"""
    if request.method == 'POST':
        if 'photo' not in request.files:
            return jsonify({'error': 'No photo provided'}), 400
        
        file = request.files['photo']
        student_id = request.form.get('student_id')
        
        if not student_id:
            return jsonify({'error': 'No student selected'}), 400
        
        # Save uploaded photo
        photo_path = save_upload_file(file)
        if not photo_path:
            return jsonify({'error': 'Invalid file format'}), 400
        
        # Get student
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        # Match face with stored embeddings from that student
        stored_embeddings = []
        if student.photo_embedding:
            stored_embeddings.append(student.photo_embedding)
        stored_embeddings.extend([photo.photo_embedding for photo in student.photos])

        if not stored_embeddings:
            return jsonify({'error': 'Student has no registered photos.'}), 400

        match_score, is_match, best_match = match_faces_with_embeddings(photo_path, stored_embeddings)
        
        if is_match:
            today = date.today()
            existing = Attendance.query.filter_by(
                student_id=student_id,
                teacher_id=current_user.id,
                date=today
            ).first()
            
            if existing:
                existing.status = 'present'
                existing.time_in = datetime.now()
                existing.photo_path = photo_path
            else:
                attendance = Attendance(
                    student_id=student_id,
                    teacher_id=current_user.id,
                    date=today,
                    time_in=datetime.now(),
                    status='present',
                    photo_path=photo_path
                )
                db.session.add(attendance)
            
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'{student.user.full_name} marked present',
                'match_score': match_score
            }), 200

        warning = 'Face not recognized for this student.'
        if match_score >= 0.45:
            warning = ('Low confidence face match. Please choose a different student, '
                       'register more photos for this student, or mark present manually.')

        return jsonify({
            'success': False,
            'error': warning,
            'match_score': match_score
        }), 400
    
    # GET request - show attendance marking page
    students = Student.query.all()
    return render_template('teacher/mark_attendance_old.html', 
                         user=current_user,
                         students=students)

@teacher_bp.route('/students')
@login_required
@login_required_with_role('teacher')
def student_list():
    """Show teacher student list with search and status filters."""
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip().lower()
    today = date.today()

    query = Student.query.join(User)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Student.student_id.ilike(pattern),
                User.full_name.ilike(pattern),
                User.username.ilike(pattern),
                User.email.ilike(pattern)
            )
        )

    students = query.order_by(Student.student_id).all()
    student_rows = []
    for student in students:
        attendance = Attendance.query.filter_by(
            student_id=student.id,
            teacher_id=current_user.id,
            date=today
        ).first()
        status = 'unmarked'
        if attendance:
            status = attendance.status
        student_rows.append({
            'student': student,
            'status': status,
            'photo_path': student.photo_path,
            'login_username': student.user.username,
            'login_email': student.user.email
        })

    if status_filter in ('present', 'absent', 'unmarked'):
        student_rows = [row for row in student_rows if row['status'] == status_filter]

    return render_template('teacher/student_list.html',
                         user=current_user,
                         students=student_rows,
                         search=search,
                         status_filter=status_filter)

@teacher_bp.route('/student/<int:student_id>/profile')
@login_required
@login_required_with_role('teacher')
def student_profile(student_id):
    """Show a detailed student profile for teacher review."""
    student = Student.query.get_or_404(student_id)
    attendance_records = Attendance.query.filter_by(student_id=student.id).order_by(Attendance.date.desc()).all()
    present_count = len([a for a in attendance_records if a.status == 'present'])
    absent_count = len([a for a in attendance_records if a.status == 'absent'])
    total_days = len(attendance_records)
    return render_template('teacher/student_profile.html',
                         user=current_user,
                         student=student,
                         attendance_records=attendance_records,
                         present_count=present_count,
                         absent_count=absent_count,
                         total_days=total_days)

@teacher_bp.route('/attendance-records')
@login_required
@login_required_with_role('teacher')
def attendance_records():
    """View and manage attendance records"""
    today = date.today()

    # Ensure every student has a record for today, default absent
    all_students = Student.query.all()
    for student in all_students:
        existing = Attendance.query.filter_by(
            student_id=student.id,
            teacher_id=current_user.id,
            date=today
        ).first()
        if not existing:
            db.session.add(Attendance(
                student_id=student.id,
                teacher_id=current_user.id,
                date=today,
                status='absent'
            ))
    db.session.commit()

    records = db.session.query(
        Attendance,
        Student,
        func.count(Attendance.id).label('total_days')
    ).join(Student, Attendance.student_id == Student.id)\
     .filter(Attendance.teacher_id == current_user.id,
             Attendance.date == today)\
     .group_by(Student.id)\
     .all()

    present_students = [r for r in records if r[0].status == 'present']
    absent_students = [r for r in records if r[0].status == 'absent']

    return render_template('teacher/attendance_records.html', 
                         user=current_user,
                         present_students=present_students,
                         absent_students=absent_students,
                         total_present=len(present_students),
                         total_absent=len(absent_students))

@teacher_bp.route('/attendance-records/mark-present/<int:student_id>', methods=['POST'])
@login_required
@login_required_with_role('teacher')
def mark_student_present(student_id):
    """Mark a student present manually without photo verification."""
    today = date.today()
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404

    attendance = Attendance.query.filter_by(
        student_id=student_id,
        teacher_id=current_user.id,
        date=today
    ).first()

    if not attendance:
        attendance = Attendance(
            student_id=student_id,
            teacher_id=current_user.id,
            date=today,
            status='present',
            time_in=datetime.now()
        )
        db.session.add(attendance)
    else:
        attendance.status = 'present'
        attendance.time_in = datetime.now()

    db.session.commit()
    return jsonify({'success': True, 'message': f'{student.user.full_name or student.student_id} marked present manually.'})

@teacher_bp.route('/register-student', methods=['GET', 'POST'])
@login_required
@login_required_with_role('teacher')
def register_student():
    """Register a student user and their photo for face recognition."""
    if request.method == 'POST':
        if 'photo' not in request.files:
            flash('No photo provided', 'danger')
            return redirect(url_for('teacher.register_student'))

        file = request.files['photo']
        student_id = request.form.get('student_id')
        student_name = request.form.get('name') or student_id
        student_email = request.form.get('email') or f'{student_id}@school.local'
        student_password_input = request.form.get('password')
        student_password = student_password_input or student_id

        if not student_id:
            flash('Student ID is required', 'danger')
            return redirect(url_for('teacher.register_student'))

        student_id = student_id.strip()
        if len(student_id) < 6:
            flash('Student ID must be at least 6 characters long.', 'danger')
            return redirect(url_for('teacher.register_student'))

        if student_password_input and len(student_password_input) < 6:
            flash('Temporary password must be at least 6 characters long.', 'danger')
            return redirect(url_for('teacher.register_student'))

        photo_path = save_upload_file(file)
        if not photo_path:
            flash('Invalid file format', 'danger')
            return redirect(url_for('teacher.register_student'))

        embedding = extract_face_embedding(photo_path)

        # Create or update student user account
        username = student_id
        student_user = User.query.filter(or_(User.username == username, User.email == student_email)).first()
        if student_user and student_user.role != UserRole.STUDENT.value:
            flash('A user with this username or email already exists and is not a student.', 'danger')
            return redirect(url_for('teacher.register_student'))

        if not student_user:
            student_user = User(
                username=username,
                email=student_email,
                full_name=student_name,
                role=UserRole.STUDENT.value
            )
            student_user.set_password(student_password)
            db.session.add(student_user)
            db.session.commit()
        else:
            student_user.full_name = student_name
            student_user.email = student_email
            if student_password:
                student_user.set_password(student_password)
            db.session.commit()

        student = Student.query.filter_by(student_id=student_id).first()
        if not student:
            student = Student(
                user_id=student_user.id,
                student_id=student_id,
                photo_path=photo_path,
                photo_embedding=embedding
            )
            db.session.add(student)
            db.session.commit()
        else:
            student.user_id = student_user.id
            student.photo_path = photo_path
            student.photo_embedding = embedding
            db.session.commit()

        photo_entry = StudentPhoto(
            student_id=student.id,
            photo_path=photo_path,
            photo_embedding=embedding
        )
        db.session.add(photo_entry)
        db.session.commit()

        message = f'Student {student_id} registered successfully. '
        message += f'Login username/password: {username}/{student_password}'
        flash(message, 'success')
        return redirect(url_for('teacher.attendance_records'))

    return render_template('teacher/register_student.html', user=current_user)
