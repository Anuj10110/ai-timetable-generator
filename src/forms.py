"""
Flask-WTF forms for input validation and CSRF protection.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, EmailField, SelectField, IntegerField,
    TextAreaField, DateTimeLocalField, BooleanField, FieldList, FormField,
    SelectMultipleField, DecimalField, FileField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, ValidationError, NumberRange,
    Optional, Regexp
)
from flask_wtf.file import FileAllowed
from models.database import User
import re

class LoginForm(FlaskForm):
    """User login form."""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    remember_me = BooleanField('Remember Me')

class RegistrationForm(FlaskForm):
    """User registration form."""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters'),
        Regexp(r'^[a-zA-Z0-9_]+$', message='Username can only contain letters, numbers, and underscores')
    ])
    email = EmailField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address'),
        Length(max=120, message='Email must be less than 120 characters')
    ])
    full_name = StringField('Full Name', validators=[
        DataRequired(message='Full name is required'),
        Length(min=2, max=100, message='Full name must be between 2 and 100 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=8, message='Password must be at least 8 characters long'),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)', 
               message='Password must contain at least one lowercase letter, one uppercase letter, and one digit')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    role = SelectField('Role', choices=[
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('admin', 'Administrator')
    ], validators=[DataRequired()])
    
    # Student-specific fields
    student_id = StringField('Student ID', validators=[
        Optional(),
        Length(max=20, message='Student ID must be less than 20 characters'),
        Regexp(r'^[A-Z0-9]+$', message='Student ID can only contain uppercase letters and numbers')
    ])
    
    department = SelectField('Department', choices=[
        ('', 'Select Department'),
        ('Computer Science', 'Computer Science'),
        ('Mathematics', 'Mathematics'),
        ('Physics', 'Physics'),
        ('Chemistry', 'Chemistry'),
        ('Biology', 'Biology'),
        ('English', 'English'),
        ('History', 'History'),
        ('Economics', 'Economics'),
        ('Psychology', 'Psychology')
    ], validators=[Optional()])
    
    semester = SelectField('Semester', choices=[
        ('', 'Select Semester'),
        ('Fall 2024', 'Fall 2024'),
        ('Spring 2024', 'Spring 2024'),
        ('Summer 2024', 'Summer 2024'),
        ('Fall 2023', 'Fall 2023'),
        ('Spring 2023', 'Spring 2023')
    ], validators=[Optional()])
    
    def validate_username(self, username):
        """Custom validation for username uniqueness."""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')
    
    def validate_email(self, email):
        """Custom validation for email uniqueness."""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email.')
    
    def validate_student_id(self, student_id):
        """Validate student ID for student role."""
        if self.role.data == 'student' and not student_id.data:
            raise ValidationError('Student ID is required for student accounts.')
        if student_id.data:
            user = User.query.filter_by(student_id=student_id.data).first()
            if user:
                raise ValidationError('Student ID already exists.')

class CourseForm(FlaskForm):
    """Course creation/edit form."""
    name = StringField('Course Name', validators=[
        DataRequired(message='Course name is required'),
        Length(min=3, max=100, message='Course name must be between 3 and 100 characters')
    ])
    code = StringField('Course Code', validators=[
        DataRequired(message='Course code is required'),
        Length(min=2, max=20, message='Course code must be between 2 and 20 characters'),
        Regexp(r'^[A-Z0-9]+$', message='Course code can only contain uppercase letters and numbers')
    ])
    department = SelectField('Department', choices=[
        ('Computer Science', 'Computer Science'),
        ('Mathematics', 'Mathematics'),
        ('Physics', 'Physics'),
        ('Chemistry', 'Chemistry'),
        ('Biology', 'Biology'),
        ('English', 'English'),
        ('History', 'History'),
        ('Economics', 'Economics'),
        ('Psychology', 'Psychology')
    ], validators=[DataRequired()])
    semester = SelectField('Semester', choices=[
        ('Fall 2024', 'Fall 2024'),
        ('Spring 2024', 'Spring 2024'),
        ('Summer 2024', 'Summer 2024')
    ], validators=[DataRequired()])
    credits = IntegerField('Credits', validators=[
        DataRequired(message='Credits are required'),
        NumberRange(min=1, max=10, message='Credits must be between 1 and 10')
    ])
    course_type = SelectField('Course Type', choices=[
        ('LECTURE', 'Lecture'),
        ('LAB', 'Laboratory'),
        ('SEMINAR', 'Seminar'),
        ('TUTORIAL', 'Tutorial')
    ], validators=[DataRequired()])
    enrolled_students = IntegerField('Enrolled Students', validators=[
        DataRequired(message='Number of enrolled students is required'),
        NumberRange(min=1, max=500, message='Enrolled students must be between 1 and 500')
    ])
    duration = IntegerField('Duration (minutes)', validators=[
        DataRequired(message='Duration is required'),
        NumberRange(min=30, max=300, message='Duration must be between 30 and 300 minutes')
    ])
    sessions_per_week = IntegerField('Sessions Per Week', validators=[
        DataRequired(message='Sessions per week is required'),
        NumberRange(min=1, max=7, message='Sessions per week must be between 1 and 7')
    ])
    faculty_id = SelectField('Faculty', coerce=str, validators=[Optional()])
    required_equipment = StringField('Required Equipment (comma-separated)', validators=[Optional()])

class FacultyForm(FlaskForm):
    """Faculty creation/edit form."""
    name = StringField('Faculty Name', validators=[
        DataRequired(message='Faculty name is required'),
        Length(min=2, max=100, message='Faculty name must be between 2 and 100 characters')
    ])
    email = EmailField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    department = SelectField('Department', choices=[
        ('Computer Science', 'Computer Science'),
        ('Mathematics', 'Mathematics'),
        ('Physics', 'Physics'),
        ('Chemistry', 'Chemistry'),
        ('Biology', 'Biology'),
        ('English', 'English'),
        ('History', 'History'),
        ('Economics', 'Economics'),
        ('Psychology', 'Psychology')
    ], validators=[DataRequired()])
    max_hours_per_week = IntegerField('Max Hours Per Week', validators=[
        DataRequired(message='Max hours per week is required'),
        NumberRange(min=5, max=60, message='Max hours must be between 5 and 60')
    ])
    max_classes_per_day = IntegerField('Max Classes Per Day', validators=[
        DataRequired(message='Max classes per day is required'),
        NumberRange(min=1, max=10, message='Max classes per day must be between 1 and 10')
    ])
    subjects_expertise = StringField('Subject Expertise (comma-separated)', validators=[Optional()])

class ClassroomForm(FlaskForm):
    """Classroom creation/edit form."""
    name = StringField('Classroom Name', validators=[
        DataRequired(message='Classroom name is required'),
        Length(min=2, max=50, message='Classroom name must be between 2 and 50 characters')
    ])
    capacity = IntegerField('Capacity', validators=[
        DataRequired(message='Capacity is required'),
        NumberRange(min=5, max=1000, message='Capacity must be between 5 and 1000')
    ])
    room_type = SelectField('Room Type', choices=[
        ('lecture_hall', 'Lecture Hall'),
        ('computer_lab', 'Computer Lab'),
        ('seminar_room', 'Seminar Room'),
        ('laboratory', 'Laboratory'),
        ('auditorium', 'Auditorium'),
        ('tutorial_room', 'Tutorial Room')
    ], validators=[DataRequired()])
    location = StringField('Location', validators=[
        Optional(),
        Length(max=100, message='Location must be less than 100 characters')
    ])
    equipment = StringField('Equipment (comma-separated)', validators=[Optional()])

class BatchForm(FlaskForm):
    """Batch creation/edit form."""
    name = StringField('Batch Name', validators=[
        DataRequired(message='Batch name is required'),
        Length(min=3, max=50, message='Batch name must be between 3 and 50 characters'),
        Regexp(r'^[A-Z0-9\-]+$', message='Batch name can only contain uppercase letters, numbers, and hyphens')
    ])
    department = SelectField('Department', choices=[
        ('Computer Science', 'Computer Science'),
        ('Mathematics', 'Mathematics'),
        ('Physics', 'Physics'),
        ('Chemistry', 'Chemistry'),
        ('Biology', 'Biology'),
        ('English', 'English'),
        ('History', 'History'),
        ('Economics', 'Economics'),
        ('Psychology', 'Psychology')
    ], validators=[DataRequired()])
    semester = SelectField('Semester', choices=[
        ('1st Semester', '1st Semester'),
        ('2nd Semester', '2nd Semester'),
        ('3rd Semester', '3rd Semester'),
        ('4th Semester', '4th Semester'),
        ('5th Semester', '5th Semester'),
        ('6th Semester', '6th Semester'),
        ('7th Semester', '7th Semester'),
        ('8th Semester', '8th Semester')
    ], validators=[DataRequired()])
    year = IntegerField('Year', validators=[
        DataRequired(message='Year is required'),
        NumberRange(min=2020, max=2030, message='Year must be between 2020 and 2030')
    ])
    section = StringField('Section', validators=[
        DataRequired(message='Section is required'),
        Length(min=1, max=10, message='Section must be between 1 and 10 characters')
    ])
    student_count = IntegerField('Student Count', validators=[
        DataRequired(message='Student count is required'),
        NumberRange(min=1, max=200, message='Student count must be between 1 and 200')
    ])
    max_classes_per_day = IntegerField('Max Classes Per Day', validators=[
        DataRequired(message='Max classes per day is required'),
        NumberRange(min=1, max=10, message='Max classes per day must be between 1 and 10')
    ])
    student_id_start = StringField('Student ID Start', validators=[
        Optional(),
        Length(max=20, message='Student ID start must be less than 20 characters')
    ])
    student_id_end = StringField('Student ID End', validators=[
        Optional(),
        Length(max=20, message='Student ID end must be less than 20 characters')
    ])
    student_id_pattern = StringField('Student ID Pattern', validators=[
        Optional(),
        Length(max=50, message='Student ID pattern must be less than 50 characters')
    ])

class FacultyUnavailabilityForm(FlaskForm):
    """Faculty unavailability form."""
    start_time = DateTimeLocalField('Start Date & Time', validators=[
        DataRequired(message='Start time is required')
    ])
    end_time = DateTimeLocalField('End Date & Time', validators=[
        DataRequired(message='End time is required')
    ])
    reason = SelectField('Reason', choices=[
        ('personal_leave', 'Personal Leave'),
        ('conference', 'Conference'),
        ('meeting', 'Meeting'),
        ('other_commitment', 'Other Commitment'),
        ('sick_leave', 'Sick Leave'),
        ('emergency', 'Emergency')
    ], validators=[DataRequired()])
    priority = SelectField('Priority', choices=[
        ('1', 'Low'),
        ('2', 'Medium'),
        ('3', 'High'),
        ('4', 'Critical')
    ], coerce=int, validators=[DataRequired()])
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=500, message='Description must be less than 500 characters')
    ])
    
    def validate_end_time(self, end_time):
        """Validate that end time is after start time."""
        if self.start_time.data and end_time.data:
            if end_time.data <= self.start_time.data:
                raise ValidationError('End time must be after start time.')

class AttendanceForm(FlaskForm):
    """Attendance marking form."""
    course_id = SelectField('Course', coerce=str, validators=[DataRequired()])
    date = DateTimeLocalField('Date', validators=[DataRequired()])
    
class NoteUploadForm(FlaskForm):
    """Note upload form."""
    title = StringField('Title', validators=[
        DataRequired(message='Title is required'),
        Length(min=3, max=200, message='Title must be between 3 and 200 characters')
    ])
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=1000, message='Description must be less than 1000 characters')
    ])
    course_id = SelectField('Course', coerce=str, validators=[DataRequired()])
    file = FileField('File', validators=[
        DataRequired(message='File is required'),
        FileAllowed(['pdf', 'doc', 'docx', 'txt', 'ppt', 'pptx'], 
                   'Only PDF, Word, Text, and PowerPoint files are allowed')
    ])

class TimetableGenerationForm(FlaskForm):
    """Timetable generation configuration form."""
    max_time = IntegerField('Maximum Generation Time (seconds)', validators=[
        DataRequired(message='Maximum generation time is required'),
        NumberRange(min=30, max=1800, message='Generation time must be between 30 and 1800 seconds')
    ], default=300)
    optimize = BooleanField('Enable Optimization', default=True)
    solver_type = SelectField('Algorithm', choices=[
        ('greedy', 'Greedy (Fast)'),
        ('csp_backtracking', 'CSP Backtracking (Thorough)'),
        ('hybrid', 'Hybrid (Balanced)')
    ], validators=[DataRequired()], default='hybrid')
    selected_batches = SelectMultipleField('Batches', coerce=str, validators=[DataRequired()])
    include_breaks = BooleanField('Include Break Times', default=True)
    allow_back_to_back = BooleanField('Allow Back-to-Back Classes', default=True)

class ProfileUpdateForm(FlaskForm):
    """User profile update form."""
    full_name = StringField('Full Name', validators=[
        DataRequired(message='Full name is required'),
        Length(min=2, max=100, message='Full name must be between 2 and 100 characters')
    ])
    email = EmailField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    current_password = PasswordField('Current Password', validators=[
        Optional()
    ])
    new_password = PasswordField('New Password', validators=[
        Optional(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_new_password = PasswordField('Confirm New Password', validators=[
        EqualTo('new_password', message='Passwords must match')
    ])
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
    
    def validate_email(self, email):
        """Validate email uniqueness (excluding current user)."""
        if email.data != self.user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email already registered. Please use a different email.')
    
    def validate_current_password(self, current_password):
        """Validate current password if new password is provided."""
        if self.new_password.data and not current_password.data:
            raise ValidationError('Current password is required to set a new password.')
        if current_password.data and not self.user.check_password(current_password.data):
            raise ValidationError('Current password is incorrect.')

def validate_time_format(form, field):
    """Custom validator for time format."""
    time_pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
    if not re.match(time_pattern, field.data):
        raise ValidationError('Please enter time in HH:MM format (24-hour).')

def validate_future_date(form, field):
    """Custom validator to ensure date is in the future."""
    from datetime import datetime
    if field.data <= datetime.now():
        raise ValidationError('Date must be in the future.')

def validate_positive_number(form, field):
    """Custom validator for positive numbers."""
    if field.data <= 0:
        raise ValidationError('Value must be a positive number.')