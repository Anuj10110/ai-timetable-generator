"""
Sample data generator for the AI-powered timetable generator.
Creates sample courses, faculty, classrooms, and time slots for testing.
"""

from models.data_models import (
    Course, Faculty, Classroom, TimeSlot, 
    DayOfWeek, CourseType
)
from timetable_generator import TimetableGenerator, SolverType
import uuid


def generate_sample_time_slots():
    """Generate standard time slots for a college schedule."""
    time_slots = []
    days = [DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY, 
            DayOfWeek.THURSDAY, DayOfWeek.FRIDAY]
    
    # Standard time slots
    slots = [
        ("09:00", "10:30", 90),
        ("10:30", "12:00", 90),
        ("12:00", "13:30", 90),  # Including lunch break slot
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


def generate_sample_classrooms():
    """Generate sample classrooms with different capacities and types."""
    classrooms = []
    
    # Regular lecture halls
    for i in range(1, 6):
        classroom = Classroom(
            id=str(uuid.uuid4()),
            name=f"LH-{i:02d}",
            capacity=80,
            room_type="Regular",
            equipment=["Projector", "Whiteboard", "Sound System"],
            location=f"Main Building - Floor {(i-1)//2 + 1}"
        )
        classrooms.append(classroom)
    
    # Small classrooms
    for i in range(1, 4):
        classroom = Classroom(
            id=str(uuid.uuid4()),
            name=f"CR-{i:02d}",
            capacity=30,
            room_type="Regular",
            equipment=["Projector", "Whiteboard"],
            location=f"Academic Block A - Floor {i}"
        )
        classrooms.append(classroom)
    
    # Computer labs
    for i in range(1, 4):
        classroom = Classroom(
            id=str(uuid.uuid4()),
            name=f"CL-{i:02d}",
            capacity=40,
            room_type="Lab",
            equipment=["Computers", "Projector", "Network", "Software"],
            location=f"Computer Center - Floor {i}"
        )
        classrooms.append(classroom)
    
    # Science labs
    for i, subject in enumerate(["Physics", "Chemistry", "Biology"], 1):
        classroom = Classroom(
            id=str(uuid.uuid4()),
            name=f"{subject[:4]}Lab-{i:02d}",
            capacity=25,
            room_type="Lab",
            equipment=["Lab Equipment", f"{subject} Instruments", "Safety Equipment"],
            location=f"Science Block - Floor {i}"
        )
        classrooms.append(classroom)
    
    return classrooms


def generate_sample_faculty():
    """Generate sample faculty members with availability."""
    faculty = []
    
    # Computer Science Department
    cs_faculty_data = [
        ("Dr. John Smith", "john.smith@college.edu"),
        ("Dr. Sarah Johnson", "sarah.johnson@college.edu"),
        ("Prof. Michael Brown", "michael.brown@college.edu"),
        ("Dr. Lisa Davis", "lisa.davis@college.edu")
    ]
    
    # Mathematics Department
    math_faculty_data = [
        ("Dr. Robert Wilson", "robert.wilson@college.edu"),
        ("Prof. Emily Chen", "emily.chen@college.edu"),
        ("Dr. David Kumar", "david.kumar@college.edu")
    ]
    
    # Physics Department
    physics_faculty_data = [
        ("Dr. James Anderson", "james.anderson@college.edu"),
        ("Prof. Maria Rodriguez", "maria.rodriguez@college.edu")
    ]
    
    # Chemistry Department
    chemistry_faculty_data = [
        ("Dr. Jennifer Lee", "jennifer.lee@college.edu"),
        ("Prof. Thomas White", "thomas.white@college.edu")
    ]
    
    # Biology Department
    biology_faculty_data = [
        ("Dr. Amanda Garcia", "amanda.garcia@college.edu"),
        ("Prof. Steven Martinez", "steven.martinez@college.edu")
    ]
    
    departments = {
        "Computer Science": cs_faculty_data,
        "Mathematics": math_faculty_data,
        "Physics": physics_faculty_data,
        "Chemistry": chemistry_faculty_data,
        "Biology": biology_faculty_data
    }
    
    for department, faculty_data in departments.items():
        for name, email in faculty_data:
            # Generate availability (most faculty available most of the time)
            available_slots = []
            days = [DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY, 
                   DayOfWeek.THURSDAY, DayOfWeek.FRIDAY]
            
            for day in days:
                # Available from 9 AM to 5 PM with some gaps
                morning_slots = [
                    ("09:00", "10:30", 90),
                    ("10:30", "12:00", 90),
                ]
                afternoon_slots = [
                    ("13:30", "15:00", 90),
                    ("15:00", "16:30", 90),
                ]
                
                # Add most slots (simulate some unavailability)
                for slots in [morning_slots, afternoon_slots]:
                    for start_time, end_time, duration in slots:
                        # 85% chance of being available for each slot
                        if hash(f"{name}{day.value}{start_time}") % 100 < 85:
                            time_slot = TimeSlot(
                                id=str(uuid.uuid4()),
                                day=day,
                                start_time=start_time,
                                end_time=end_time,
                                duration=duration
                            )
                            available_slots.append(time_slot)
            
            # Add some preferred slots (morning preference for most faculty)
            preferred_slots = []
            for day in [DayOfWeek.TUESDAY, DayOfWeek.THURSDAY]:
                preferred_slot = TimeSlot(
                    id=str(uuid.uuid4()),
                    day=day,
                    start_time="10:30",
                    end_time="12:00",
                    duration=90
                )
                preferred_slots.append(preferred_slot)
            
            faculty_member = Faculty(
                id=str(uuid.uuid4()),
                name=name,
                email=email,
                department=department,
                available_slots=available_slots,
                max_hours_per_week=18,
                preferred_slots=preferred_slots,
                unavailable_slots=[]  # No specific unavailable slots for sample data
            )
            faculty.append(faculty_member)
    
    return faculty


def generate_sample_courses():
    """Generate sample courses across different departments."""
    courses = []
    faculty_by_dept = {
        "Computer Science": [],
        "Mathematics": [],
        "Physics": [],
        "Chemistry": [],
        "Biology": []
    }
    
    # We'll assign faculty IDs after creating faculty
    # For now, we'll leave faculty_id empty and assign by department
    
    # Computer Science Courses
    cs_courses = [
        ("CS101", "Introduction to Programming", 3, CourseType.LECTURE, 45, 90, 2),
        ("CS101L", "Programming Lab", 1, CourseType.LAB, 25, 180, 1),
        ("CS201", "Data Structures", 3, CourseType.LECTURE, 40, 90, 2),
        ("CS201L", "Data Structures Lab", 1, CourseType.LAB, 20, 180, 1),
        ("CS301", "Database Systems", 3, CourseType.LECTURE, 35, 90, 2),
        ("CS401", "Software Engineering", 3, CourseType.LECTURE, 30, 90, 2),
        ("CS405", "Machine Learning", 3, CourseType.LECTURE, 25, 90, 2)
    ]
    
    # Mathematics Courses
    math_courses = [
        ("MATH101", "Calculus I", 4, CourseType.LECTURE, 60, 90, 3),
        ("MATH102", "Calculus II", 4, CourseType.LECTURE, 55, 90, 3),
        ("MATH201", "Linear Algebra", 3, CourseType.LECTURE, 45, 90, 2),
        ("MATH301", "Differential Equations", 3, CourseType.LECTURE, 35, 90, 2),
        ("MATH401", "Real Analysis", 3, CourseType.LECTURE, 20, 90, 2)
    ]
    
    # Physics Courses
    physics_courses = [
        ("PHYS101", "General Physics I", 4, CourseType.LECTURE, 50, 90, 3),
        ("PHYS101L", "Physics Lab I", 1, CourseType.LAB, 25, 180, 1),
        ("PHYS201", "General Physics II", 4, CourseType.LECTURE, 45, 90, 3),
        ("PHYS301", "Modern Physics", 3, CourseType.LECTURE, 30, 90, 2)
    ]
    
    # Chemistry Courses
    chem_courses = [
        ("CHEM101", "General Chemistry I", 4, CourseType.LECTURE, 55, 90, 3),
        ("CHEM101L", "Chemistry Lab I", 1, CourseType.LAB, 25, 180, 1),
        ("CHEM201", "Organic Chemistry", 4, CourseType.LECTURE, 40, 90, 3),
        ("CHEM301", "Physical Chemistry", 3, CourseType.LECTURE, 30, 90, 2)
    ]
    
    # Biology Courses
    bio_courses = [
        ("BIO101", "General Biology I", 4, CourseType.LECTURE, 60, 90, 3),
        ("BIO101L", "Biology Lab I", 1, CourseType.LAB, 25, 180, 1),
        ("BIO201", "Cell Biology", 3, CourseType.LECTURE, 35, 90, 2),
        ("BIO301", "Genetics", 3, CourseType.LECTURE, 30, 90, 2)
    ]
    
    all_courses = [
        ("Computer Science", cs_courses),
        ("Mathematics", math_courses),
        ("Physics", physics_courses),
        ("Chemistry", chem_courses),
        ("Biology", bio_courses)
    ]
    
    for department, course_list in all_courses:
        for course_data in course_list:
            code, name, credits, course_type, enrolled, duration, sessions = course_data
            
            # Determine required equipment based on course type
            required_equipment = []
            if course_type == CourseType.LAB:
                if "Computer" in department or "CS" in code:
                    required_equipment = ["Computers", "Software"]
                else:
                    required_equipment = ["Lab Equipment"]
            
            course = Course(
                id=str(uuid.uuid4()),
                name=name,
                code=code,
                department=department,
                semester="Fall 2024",
                credits=credits,
                course_type=course_type,
                enrolled_students=enrolled,
                duration=duration,
                sessions_per_week=sessions,
                required_equipment=required_equipment,
                preferred_room_type="Lab" if course_type == CourseType.LAB else "Regular",
                faculty_id=""  # Will be assigned based on department
            )
            courses.append(course)
    
    return courses


def test_timetable_generation():
    """Test the timetable generation system with sample data."""
    print("=== AI-Powered Timetable Generator Test ===\n")
    
    # Generate sample data
    print("Generating sample data...")
    courses = generate_sample_courses()
    faculty = generate_sample_faculty()
    classrooms = generate_sample_classrooms()
    time_slots = generate_sample_time_slots()
    
    print(f"✓ Generated {len(courses)} courses")
    print(f"✓ Generated {len(faculty)} faculty members")
    print(f"✓ Generated {len(classrooms)} classrooms")
    print(f"✓ Generated {len(time_slots)} time slots")
    
    # Create timetable generator
    generator = TimetableGenerator()
    generator.set_data(courses, faculty, classrooms, time_slots)
    
    # Test different solver types
    solver_types = [
        (SolverType.GREEDY, "Greedy Algorithm"),
        (SolverType.HYBRID, "Hybrid Approach"),
        # (SolverType.CSP_BACKTRACKING, "CSP Backtracking")  # Might take longer
    ]
    
    results = {}
    
    for solver_type, solver_name in solver_types:
        print(f"\n--- Testing {solver_name} ---")
        
        try:
            schedule = generator.generate_timetable(
                solver_type=solver_type,
                max_time=60,  # 1 minute max for testing
                optimize=True
            )
            
            if schedule:
                analysis = generator.analyze_schedule(schedule)
                stats = generator.get_generation_statistics()
                
                results[solver_name] = {
                    'schedule': schedule,
                    'analysis': analysis,
                    'stats': stats
                }
                
                print(f"✓ Generation successful!")
                print(f"  - Total entries: {len(schedule.entries)}")
                print(f"  - Conflicts: {len(schedule.conflicts)}")
                print(f"  - Optimization score: {schedule.optimization_score:.2f}")
                print(f"  - Room utilization: {analysis['basic_stats']['room_utilization']:.1%}")
                print(f"  - Generation time: {stats['generation_time']:.2f}s")
                
                if analysis.get('improvement_suggestions'):
                    print(f"  - Suggestions: {len(analysis['improvement_suggestions'])}")
            else:
                print(f"✗ Generation failed")
                
        except Exception as e:
            print(f"✗ Error: {str(e)}")
    
    # Display best result
    if results:
        print(f"\n=== Best Results Comparison ===")
        for solver_name, result in results.items():
            schedule = result['schedule']
            print(f"{solver_name}:")
            print(f"  Score: {schedule.optimization_score:.2f}")
            print(f"  Entries: {len(schedule.entries)}")
            print(f"  Conflicts: {len(schedule.conflicts)}")
            print(f"  Valid: {schedule.is_valid()}")
        
        # Find best schedule
        best_solver = max(results.keys(), 
                         key=lambda k: results[k]['schedule'].optimization_score)
        best_schedule = results[best_solver]['schedule']
        
        print(f"\nBest solver: {best_solver}")
        print(f"Schedule summary: {best_schedule}")
        
        # Show sample schedule entries
        print(f"\n=== Sample Schedule Entries ===")
        for i, entry in enumerate(best_schedule.entries[:5]):  # Show first 5 entries
            print(f"{i+1}. {entry}")
        
        if len(best_schedule.entries) > 5:
            print(f"... and {len(best_schedule.entries) - 5} more entries")
    
    return results


if __name__ == "__main__":
    results = test_timetable_generation()
    
    print(f"\n=== Test completed successfully! ===")
    if results:
        print("You can now run the web application with: python app.py")
    else:
        print("No successful results. Check the implementation and try again.")