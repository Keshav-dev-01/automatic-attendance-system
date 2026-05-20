# Attendance System Implementation Guide

## Completed Features (Based on Flowchart)

This document outlines all the features implemented based on the attendance system flowchart provided.

### 1. **Authentication System** ✓
- Login for Teacher/Admin/Student
- Role-based access control
- User registration with different roles
- Password hashing and secure authentication

### 2. **Teacher Dashboard** ✓
- Home screen with navigation and profile button
- Statistics showing:
  - Number of students present
  - Number of students absent
  - Total number of students
- Quick access to main features

### 3. **Photo-Based Attendance** ✓
- **Mark Attendance Route**: `/teacher/mark-attendance`
  - Live camera feed for capturing student photos
  - Student selection dropdown
  - Photo capture and verification interface
  - Face matching against stored embeddings
  - Real-time feedback on match success/failure

### 4. **Face Recognition System** ✓
- Photo capture from teacher's device
- Storage of student photos in database
- Face embedding extraction (placeholder ready for real library)
- Photo matching with confidence score
- Support for unregistered student error handling

### 5. **Student Registration** ✓
- **Register Student Route**: `/teacher/register-student`
- Capture and store student photo
- Generate face embeddings for recognition
- Student information storage
- Photo path tracking in database

### 6. **Attendance Recording** ✓
- Automatic marking of present/absent status
- Time-in recording
- Photo reference for each attendance record
- Daily attendance tracking
- Database persistence

### 7. **Attendance Dashboard** ✓
- **View Records Route**: `/teacher/attendance-records`
- Tabular display of:
  - Present students (with time-in)
  - Absent students
  - Statistics summary
- Color-coded status badges
- Responsive table layout

## Database Models

### User Model
```
- id (Primary Key)
- username (Unique)
- email (Unique)
- password_hash
- role (admin, teacher, student)
- full_name
- is_active
- created_at
```

### Student Model
```
- id (Primary Key)
- user_id (Foreign Key to User)
- student_id (Unique)
- photo_path
- photo_embedding (Face recognition data)
- created_at
```

### Attendance Model
```
- id (Primary Key)
- student_id (Foreign Key to Student)
- teacher_id (Foreign Key to User)
- date
- time_in
- status (present, absent, late)
- photo_path (Reference to captured photo)
- created_at
```

## Project Structure

```
attendance_app/
├── app.py                          # Flask app factory
├── config.py                       # Configuration
├── extensions.py                   # Flask extensions
├── models/
│   ├── user.py                    # User, Student, Attendance models
├── auth/
│   ├── routes.py                  # Auth routes
│   ├── forms.py                   # Login/Register forms
│   ├── utils.py                   # Auth utilities & decorators
├── teacher/
│   └── routes.py                  # Teacher routes (mark attendance, etc.)
├── utils/
│   └── photo.py                   # Photo handling utilities
├── templates/
│   ├── base.html                  # Base template
│   ├── login.html
│   ├── register.html
│   ├── teacher/
│   │   ├── dashboard.html         # Teacher home screen
│   │   ├── mark_attendance.html   # Photo capture interface
│   │   ├── attendance_records.html # Attendance table/dashboard
│   │   └── register_student.html  # Student registration
│   └── static/
│       └── uploads/               # Uploaded photos
```

## Setup Instructions

### 1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 2. **Initialize Database**
```bash
# Basic initialization
python setup_db.py

# With test data
python setup_db.py --test

# Reset database (WARNING: Deletes all data)
python setup_db.py --reset
```

### 3. **Run the Application**
```bash
python -m attendance_app.app
```
The application will be available at `http://localhost:5000`

### 4. **Test Credentials (if using --test flag)**
```
Admin:    admin / admin123
Teacher:  teacher1 / teacher123
Student:  student1 / student123
```

## API Endpoints

### Authentication
- `GET/POST /auth/login` - User login
- `GET/POST /auth/register` - User registration
- `GET /auth/logout` - User logout

### Teacher Routes
- `GET /teacher/dashboard` - Teacher home screen
- `GET/POST /teacher/mark-attendance` - Mark attendance with photo
- `GET /teacher/attendance-records` - View attendance records
- `GET/POST /teacher/register-student` - Register new student with photo

## Technical Implementation Details

### Photo Capture (Frontend)
- Uses HTML5 `getUserMedia()` API for camera access
- Canvas API for photo capture
- Real-time preview before submission
- Blob conversion for file upload

### Photo Upload (Backend)
- File validation (allowed extensions: png, jpg, jpeg, gif, webp)
- Secure filename generation with timestamp and hash
- Upload folder: `attendance_app/static/uploads/`
- Maximum file size: 5MB

### Face Recognition (Placeholder)
- Currently uses placeholder matching (80% confidence threshold)
- Ready for integration with:
  - `face_recognition` library
  - `deepface` library
  - `mediapipe` for face detection
  - OpenCV for image processing

### Match Score System
- Returns confidence score (0.0 to 1.0)
- Threshold: 0.80 (80%)
- Above threshold = Student marked present
- Below threshold = Registration error message

## Next Steps for Production

1. **Implement Real Face Recognition**
   ```bash
   # Install face recognition library
   pip install face-recognition
   # or
   pip install deepface
   ```

2. **Update `utils/photo.py`**
   - Replace `match_faces()` function with real face matching
   - Replace `extract_face_embedding()` with real embedding extraction

3. **Add SSL/HTTPS Support**
   - Configure SSL certificates for production
   - Update Flask app configuration

4. **Database Migration to Production**
   - Switch from SQLite to PostgreSQL/MySQL
   - Update `DATABASE_URL` in `.env`

5. **Security Hardening**
   - Update `SECRET_KEY` in `.env`
   - Enable CSRF protection
   - Add rate limiting
   - Implement API authentication tokens

6. **File Storage**
   - Move uploads to cloud storage (S3, Azure Blob, etc.)
   - Implement backup strategy

7. **Testing**
   - Add unit tests
   - Add integration tests
   - Performance testing under load

## Error Handling

### Common Errors and Solutions

**Camera Permission Denied**
- Browser requires HTTPS (or localhost)
- User needs to grant camera permission
- Check browser settings

**Student Not Found**
- Ensure student is registered first
- Check student_id in database

**Face Not Matching**
- Lighting conditions may affect recognition
- Ask student to retake photo
- Ensure face is clearly visible
- Check if student's photo is properly registered

## Environment Variables

Create a `.env` file with:
```
FLASK_APP=attendance_app/app.py
FLASK_ENV=development
SECRET_KEY=your-secure-random-key-here
DATABASE_URL=sqlite:///attendance.db
```

## File Uploads

Photos are stored in: `attendance_app/static/uploads/`

Naming convention: `YYYYMMDD_HHMMSS_<hash>.ext`

Example: `20240518_143022_a1b2c3d4.jpg`

## Performance Considerations

- Face embedding storage in database (binary data)
- Photo caching for quick access
- Indexed queries on student_id and date
- Consider implementing pagination for large attendance lists

## Support & Documentation

For more details on specific components:
- Flask: https://flask.palletsprojects.com/
- Flask-SQLAlchemy: https://flask-sqlalchemy.palletsprojects.com/
- Face Recognition: https://github.com/ageitgey/face_recognition

---

**Last Updated**: May 18, 2026
**Status**: Core features implemented, ready for face recognition integration
