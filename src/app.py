"""
Flask web application for the AI-powered timetable generator.
Includes user authentication and web interface for timetable generation.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from datetime import datetime, timedelta
import uuid
from functools import wraps

from timetable_generator import TimetableGenerator, SolverType
from enhanced_timetable_generator import (
    EnhancedTimetableGenerator, FacultyUnavailability, UnavailabilityReason
)
from models.data_models import (
    Course, Faculty, Classroom, TimeSlot, DayOfWeek, CourseType
)


app = Flask(__name__, template_folder='../templates', static_folder='../static')

# Load configuration
import os
config_name = os.environ.get('FLASK_CONFIG') or 'default'
from config import config
app.config.from_object(config[config_name])

# Security headers
from flask import make_response

@app.after_request
def after_request(response):
    """Add security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; font-src 'self' cdn.jsdelivr.net cdnjs.cloudflare.com; img-src 'self' data:;"
    return response

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access the timetable generator.'


# Simple user model (in production, use a proper database)
class User(UserMixin):
    def __init__(self, user_id, username, email, password_hash, role='user', 
                 full_name='', student_id='', department='', semester=''):
        self.id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.full_name = full_name
        self.student_id = student_id
        self.department = department
        self.semester = semester


# Mock user database (in production, use a proper database)
users_db = {
    '1': User('1', 'admin', 'admin@college.edu', 
              generate_password_hash('admin123'), 'admin',
              full_name='System Administrator'),
    '2': User('2', 'faculty', 'faculty@college.edu', 
              generate_password_hash('faculty123'), 'faculty',
              full_name='Dr. Faculty Member', department='Computer Science'),
    '3': User('3', 'student1', 'john.doe@student.edu',
              generate_password_hash('student123'), 'student',
              full_name='John Doe', student_id='CS2024001', 
              department='Computer Science', semester='Fall 2024'),
    '4': User('4', 'student2', 'jane.smith@student.edu',
              generate_password_hash('student123'), 'student',
              full_name='Jane Smith', student_id='CS2024015',
              department='Computer Science', semester='Fall 2024'),
    '5': User('5', 'student3', 'mike.wilson@student.edu',
              generate_password_hash('student123'), 'student',
              full_name='Mike Wilson', student_id='MATH2024025',
              department='Mathematics', semester='Fall 2024')
}

# Global timetable generator instances
timetable_gen = TimetableGenerator()
enhanced_timetable_gen = EnhancedTimetableGenerator()

# Initialize sample batches if session is empty
def initialize_sample_batches():
    """Initialize sample batches for demonstration."""
    if 'batches' not in session or not session['batches']:
        sample_batches = [
            {
                'id': str(uuid.uuid4()),
                'name': 'CS-A-2024',
                'department': 'Computer Science',
                'semester': '3rd Semester',
                'year': 2024,
                'section': 'A',
                'student_count': 50,
                'max_classes_per_day': 6,
                'subjects': [],
                'student_id_start': 'CS2024001',
                'student_id_end': 'CS2024050',
                'student_id_pattern': 'CS2024{###}'
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'MATH-A-2024',
                'department': 'Mathematics',
                'semester': '3rd Semester',
                'year': 2024,
                'section': 'A',
                'student_count': 30,
                'max_classes_per_day': 6,
                'subjects': [],
                'student_id_start': 'MATH2024001',
                'student_id_end': 'MATH2024030',
                'student_id_pattern': 'MATH2024{###}'
            }
        ]
        session['batches'] = sample_batches
        session.permanent = True

# Role-based access control decorators
def require_role(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                flash('Access denied. Insufficient permissions.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_roles(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                flash('Access denied. Insufficient permissions.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@login_manager.user_loader
def load_user(user_id):
    return users_db.get(user_id)


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Find user by username
        user = None
        for u in users_db.values():
            if u.username == username:
                user = u
                break
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=request.form.get('remember', False))
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            role = request.form['role']
            full_name = request.form['full_name']
            
            # Validation
            if password != confirm_password:
                flash('Passwords do not match', 'error')
                return render_template('register.html')
            
            # Check if username or email already exists
            for user in users_db.values():
                if user.username == username:
                    flash('Username already exists', 'error')
                    return render_template('register.html')
                if user.email == email:
                    flash('Email already exists', 'error')
                    return render_template('register.html')
            
            # Create new user
            user_id = str(len(users_db) + 1)
            
            # Additional fields based on role
            student_id = request.form.get('student_id', '') if role == 'student' else ''
            department = request.form.get('department', '')
            semester = request.form.get('semester', '') if role == 'student' else ''
            
            new_user = User(
                user_id=user_id,
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                role=role,
                full_name=full_name,
                student_id=student_id,
                department=department,
                semester=semester
            )
            
            users_db[user_id] = new_user
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'error')
    
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    # Redirect based on user role
    if current_user.role == 'student':
        return redirect(url_for('student_portal'))
    elif current_user.role == 'faculty':
        return redirect(url_for('faculty_portal'))
    else:
        return render_template('dashboard.html', user=current_user)


@app.route('/student_portal')
@login_required
@require_role('student')
def student_portal():
    # Initialize sample batches for demo
    initialize_sample_batches()
    
    # Find the student's batch based on their student ID
    student_batch = find_student_batch(current_user.student_id)
    
    if not student_batch:
        flash('No batch found for your student ID. Please contact administration.', 'warning')
        student_courses = []
        student_schedule = []
        batch_info = None
    else:
        # Get courses assigned to the student's batch
        student_courses = []
        all_courses = session.get('courses', [])
        
        # Filter courses by those assigned to the student's batch
        for course_data in all_courses:
            assigned_batches = course_data.get('assigned_batches', [])
            if student_batch['id'] in assigned_batches:
                student_courses.append(course_data)
        
        # Get generated schedule for the student's batch only
        student_schedule = get_student_schedule(current_user.student_id, student_batch)
        batch_info = student_batch
    
    return render_template('student_portal.html', 
                         user=current_user, 
                         courses=student_courses,
                         schedule=student_schedule,
                         batch=batch_info)


@app.route('/faculty_portal')
@login_required
@require_role('faculty')
def faculty_portal():
    # Get faculty's courses and availability
    faculty_courses = []
    all_courses = session.get('courses', [])
    
    # Filter courses by faculty's department or assigned to them
    for course_data in all_courses:
        if (course_data.get('department') == current_user.department or 
            course_data.get('faculty_id') == current_user.id):
            faculty_courses.append(course_data)
    
    # Get faculty availability status
    faculty_availability = session.get(f'faculty_availability_{current_user.id}', {})
    
    return render_template('faculty_portal.html', 
                         user=current_user, 
                         courses=faculty_courses,
                         availability=faculty_availability)


@app.route('/update_faculty_availability', methods=['POST'])
@login_required
@require_role('faculty')
def update_faculty_availability():
    try:
        course_id = request.form['course_id']
        availability = request.form['availability']  # 'available', 'unavailable', 'preferred'
        
        # Store faculty availability in session
        faculty_key = f'faculty_availability_{current_user.id}'
        faculty_availability = session.get(faculty_key, {})
        faculty_availability[course_id] = availability
        session[faculty_key] = faculty_availability
        session.permanent = True
        
        flash('Availability updated successfully', 'success')
    except Exception as e:
        flash(f'Error updating availability: {str(e)}', 'error')
    
    return redirect(url_for('faculty_portal'))


@app.route('/courses')
@login_required
@require_role('admin')
def courses():
    # Get courses from session or initialize empty list
    courses = session.get('courses', [])
    return render_template('courses.html', user=current_user, courses=courses)


def find_student_batch(student_id):
    """Find which batch a student belongs to based on their student ID."""
    batches = session.get('batches', [])
    
    for batch_data in batches:
        # Create a temporary Batch object to use the belongs_to_batch method
        from models.data_models import Batch
        batch = Batch(
            id=batch_data['id'],
            name=batch_data['name'],
            department=batch_data['department'],
            semester=batch_data['semester'],
            year=batch_data['year'],
            section=batch_data['section'],
            student_count=batch_data['student_count'],
            max_classes_per_day=batch_data.get('max_classes_per_day', 6),
            subjects=batch_data.get('subjects', []),
            student_id_start=batch_data.get('student_id_start', ''),
            student_id_end=batch_data.get('student_id_end', ''),
            student_id_pattern=batch_data.get('student_id_pattern', '')
        )
        
        if batch.belongs_to_batch(student_id):
            return batch_data
    
    return None

def get_student_schedule(student_id, student_batch=None):
    """Get student's timetable from the generated schedule."""
    # If no batch is provided, try to find it
    if student_batch is None:
        student_batch = find_student_batch(student_id)
    
    if not student_batch:
        return []
    
    # Get the generated schedule from session
    generated_schedule = session.get('generated_schedule', {})
    
    if not generated_schedule.get('schedule'):
        # Return sample schedule for demo purposes
        return [
            {
                'course_code': 'CS101',
                'course_name': 'Introduction to Programming',
                'faculty': 'Dr. Smith',
                'classroom': 'Lab-01',
                'day': 'Monday',
                'time': '09:00-10:30',
                'batch': student_batch['name']
            },
            {
                'course_code': 'MATH101',
                'course_name': 'Calculus I',
                'faculty': 'Prof. Johnson',
                'classroom': 'LH-01',
                'day': 'Tuesday',
                'time': '10:30-12:00',
                'batch': student_batch['name']
            }
        ]
    
    # Filter schedule entries for this specific batch
    student_schedule = []
    for entry in generated_schedule['schedule']:
        # Check if this schedule entry is for the student's batch
        if entry.get('batch_id') == student_batch['id']:
            student_schedule.append(entry)
    
    return student_schedule


@app.route('/add_course', methods=['POST'])
@login_required
@require_role('admin')
def add_course():
    try:
        # Get selected batches
        selected_batches = request.form.getlist('selected_batches')
        
        course_data = {
            'id': str(uuid.uuid4()),
            'name': request.form['name'],
            'code': request.form['code'],
            'department': request.form['department'],
            'semester': request.form['semester'],
            'credits': int(request.form['credits']),
            'course_type': request.form['course_type'],
            'enrolled_students': int(request.form['enrolled_students']),
            'duration': int(request.form['duration']),
            'sessions_per_week': int(request.form['sessions_per_week']),
            'faculty_id': request.form.get('faculty_id', ''),
            'required_equipment': request.form.get('required_equipment', '').split(',') if request.form.get('required_equipment') else [],
            # Enhanced parameters
            'assigned_batches': selected_batches,
            'sessions_per_day': int(request.form.get('sessions_per_day', 1)),
            'is_core_subject': request.form.get('is_core_subject', 'true') == 'true',
            'requires_consecutive_sessions': 'requires_consecutive_sessions' in request.form,
            'minimum_gap_between_sessions': int(request.form.get('minimum_gap_between_sessions', 0)),
            'preferred_time_slots': [],
            'cannot_be_scheduled_with': []
        }
        
        courses = session.get('courses', [])
        courses.append(course_data)
        session['courses'] = courses
        session.permanent = True
        
        flash('Course added successfully', 'success')
    except Exception as e:
        flash(f'Error adding course: {str(e)}', 'error')
    
    return redirect(url_for('courses'))


@app.route('/faculty')
@login_required
@require_role('admin')
def faculty():
    faculty_list = session.get('faculty', [])
    return render_template('faculty.html', user=current_user, faculty=faculty_list)


@app.route('/add_faculty', methods=['POST'])
@login_required
@require_role('admin')
def add_faculty():
    try:
        # Parse available slots
        available_slots = []
        for i in range(10):  # Support up to 10 time slots
            day = request.form.get(f'day_{i}')
            start_time = request.form.get(f'start_time_{i}')
            end_time = request.form.get(f'end_time_{i}')
            
            if day and start_time and end_time:
                available_slots.append({
                    'day': day,
                    'start_time': start_time,
                    'end_time': end_time
                })
        
        faculty_data = {
            'id': str(uuid.uuid4()),
            'name': request.form['name'],
            'email': request.form['email'],
            'department': request.form['department'],
            'max_hours_per_week': int(request.form.get('max_hours_per_week', 20)),
            'available_slots': available_slots
        }
        
        faculty_list = session.get('faculty', [])
        faculty_list.append(faculty_data)
        session['faculty'] = faculty_list
        session.permanent = True
        
        flash('Faculty added successfully', 'success')
    except Exception as e:
        flash(f'Error adding faculty: {str(e)}', 'error')
    
    return redirect(url_for('faculty'))


@app.route('/classrooms')
@login_required
@require_role('admin')
def classrooms():
    classrooms_list = session.get('classrooms', [])
    return render_template('classrooms.html', user=current_user, classrooms=classrooms_list)


@app.route('/add_classroom', methods=['POST'])
@login_required
@require_role('admin')
def add_classroom():
    try:
        classroom_data = {
            'id': str(uuid.uuid4()),
            'name': request.form['name'],
            'capacity': int(request.form['capacity']),
            'room_type': request.form['room_type'],
            'location': request.form.get('location', ''),
            'equipment': request.form.get('equipment', '').split(',') if request.form.get('equipment') else []
        }
        
        classrooms_list = session.get('classrooms', [])
        classrooms_list.append(classroom_data)
        session['classrooms'] = classrooms_list
        session.permanent = True
        
        flash('Classroom added successfully', 'success')
    except Exception as e:
        flash(f'Error adding classroom: {str(e)}', 'error')
    
    return redirect(url_for('classrooms'))


@app.route('/generate_timetable')
@login_required
@require_role('admin')
def generate_timetable():
    return render_template('generate_timetable.html', user=current_user)


@app.route('/api/generate', methods=['POST'])
@login_required
@require_role('admin')
def api_generate_timetable():
    try:
        # Get configuration from request
        config = request.get_json()
        max_time = int(config.get('max_time', 300))
        optimize = config.get('optimize', True)
        selected_courses = config.get('selected_courses', [])
        selected_faculty = config.get('selected_faculty', [])
        
        # Intelligent algorithm selection based on complexity
        solver_type = choose_optimal_algorithm(config, session)
        
        # Convert session data to model objects
        all_courses_data = session.get('courses', [])
        all_faculty_data = session.get('faculty', [])
        classrooms_data = session.get('classrooms', [])
        
        # Filter courses and faculty based on selection
        if selected_courses:
            courses_data = [c for c in all_courses_data if c['id'] in selected_courses]
        else:
            courses_data = all_courses_data
            
        if selected_faculty:
            faculty_data = [f for f in all_faculty_data if f['id'] in selected_faculty]
        else:
            faculty_data = all_faculty_data
        
        if not courses_data:
            return jsonify({'error': 'No courses defined'}), 400
        
        if not faculty_data:
            return jsonify({'error': 'No faculty defined'}), 400
            
        if not classrooms_data:
            return jsonify({'error': 'No classrooms defined'}), 400
        
        # Create model objects
        courses = []
        for course_data in courses_data:
            course = Course(
                id=course_data['id'],
                name=course_data['name'],
                code=course_data['code'],
                department=course_data['department'],
                semester=course_data['semester'],
                credits=course_data['credits'],
                course_type=CourseType(course_data['course_type']),
                enrolled_students=course_data['enrolled_students'],
                duration=course_data['duration'],
                sessions_per_week=course_data['sessions_per_week'],
                faculty_id=course_data.get('faculty_id', ''),
                required_equipment=course_data.get('required_equipment', [])
            )
            courses.append(course)
        
        faculty = []
        for faculty_item in faculty_data:
            # Convert available slots
            available_slots = []
            for slot_data in faculty_item.get('available_slots', []):
                time_slot = TimeSlot(
                    id=str(uuid.uuid4()),
                    day=DayOfWeek(slot_data['day']),
                    start_time=slot_data['start_time'],
                    end_time=slot_data['end_time'],
                    duration=calculate_duration(slot_data['start_time'], slot_data['end_time'])
                )
                available_slots.append(time_slot)
            
            faculty_member = Faculty(
                id=faculty_item['id'],
                name=faculty_item['name'],
                email=faculty_item['email'],
                department=faculty_item['department'],
                available_slots=available_slots,
                max_hours_per_week=faculty_item.get('max_hours_per_week', 20)
            )
            faculty.append(faculty_member)
        
        classrooms = []
        for classroom_data in classrooms_data:
            classroom = Classroom(
                id=classroom_data['id'],
                name=classroom_data['name'],
                capacity=classroom_data['capacity'],
                room_type=classroom_data['room_type'],
                equipment=classroom_data.get('equipment', []),
                location=classroom_data.get('location', '')
            )
            classrooms.append(classroom)
        
        # Generate default time slots if not provided
        time_slots = generate_default_time_slots()
        
        # Set data and generate timetable
        timetable_gen.set_data(courses, faculty, classrooms, time_slots)
        schedule = timetable_gen.generate_timetable(solver_type, max_time, optimize)
        
        if schedule:
            # Export schedule and analysis
            schedule_dict = timetable_gen.export_schedule_to_dict(schedule)
            analysis = timetable_gen.analyze_schedule(schedule)
            
            return jsonify({
                'success': True,
                'schedule': schedule_dict,
                'analysis': analysis,
                'statistics': timetable_gen.get_generation_statistics()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate a valid timetable',
                'statistics': timetable_gen.get_generation_statistics()
            })
    
    except Exception as e:
        return jsonify({'error': f'Error generating timetable: {str(e)}'}), 500


@app.route('/view_schedule')
@login_required
def view_schedule():
    return render_template('view_schedule.html', user=current_user)


@app.route('/api/clear_data', methods=['POST'])
@login_required
def clear_data():
    """Clear all session data."""
    session.pop('courses', None)
    session.pop('faculty', None)
    session.pop('classrooms', None)
    return jsonify({'success': True})


@app.route('/api/clear_faculty', methods=['POST'])
@login_required
@require_role('admin')
def clear_faculty_data():
    """Clear all faculty data from session."""
    try:
        session.pop('faculty', None)
        # Also clear any faculty-related session data
        keys_to_remove = []
        for key in session.keys():
            if key.startswith('faculty_availability_'):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            session.pop(key, None)
        
        session.permanent = True
        flash('All faculty data has been cleared successfully', 'success')
        return jsonify({'success': True, 'message': 'All faculty data cleared'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/clear_faculty_direct')
@login_required
@require_role('admin')
def clear_faculty_direct():
    """Direct route to clear all faculty data."""
    try:
        session.pop('faculty', None)
        # Also clear any faculty-related session data
        keys_to_remove = []
        for key in list(session.keys()):
            if key.startswith('faculty_availability_'):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            session.pop(key, None)
        
        session.permanent = True
        flash('All faculty data has been cleared successfully!', 'success')
        return redirect(url_for('faculty'))
    except Exception as e:
        flash(f'Error clearing faculty data: {str(e)}', 'error')
        return redirect(url_for('faculty'))


@app.route('/api/courses', methods=['GET'])
@login_required
def api_get_courses():
    """Get all courses for selection."""
    courses = session.get('courses', [])
    return jsonify({'courses': courses})


@app.route('/api/faculty', methods=['GET'])
@login_required
def api_get_faculty():
    """Get all faculty for selection."""
    faculty = session.get('faculty', [])
    return jsonify({'faculty': faculty})


@app.route('/batches')
@login_required
@require_role('admin')
def batches():
    """Display batch management page."""
    batches_list = session.get('batches', [])
    return render_template('batches.html', user=current_user, batches=batches_list)


@app.route('/add_batch', methods=['POST'])
@login_required
@require_role('admin')
def add_batch():
    """Add a new batch."""
    try:
        batch_data = {
            'id': str(uuid.uuid4()),
            'name': request.form['name'],
            'department': request.form['department'],
            'semester': request.form['semester'],
            'year': int(request.form['year']),
            'section': request.form['section'].upper(),
            'student_count': int(request.form['student_count']),
            'max_classes_per_day': int(request.form.get('max_classes_per_day', 6)),
            'subjects': [],  # Will be populated when courses are assigned
            # Student ID range fields
            'student_id_start': request.form.get('student_id_start', ''),
            'student_id_end': request.form.get('student_id_end', ''),
            'student_id_pattern': request.form.get('student_id_pattern', '')
        }
        
        batches_list = session.get('batches', [])
        
        # Check for duplicate batch names
        for existing_batch in batches_list:
            if existing_batch['name'] == batch_data['name']:
                flash('A batch with this name already exists', 'error')
                return redirect(url_for('batches'))
        
        batches_list.append(batch_data)
        session['batches'] = batches_list
        session.permanent = True
        
        flash(f'Batch "{batch_data["name"]}" added successfully', 'success')
        
    except Exception as e:
        flash(f'Error adding batch: {str(e)}', 'error')
    
    return redirect(url_for('batches'))


@app.route('/api/batches', methods=['GET'])
@login_required
def api_get_batches():
    """Get all batches for selection."""
    batches = session.get('batches', [])
    return jsonify({'batches': batches})


def choose_optimal_algorithm(config, session_data):
    """Intelligently choose the best algorithm based on problem complexity."""
    # Get data sizes
    courses_count = len(session_data.get('courses', []))
    faculty_count = len(session_data.get('faculty', []))
    classrooms_count = len(session_data.get('classrooms', []))
    selected_courses_count = len(config.get('selected_courses', []))
    selected_faculty_count = len(config.get('selected_faculty', []))
    
    # Calculate effective complexity
    if selected_courses_count > 0:
        courses_count = selected_courses_count
    if selected_faculty_count > 0:
        faculty_count = selected_faculty_count
    
    # Calculate complexity score
    complexity_score = courses_count * faculty_count * classrooms_count
    
    # Decision logic for algorithm selection
    if complexity_score <= 100:  # Small problem
        # For small problems, use greedy for speed
        return SolverType('greedy')
    elif complexity_score <= 1000:  # Medium problem
        # For medium problems, use hybrid for balance
        return SolverType('hybrid')
    else:  # Large problem
        # For large problems, use CSP for thoroughness
        return SolverType('csp_backtracking')


def calculate_duration(start_time: str, end_time: str) -> int:
    """Calculate duration in minutes between two time strings."""
    start_hour, start_min = map(int, start_time.split(':'))
    end_hour, end_min = map(int, end_time.split(':'))
    
    start_minutes = start_hour * 60 + start_min
    end_minutes = end_hour * 60 + end_min
    
    return end_minutes - start_minutes


def prepare_timetable_data(selected_batches):
    """Prepare course, faculty, classroom and time slot data from batches."""
    courses = []
    faculty = []
    classrooms = []
    time_slots = generate_default_time_slots()
    
    # Generate sample faculty
    faculty_data = [
        Faculty("F001", "Dr. Alice Smith", "alice.smith@college.edu", "Computer Science", 
                time_slots, 40, subjects_expertise=["algorithms", "data_structures"]),
        Faculty("F002", "Prof. Bob Johnson", "bob.johnson@college.edu", "Computer Science", 
                time_slots, 35, subjects_expertise=["databases", "software_engineering"]),
        Faculty("F003", "Dr. Carol Davis", "carol.davis@college.edu", "Mathematics", 
                time_slots, 30, subjects_expertise=["calculus", "linear_algebra"]),
        Faculty("F004", "Prof. David Wilson", "david.wilson@college.edu", "Computer Science", 
                time_slots, 45, subjects_expertise=["machine_learning", "ai"]),
        Faculty("F005", "Dr. Eve Brown", "eve.brown@college.edu", "Mathematics", 
                time_slots, 35, subjects_expertise=["statistics", "probability"])
    ]
    faculty.extend(faculty_data)
    
    # Generate sample classrooms
    classroom_data = [
        Classroom("R101", "Computer Lab 1", 40, "computer_lab", ["projector", "computers", "whiteboard"]),
        Classroom("R102", "Computer Lab 2", 35, "computer_lab", ["projector", "computers", "whiteboard"]),
        Classroom("R201", "Lecture Hall A", 80, "lecture_hall", ["projector", "microphone", "whiteboard"]),
        Classroom("R202", "Lecture Hall B", 60, "lecture_hall", ["projector", "microphone", "whiteboard"]),
        Classroom("R301", "Seminar Room", 25, "seminar_room", ["projector", "whiteboard"])
    ]
    classrooms.extend(classroom_data)
    
    # Generate courses from batches
    for batch in selected_batches:
        department = batch['department']
        student_count = batch['student_count']
        
        if department == 'Computer Science':
            batch_courses = [
                Course(
                    id=f"CS101_{batch['id'][:8]}",
                    name="Data Structures",
                    code="CS101",
                    department=department,
                    semester="Fall 2024",
                    credits=4,
                    course_type=CourseType.LECTURE,
                    enrolled_students=student_count,
                    duration=90,
                    sessions_per_week=2,
                    faculty_id="F001"
                ),
                Course(
                    id=f"CS201_{batch['id'][:8]}",
                    name="Database Systems",
                    code="CS201",
                    department=department,
                    semester="Fall 2024",
                    credits=3,
                    course_type=CourseType.LECTURE,
                    enrolled_students=student_count,
                    duration=90,
                    sessions_per_week=2,
                    faculty_id="F002"
                ),
                Course(
                    id=f"CS301_{batch['id'][:8]}",
                    name="Machine Learning",
                    code="CS301",
                    department=department,
                    semester="Fall 2024",
                    credits=4,
                    course_type=CourseType.LECTURE,
                    enrolled_students=student_count,
                    duration=90,
                    sessions_per_week=2,
                    faculty_id="F004"
                )
            ]
        elif department == 'Mathematics':
            batch_courses = [
                Course(
                    id=f"MATH101_{batch['id'][:8]}",
                    name="Calculus I",
                    code="MATH101",
                    department=department,
                    semester="Fall 2024",
                    credits=3,
                    course_type=CourseType.LECTURE,
                    enrolled_students=student_count,
                    duration=90,
                    sessions_per_week=3,
                    faculty_id="F003"
                ),
                Course(
                    id=f"MATH201_{batch['id'][:8]}",
                    name="Statistics",
                    code="MATH201",
                    department=department,
                    semester="Fall 2024",
                    credits=3,
                    course_type=CourseType.LECTURE,
                    enrolled_students=student_count,
                    duration=90,
                    sessions_per_week=2,
                    faculty_id="F005"
                )
            ]
        else:
            # Default courses for other departments
            batch_courses = [
                Course(
                    id=f"GEN101_{batch['id'][:8]}",
                    name="General Course 1",
                    code="GEN101",
                    department=department,
                    semester="Fall 2024",
                    credits=3,
                    course_type=CourseType.LECTURE,
                    enrolled_students=student_count,
                    duration=90,
                    sessions_per_week=2,
                    faculty_id="F001"
                ),
                Course(
                    id=f"GEN102_{batch['id'][:8]}",
                    name="General Course 2",
                    code="GEN102",
                    department=department,
                    semester="Fall 2024",
                    credits=3,
                    course_type=CourseType.LECTURE,
                    enrolled_students=student_count,
                    duration=90,
                    sessions_per_week=2,
                    faculty_id="F002"
                )
            ]
        
        courses.extend(batch_courses)
    
    return courses, faculty, classrooms, time_slots


def generate_default_time_slots() -> list:
    """Generate default time slots for a typical college schedule."""
    time_slots = []
    days = [DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY, 
            DayOfWeek.THURSDAY, DayOfWeek.FRIDAY]
    
    # Morning slots
    slots = [
        ("09:00", "10:30", 90),
        ("10:30", "12:00", 90),
        ("12:00", "13:30", 90),
        ("13:30", "15:00", 90),
        ("15:00", "16:30", 90),
        ("16:30", "18:00", 90)
    ]
    
    for day in days:
        for start_time, end_time, duration in slots:
            time_slot = TimeSlot(
                id=str(uuid.uuid4()),
                day=day,
                start_time=start_time,
                end_time=end_time,
                duration=duration
            )
            time_slots.append(time_slot)
    
    return time_slots


# Student Attendance Routes
@app.route('/student/attendance')
@login_required
@require_role('student')
def student_attendance():
    """Student attendance tracking page."""
    initialize_sample_batches()
    student_batch = find_student_batch(current_user.student_id)
    
    # Sample attendance data
    attendance_data = get_student_attendance_data(current_user.student_id, student_batch)
    
    return render_template('student_attendance.html', 
                         user=current_user,
                         batch=student_batch,
                         attendance=attendance_data)

@app.route('/student/notes')
@login_required
@require_role('student')
def student_notes():
    """Student notes download page."""
    initialize_sample_batches()
    student_batch = find_student_batch(current_user.student_id)
    
    # Get available notes for student's courses
    available_notes = get_student_notes_data(current_user.student_id, student_batch)
    
    return render_template('student_notes.html',
                         user=current_user,
                         batch=student_batch,
                         notes=available_notes)

# Faculty Attendance Routes
@app.route('/faculty/attendance')
@login_required
@require_role('faculty')
def faculty_attendance():
    """Faculty attendance management page."""
    # Get faculty's courses and students
    faculty_courses = get_faculty_courses(current_user.id)
    attendance_data = get_faculty_attendance_data(current_user.id)
    
    return render_template('faculty_attendance.html',
                         user=current_user,
                         courses=faculty_courses,
                         attendance=attendance_data)

@app.route('/faculty/notes')
@login_required
@require_role('faculty')
def faculty_notes():
    """Faculty notes management page."""
    # Get faculty's courses and uploaded notes
    faculty_courses = get_faculty_courses(current_user.id)
    uploaded_notes = get_faculty_notes_data(current_user.id)
    
    return render_template('faculty_notes.html',
                         user=current_user,
                         courses=faculty_courses,
                         notes=uploaded_notes)

@app.route('/faculty/unavailability')
@login_required
@require_roles('admin', 'faculty')
def faculty_unavailability():
    """Faculty unavailability management page."""
    return render_template('faculty_unavailability.html')

# API Routes for attendance and notes
@app.route('/api/attendance/mark', methods=['POST'])
@login_required
@require_role('faculty')
def mark_attendance():
    """Mark attendance for students."""
    try:
        data = request.get_json()
        course_id = data.get('course_id')
        date = data.get('date')
        attendance_records = data.get('attendance')
        
        # Store attendance in session (in production, use database)
        attendance_key = f'attendance_{course_id}_{date}'
        session[attendance_key] = attendance_records
        session.permanent = True
        
        return jsonify({'success': True, 'message': 'Attendance marked successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/notes/upload', methods=['POST'])
@login_required
@require_role('faculty')
def upload_notes():
    """Upload notes for a course."""
    try:
        # In a real app, handle file upload properly
        course_id = request.form.get('course_id')
        note_title = request.form.get('note_title')
        note_description = request.form.get('note_description')
        
        # Store notes metadata in session (in production, use database and file storage)
        notes_key = f'notes_{current_user.id}'
        faculty_notes = session.get(notes_key, [])
        
        new_note = {
            'id': str(uuid.uuid4()),
            'course_id': course_id,
            'title': note_title,
            'description': note_description,
            'uploaded_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'faculty_id': current_user.id,
            'file_name': f'{note_title}.pdf'  # Simulated
        }
        
        faculty_notes.append(new_note)
        session[notes_key] = faculty_notes
        session.permanent = True
        
        return jsonify({'success': True, 'message': 'Notes uploaded successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/notes/download/<note_id>')
@login_required
def download_note(note_id):
    """Download a specific note file."""
    try:
        # In production, serve actual files from secure storage
        # For demo, return a simulated response
        return jsonify({
            'success': True,
            'message': 'File download initiated',
            'note_id': note_id,
            'download_url': f'/static/sample_notes/{note_id}.pdf'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/batch/students', methods=['POST'])
@login_required
@require_role('faculty')
def get_batch_students_api():
    """Get students for a specific batch."""
    try:
        data = request.get_json()
        batch_id = data.get('batch_id')
        batch_name = data.get('batch_name')
        
        if not batch_id or not batch_name:
            return jsonify({'success': False, 'error': 'Batch ID and name are required'})
        
        students = get_batch_students(batch_id, batch_name)
        
        return jsonify({
            'success': True,
            'students': students,
            'batch_name': batch_name,
            'student_count': len(students)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/faculty/unavailability', methods=['POST'])
@login_required
@require_roles('admin', 'faculty')
def add_faculty_unavailability():
    """Add faculty unavailability period."""
    try:
        data = request.get_json()
        faculty_id = data.get('faculty_id')
        start_time = data.get('start_time')  # ISO format datetime string
        end_time = data.get('end_time')      # ISO format datetime string
        reason = data.get('reason')
        priority = data.get('priority', 1)
        
        if not all([faculty_id, start_time, end_time, reason]):
            return jsonify({'success': False, 'error': 'Missing required fields'})
        
        # Parse datetime strings
        from datetime import datetime
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        # Validate reason
        try:
            unavailability_reason = UnavailabilityReason(reason)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid reason'})
        
        # Create unavailability
        unavailability = FacultyUnavailability(
            faculty_id=faculty_id,
            start_time=start_dt,
            end_time=end_dt,
            reason=unavailability_reason,
            priority=int(priority)
        )
        
        # Add to enhanced generator
        enhanced_timetable_gen.add_faculty_unavailability(unavailability)
        
        return jsonify({
            'success': True,
            'message': f'Unavailability added for faculty {faculty_id}',
            'unavailability_id': f'{faculty_id}_{start_time}_{end_time}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/timetable/generate-adaptive', methods=['POST'])
@login_required
@require_role('admin')
def generate_adaptive_timetable():
    """Generate adaptive timetable with faculty unavailability handling."""
    try:
        data = request.get_json()
        batch_ids = data.get('batch_ids', [])
        max_time = data.get('max_time', 300)
        
        if not batch_ids:
            return jsonify({'success': False, 'error': 'No batches selected'})
        
        # Get selected batches
        selected_batches = []
        all_batches = session.get('batches', [])
        
        for batch in all_batches:
            if batch['id'] in batch_ids:
                selected_batches.append(batch)
        
        if not selected_batches:
            return jsonify({'success': False, 'error': 'Selected batches not found'})
        
        # Prepare data for enhanced generator
        courses, faculty, classrooms, time_slots = prepare_timetable_data(selected_batches)
        enhanced_timetable_gen.set_data(courses, faculty, classrooms, time_slots)
        
        # Generate adaptive timetable
        schedule = enhanced_timetable_gen.generate_adaptive_timetable(max_time=max_time)
        
        if schedule:
            # Store in session
            schedule_data = enhanced_timetable_gen.export_schedule_to_dict(schedule)
            session['current_schedule'] = schedule_data
            session['generation_method'] = 'adaptive'
            
            # Get rescheduling report
            rescheduling_report = enhanced_timetable_gen.get_rescheduling_report()
            
            return jsonify({
                'success': True,
                'message': 'Adaptive timetable generated successfully',
                'schedule': schedule_data,
                'rescheduling_report': rescheduling_report,
                'stats': enhanced_timetable_gen.generation_stats
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate adaptive timetable'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/faculty/unavailability/list', methods=['GET'])
@login_required
@require_roles('admin', 'faculty')
def list_faculty_unavailabilities():
    """List all faculty unavailabilities."""
    try:
        unavailabilities = []
        
        for unavail in enhanced_timetable_gen.unavailabilities:
            unavailabilities.append({
                'faculty_id': unavail.faculty_id,
                'start_time': unavail.start_time.isoformat(),
                'end_time': unavail.end_time.isoformat(),
                'reason': unavail.reason.value,
                'priority': unavail.priority
            })
        
        return jsonify({
            'success': True,
            'unavailabilities': unavailabilities,
            'total_count': len(unavailabilities)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/faculty/substitution-matrix', methods=['GET'])
@login_required
@require_roles('admin', 'faculty')
def get_faculty_substitution_matrix():
    """Get faculty substitution possibilities."""
    try:
        return jsonify({
            'success': True,
            'substitution_matrix': enhanced_timetable_gen.faculty_substitution_matrix
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def get_student_attendance_data(student_id, student_batch):
    """Get attendance data for a student."""
    if not student_batch:
        return []
    
    # Sample attendance data
    return [
        {
            'course_code': 'CS101',
            'course_name': 'Introduction to Programming',
            'total_classes': 20,
            'attended': 18,
            'percentage': 90.0,
            'status': 'Good'
        },
        {
            'course_code': 'MATH101',
            'course_name': 'Calculus I',
            'total_classes': 18,
            'attended': 15,
            'percentage': 83.3,
            'status': 'Satisfactory'
        },
        {
            'course_code': 'PHY101',
            'course_name': 'Physics I',
            'total_classes': 16,
            'attended': 12,
            'percentage': 75.0,
            'status': 'Warning'
        }
    ]

def get_student_notes_data(student_id, student_batch):
    """Get available notes for a student."""
    if not student_batch:
        return []
    
    # Sample notes data
    return [
        {
            'id': 'note1',
            'course_code': 'CS101',
            'course_name': 'Introduction to Programming',
            'title': 'Chapter 1: Variables and Data Types',
            'uploaded_date': '2024-01-15',
            'faculty': 'Dr. Smith',
            'file_size': '2.5 MB',
            'format': 'PDF'
        },
        {
            'id': 'note2',
            'course_code': 'CS101',
            'course_name': 'Introduction to Programming',
            'title': 'Chapter 2: Control Structures',
            'uploaded_date': '2024-01-22',
            'faculty': 'Dr. Smith',
            'file_size': '1.8 MB',
            'format': 'PDF'
        },
        {
            'id': 'note3',
            'course_code': 'MATH101',
            'course_name': 'Calculus I',
            'title': 'Limits and Continuity',
            'uploaded_date': '2024-01-20',
            'faculty': 'Prof. Johnson',
            'file_size': '3.2 MB',
            'format': 'PDF'
        }
    ]

def get_faculty_courses(faculty_id):
    """Get courses assigned to a faculty member with batch information."""
    # In production, this would query the database for faculty's courses
    # For now, return sample data with batch details
    return [
        {
            'id': 'cs101',
            'code': 'CS101',
            'name': 'Introduction to Programming',
            'batch_id': 'batch1',
            'batch_name': 'CS-A-2024',
            'department': 'Computer Science',
            'semester': '3rd Semester',
            'students': 45
        },
        {
            'id': 'cs201', 
            'code': 'CS201',
            'name': 'Data Structures',
            'batch_id': 'batch1',
            'batch_name': 'CS-A-2024', 
            'department': 'Computer Science',
            'semester': '5th Semester',
            'students': 38
        },
        {
            'id': 'math101',
            'code': 'MATH101',
            'name': 'Calculus I',
            'batch_id': 'batch2',
            'batch_name': 'MATH-A-2024',
            'department': 'Mathematics',
            'semester': '1st Semester', 
            'students': 30
        }
    ]

def get_faculty_attendance_data(faculty_id):
    """Get attendance data for faculty's courses."""
    return {}

def get_faculty_notes_data(faculty_id):
    """Get uploaded notes by faculty."""
    notes_key = f'notes_{faculty_id}'
    return session.get(notes_key, [])

def get_batch_students(batch_id, batch_name):
    """Get students for a specific batch based on batch configuration."""
    # Initialize sample batches to get batch info
    initialize_sample_batches()
    batches = session.get('batches', [])
    
    # Find the batch configuration
    batch_config = None
    for batch in batches:
        if batch['name'] == batch_name:
            batch_config = batch
            break
    
    if not batch_config:
        # Fallback: generate generic students
        return generate_generic_students(30)
    
    # Generate students based on batch ID range
    students = []
    start_id = batch_config.get('student_id_start', '')
    end_id = batch_config.get('student_id_end', '')
    
    if start_id and end_id:
        # Extract numeric parts
        try:
            prefix = ''.join(c for c in start_id if not c.isdigit())
            start_num = int(''.join(c for c in start_id if c.isdigit()))
            end_num = int(''.join(c for c in end_id if c.isdigit()))
            num_digits = len(''.join(c for c in start_id if c.isdigit()))
            
            # Generate student list
            first_names = ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Emma', 'Alex', 'Lisa', 'Tom', 'Anna', 
                          'Chris', 'Maria', 'James', 'Amy', 'Robert', 'Jessica', 'Daniel', 'Laura', 'Kevin', 'Sophie']
            last_names = ['Smith', 'Johnson', 'Brown', 'Davis', 'Wilson', 'Miller', 'Taylor', 'Anderson', 'Thomas', 'Jackson',
                         'White', 'Harris', 'Martin', 'Garcia', 'Rodriguez', 'Lewis', 'Lee', 'Walker', 'Hall', 'Allen']
            
            for i in range(start_num, min(end_num + 1, start_num + 50)):  # Limit to 50 students max
                student_id = f"{prefix}{str(i).zfill(num_digits)}"
                first_name = first_names[(i - start_num) % len(first_names)]
                last_name = last_names[(i - start_num) % len(last_names)]
                
                students.append({
                    'id': student_id,
                    'name': f"{first_name} {last_name}",
                    'batch': batch_name
                })
        except (ValueError, IndexError):
            # Fallback to generic generation
            return generate_generic_students(batch_config.get('student_count', 30))
    else:
        return generate_generic_students(batch_config.get('student_count', 30))
    
    return students

def generate_generic_students(count):
    """Generate generic student list when batch info is not available."""
    first_names = ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Emma', 'Alex', 'Lisa', 'Tom', 'Anna']
    last_names = ['Smith', 'Johnson', 'Brown', 'Davis', 'Wilson', 'Miller', 'Taylor', 'Anderson', 'Thomas', 'Jackson']
    
    students = []
    for i in range(1, count + 1):
        first_name = first_names[i % len(first_names)]
        last_name = last_names[i % len(last_names)]
        students.append({
            'id': f'STD{str(i).zfill(3)}',
            'name': f"{first_name} {last_name}",
            'batch': 'Generic'
        })
    return students

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8080)
