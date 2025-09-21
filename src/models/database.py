"""
Database models and initialization for the AI Timetable Generator.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication."""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')
    full_name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(20), nullable=True, index=True)
    department = db.Column(db.String(50), nullable=True)
    semester = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Course(db.Model):
    """Course model."""
    __tablename__ = 'courses'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False, unique=True, index=True)
    department = db.Column(db.String(50), nullable=False, index=True)
    semester = db.Column(db.String(20), nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    course_type = db.Column(db.String(20), nullable=False, default='LECTURE')
    enrolled_students = db.Column(db.Integer, nullable=False, default=0)
    duration = db.Column(db.Integer, nullable=False, default=90)  # minutes
    sessions_per_week = db.Column(db.Integer, nullable=False, default=2)
    faculty_id = db.Column(db.String(36), db.ForeignKey('faculty.id'), nullable=True)
    required_equipment = db.Column(db.JSON, nullable=True)
    assigned_batches = db.Column(db.JSON, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    faculty = db.relationship('Faculty', backref='courses')
    
    def __repr__(self):
        return f'<Course {self.code}: {self.name}>'

class Faculty(db.Model):
    """Faculty model."""
    __tablename__ = 'faculty'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    department = db.Column(db.String(50), nullable=False, index=True)
    max_hours_per_week = db.Column(db.Integer, default=20)
    available_slots = db.Column(db.JSON, nullable=True)
    subjects_expertise = db.Column(db.JSON, nullable=True)
    max_classes_per_day = db.Column(db.Integer, default=6)
    priority_level = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Faculty {self.name}>'

class Classroom(db.Model):
    """Classroom model."""
    __tablename__ = 'classrooms'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(50), nullable=False, unique=True)
    capacity = db.Column(db.Integer, nullable=False)
    room_type = db.Column(db.String(20), nullable=False)
    equipment = db.Column(db.JSON, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Classroom {self.name}>'

class Batch(db.Model):
    """Batch model."""
    __tablename__ = 'batches'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(50), nullable=False, unique=True, index=True)
    department = db.Column(db.String(50), nullable=False, index=True)
    semester = db.Column(db.String(20), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    section = db.Column(db.String(10), nullable=False)
    student_count = db.Column(db.Integer, nullable=False)
    max_classes_per_day = db.Column(db.Integer, default=6)
    student_id_start = db.Column(db.String(20), nullable=True)
    student_id_end = db.Column(db.String(20), nullable=True)
    student_id_pattern = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Batch {self.name}>'

class Schedule(db.Model):
    """Schedule model."""
    __tablename__ = 'schedules'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    course_id = db.Column(db.String(36), db.ForeignKey('courses.id'), nullable=False)
    faculty_id = db.Column(db.String(36), db.ForeignKey('faculty.id'), nullable=False)
    classroom_id = db.Column(db.String(36), db.ForeignKey('classrooms.id'), nullable=False)
    batch_id = db.Column(db.String(36), db.ForeignKey('batches.id'), nullable=False)
    day_of_week = db.Column(db.String(10), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # minutes
    week_number = db.Column(db.Integer, default=1)
    session_type = db.Column(db.String(20), default='regular')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    course = db.relationship('Course', backref='schedule_entries')
    faculty = db.relationship('Faculty', backref='schedule_entries')
    classroom = db.relationship('Classroom', backref='schedule_entries')
    batch = db.relationship('Batch', backref='schedule_entries')
    
    def __repr__(self):
        return f'<Schedule {self.course.code} - {self.day_of_week} {self.start_time}>'

class FacultyUnavailability(db.Model):
    """Faculty unavailability model."""
    __tablename__ = 'faculty_unavailability'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    faculty_id = db.Column(db.String(36), db.ForeignKey('faculty.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.Integer, default=1)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    faculty = db.relationship('Faculty', backref='unavailabilities')
    creator = db.relationship('User', backref='created_unavailabilities')
    
    def __repr__(self):
        return f'<Unavailability {self.faculty.name} - {self.reason}>'

class AttendanceRecord(db.Model):
    """Attendance record model."""
    __tablename__ = 'attendance_records'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column(db.String(20), nullable=False, index=True)
    course_id = db.Column(db.String(36), db.ForeignKey('courses.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False)  # present, absent, late
    marked_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    course = db.relationship('Course', backref='attendance_records')
    marker = db.relationship('User', backref='marked_attendance')
    
    def __repr__(self):
        return f'<Attendance {self.student_id} - {self.course.code} - {self.status}>'

class Note(db.Model):
    """Notes model."""
    __tablename__ = 'notes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    course_id = db.Column(db.String(36), db.ForeignKey('courses.id'), nullable=False)
    uploaded_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    file_path = db.Column(db.String(500), nullable=True)
    file_name = db.Column(db.String(200), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    mime_type = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    course = db.relationship('Course', backref='notes')
    uploader = db.relationship('User', backref='uploaded_notes')
    
    def __repr__(self):
        return f'<Note {self.title}>'

class SystemLog(db.Model):
    """System log model for monitoring."""
    __tablename__ = 'system_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    level = db.Column(db.String(10), nullable=False)  # INFO, WARNING, ERROR, CRITICAL
    message = db.Column(db.Text, nullable=False)
    module = db.Column(db.String(50), nullable=True)
    function = db.Column(db.String(50), nullable=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    additional_data = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = db.relationship('User', backref='system_logs')
    
    def __repr__(self):
        return f'<Log {self.level}: {self.message[:50]}>'

def init_db(app):
    """Initialize database with app context."""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create default admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@college.edu',
                role='admin',
                full_name='System Administrator'
            )
            admin.set_password('admin123')
            db.session.add(admin)
        
        # Create default faculty user if not exists
        if not User.query.filter_by(username='faculty').first():
            faculty_user = User(
                username='faculty',
                email='faculty@college.edu',
                role='faculty',
                full_name='Dr. Faculty Member',
                department='Computer Science'
            )
            faculty_user.set_password('faculty123')
            db.session.add(faculty_user)
        
        # Create default student users if not exist
        for i in range(1, 4):
            username = f'student{i}'
            if not User.query.filter_by(username=username).first():
                student = User(
                    username=username,
                    email=f'{username}@student.edu',
                    role='student',
                    full_name=f'Student {i}',
                    student_id=f'CS2024{i:03d}',
                    department='Computer Science',
                    semester='Fall 2024'
                )
                student.set_password('student123')
                db.session.add(student)
        
        try:
            db.session.commit()
            print("✅ Database initialized with default users")
        except Exception as e:
            db.session.rollback()
            print(f"⚠️ Database initialization warning: {e}")

def get_db_stats():
    """Get database statistics."""
    return {
        'users': User.query.count(),
        'courses': Course.query.count(),
        'faculty': Faculty.query.count(),
        'classrooms': Classroom.query.count(),
        'batches': Batch.query.count(),
        'schedules': Schedule.query.count(),
        'attendance_records': AttendanceRecord.query.count(),
        'notes': Note.query.count()
    }