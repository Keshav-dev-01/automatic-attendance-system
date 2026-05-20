# Attendance Management System

A Flask-based web application for managing student attendance with role-based access control (Admin, Teacher, Student).

## Features

- **User Authentication**: Secure login and registration system
- **Role-Based Access Control**: Different dashboards for Admin, Teacher, and Student
- **Student Management**: View and manage student attendance records
- **Teacher Dashboard**: Record and manage attendance
- **Admin Panel**: User management and system reports
- **Database**: SQLite database for data persistence
- **Responsive UI**: Modern, responsive web interface

## Project Structure

```
attendance_app/
├── app.py                 # Flask application factory
├── config.py              # Configuration management
├── extensions.py          # Flask extensions (db, login_manager)
│
├── models/
│   └── user.py            # User model with roles
│
├── auth/
│   ├── routes.py          # Authentication routes
│   ├── forms.py           # Login/Register forms
│   └── utils.py           # Authentication utilities
│
├── student/
│   └── routes.py          # Student dashboard routes
│
├── teacher/
│   └── routes.py          # Teacher dashboard routes
│
├── admin/
│   └── routes.py          # Admin dashboard routes
│
├── templates/
│   ├── base.html          # Base template
│   ├── login.html         # Login page
│   ├── register.html      # Registration page
│   ├── student/
│   │   ├── dashboard.html
│   │   └── attendance.html
│   ├── teacher/
│   │   ├── dashboard.html
│   │   └── attendance_records.html
│   └── admin/
│       ├── dashboard.html
│       ├── users.html
│       └── reports.html
│
└── static/                # Static files (CSS, JS, images)
```

## Installation

1. **Clone the repository**
   ```bash
   cd attendance_app
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables**
   ```bash
   # Create .env file with necessary configurations
   FLASK_APP=attendance_app/app.py
   FLASK_ENV=development
   SECRET_KEY=your-secret-key-here
   ```

5. **Initialize the database**
   ```bash
   python
   >>> from attendance_app.app import create_app
   >>> app = create_app()
   >>> with app.app_context():
   ...     from attendance_app.extensions import db
   ...     db.create_all()
   ```

## Usage

1. **Run the application**
   ```bash
   python -m attendance_app.app
   # OR
   flask run
   ```

2. **Access the application**
   - Open your browser and navigate to `http://localhost:5000`
   - Create a new account or login with existing credentials

3. **Default Roles**
   - **Admin**: Full system access, user management, reports
   - **Teacher**: Manage attendance for students
   - **Student**: View own attendance records

## Requirements

- Python 3.7+
- Flask 2.3+
- Flask-SQLAlchemy
- Flask-Login
- Flask-WTF
- WTForms

See `requirements.txt` for complete dependencies.

## Configuration

Configuration is managed through `config.py`:
- **Development**: Debug mode enabled, local SQLite database
- **Production**: Debug disabled, requires external database
- **Testing**: In-memory database for tests

Update environment variables in `.env` file for different configurations.

## License

MIT License

## Support

For issues or questions, please create an issue in the repository.
