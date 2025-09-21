"""
Data models for the AI-powered timetable generator system.
Defines core entities: Course, Faculty, Classroom, TimeSlot, and Schedule.
"""

from __future__ import annotations
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime, time


class DayOfWeek(Enum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class CourseType(Enum):
    LECTURE = "Lecture"
    LAB = "Lab"
    TUTORIAL = "Tutorial"
    SEMINAR = "Seminar"
    PRACTICAL = "Practical"
    WORKSHOP = "Workshop"


class SpecialClassType(Enum):
    ASSEMBLY = "Assembly"
    BREAK = "Break"
    LUNCH = "Lunch"
    SPORTS = "Sports"
    LIBRARY = "Library"
    EXAM = "Exam"
    MEETING = "Meeting"


@dataclass
class Batch:
    """Represents a batch/group of students."""
    id: str
    name: str  # e.g., "CS-A-2024", "ECE-B-2023"
    department: str
    semester: str
    year: int
    section: str  # A, B, C, etc.
    student_count: int
    max_classes_per_day: int = 6
    subjects: List[str] = None  # List of subject IDs for this batch
    # Student ID range for this batch
    student_id_start: str = ""  # Starting student ID (e.g., "CS2024001")
    student_id_end: str = ""    # Ending student ID (e.g., "CS2024050")
    student_id_pattern: str = ""  # Pattern for ID generation (e.g., "CS2024{###}")
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if self.subjects is None:
            self.subjects = []
    
    def belongs_to_batch(self, student_id: str) -> bool:
        """Check if a student ID belongs to this batch."""
        if not self.student_id_start or not self.student_id_end:
            return False
        
        # Extract numeric part for comparison
        try:
            # Assumes student ID format like "CS2024001"
            start_prefix = ''.join(c for c in self.student_id_start if not c.isdigit())
            end_prefix = ''.join(c for c in self.student_id_end if not c.isdigit())
            student_prefix = ''.join(c for c in student_id if not c.isdigit())
            
            if student_prefix != start_prefix or student_prefix != end_prefix:
                return False
            
            start_num = int(''.join(c for c in self.student_id_start if c.isdigit()))
            end_num = int(''.join(c for c in self.student_id_end if c.isdigit()))
            student_num = int(''.join(c for c in student_id if c.isdigit()))
            
            return start_num <= student_num <= end_num
        except (ValueError, IndexError):
            # Fallback: simple string comparison
            return self.student_id_start <= student_id <= self.student_id_end
    
    def generate_student_ids(self) -> List[str]:
        """Generate list of all student IDs in this batch."""
        if not self.student_id_start or not self.student_id_end:
            return []
        
        student_ids = []
        try:
            prefix = ''.join(c for c in self.student_id_start if not c.isdigit())
            start_num = int(''.join(c for c in self.student_id_start if c.isdigit()))
            end_num = int(''.join(c for c in self.student_id_end if c.isdigit()))
            
            # Determine padding length from original format
            num_digits = len(''.join(c for c in self.student_id_start if c.isdigit()))
            
            for i in range(start_num, end_num + 1):
                student_id = f"{prefix}{str(i).zfill(num_digits)}"
                student_ids.append(student_id)
        except (ValueError, IndexError):
            pass
        
        return student_ids
    
    def __str__(self):
        return f"{self.name} ({self.student_count} students)"


@dataclass
class SpecialClass:
    """Represents special classes with fixed time slots."""
    id: str
    name: str
    type: SpecialClassType
    time_slots: List['TimeSlot']  # Fixed time slots
    affected_batches: List[str] = None  # Batch IDs affected by this special class
    is_recurring: bool = True  # Whether it repeats every week
    description: str = ""
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if self.affected_batches is None:
            self.affected_batches = []
    
    def __str__(self):
        return f"{self.name} ({self.type.value})"


@dataclass
class TimeSlot:
    """Represents a time slot in the timetable."""
    id: str
    day: DayOfWeek
    start_time: str  # Format: "HH:MM"
    end_time: str    # Format: "HH:MM"
    duration: int    # Duration in minutes
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def overlaps_with(self, other: 'TimeSlot') -> bool:
        """Check if this time slot overlaps with another time slot."""
        if self.day != other.day:
            return False
        
        # Convert time strings to minutes for comparison
        self_start = self._time_to_minutes(self.start_time)
        self_end = self._time_to_minutes(self.end_time)
        other_start = other._time_to_minutes(other.start_time)
        other_end = other._time_to_minutes(other.end_time)
        
        return not (self_end <= other_start or other_end <= self_start)
    
    def _time_to_minutes(self, time_str: str) -> int:
        """Convert time string to minutes since midnight."""
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    
    def __str__(self):
        return f"{self.day.value} {self.start_time}-{self.end_time}"


@dataclass
class Classroom:
    """Represents a classroom with its properties."""
    id: str
    name: str
    capacity: int
    room_type: str  # "Regular", "Lab", "Auditorium", etc.
    equipment: List[str]  # Available equipment
    location: str = ""
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def can_accommodate(self, required_capacity: int, required_equipment: List[str] = None) -> bool:
        """Check if classroom can accommodate the requirements."""
        if self.capacity < required_capacity:
            return False
        
        if required_equipment:
            return all(eq in self.equipment for eq in required_equipment)
        
        return True
    
    def __str__(self):
        return f"{self.name} (Capacity: {self.capacity})"


@dataclass
class Faculty:
    """Represents a faculty member with availability and constraints."""
    id: str
    name: str
    email: str
    department: str
    available_slots: List[TimeSlot]
    max_hours_per_week: int = 20
    preferred_slots: List[TimeSlot] = None
    unavailable_slots: List[TimeSlot] = None
    # New parameters for enhanced functionality
    subjects_expertise: List[str] = None  # Subject IDs the faculty can teach
    average_leaves_per_month: int = 2  # Average leaves per month
    leave_pattern: Dict[str, bool] = None  # Specific leave dates {"2024-01-15": True}
    priority_level: int = 1  # 1=High, 2=Medium, 3=Low priority for assignment
    max_classes_per_day: int = 4  # Maximum classes per day
    workload_preference: float = 1.0  # 0.5=Part-time, 1.0=Full-time, 1.5=Overtime
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if self.preferred_slots is None:
            self.preferred_slots = []
        if self.unavailable_slots is None:
            self.unavailable_slots = []
        if self.subjects_expertise is None:
            self.subjects_expertise = []
        if self.leave_pattern is None:
            self.leave_pattern = {}
    
    def is_available(self, time_slot: TimeSlot) -> bool:
        """Check if faculty is available during a specific time slot."""
        # Check if the slot conflicts with unavailable slots
        for unavailable in self.unavailable_slots:
            if time_slot.overlaps_with(unavailable):
                return False
        
        # Check if the slot is in available slots
        for available in self.available_slots:
            if time_slot.overlaps_with(available):
                return True
        
        return False
    
    def get_preference_score(self, time_slot: TimeSlot) -> float:
        """Get preference score for a time slot (higher is better)."""
        for preferred in self.preferred_slots:
            if time_slot.overlaps_with(preferred):
                return 1.0
        return 0.5  # Neutral preference
    
    def can_teach_subject(self, subject_id: str) -> bool:
        """Check if faculty can teach a specific subject."""
        return subject_id in self.subjects_expertise
    
    def is_available_on_date(self, date_str: str) -> bool:
        """Check if faculty is available on a specific date."""
        return not self.leave_pattern.get(date_str, False)
    
    def get_workload_score(self, current_classes: int) -> float:
        """Get workload score based on current assignment."""
        optimal_classes = int(self.max_hours_per_week / 2)  # Assuming 2-hour classes
        if current_classes <= optimal_classes:
            return 1.0
        return max(0.1, 1.0 - (current_classes - optimal_classes) * 0.2)
    
    def __str__(self):
        return f"{self.name} ({self.department})"


@dataclass
class Course:
    """Represents a course with its requirements and constraints."""
    id: str
    name: str
    code: str
    department: str
    semester: str
    credits: int
    course_type: CourseType
    enrolled_students: int
    duration: int  # Duration in minutes
    sessions_per_week: int
    required_equipment: List[str] = None
    preferred_room_type: str = "Regular"
    faculty_id: str = ""
    # Enhanced parameters
    assigned_batches: List[str] = None  # Batch IDs for this course
    sessions_per_day: int = 1  # Maximum sessions per day
    preferred_time_slots: List[str] = None  # Preferred time slot IDs
    cannot_be_scheduled_with: List[str] = None  # Course IDs that conflict
    is_core_subject: bool = True  # Core vs elective
    requires_consecutive_sessions: bool = False  # For lab sessions
    minimum_gap_between_sessions: int = 0  # In hours
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if self.required_equipment is None:
            self.required_equipment = []
        if self.assigned_batches is None:
            self.assigned_batches = []
        if self.preferred_time_slots is None:
            self.preferred_time_slots = []
        if self.cannot_be_scheduled_with is None:
            self.cannot_be_scheduled_with = []
    
    def get_required_capacity(self) -> int:
        """Get required classroom capacity with some buffer."""
        return int(self.enrolled_students * 1.1)  # 10% buffer
    
    def is_compatible_with_room(self, classroom: Classroom) -> bool:
        """Check if course is compatible with a classroom."""
        if not classroom.can_accommodate(self.get_required_capacity(), self.required_equipment):
            return False
        
        # Check room type compatibility
        if self.course_type == CourseType.LAB and classroom.room_type != "Lab":
            return False
        
        return True
    
    def __str__(self):
        return f"{self.code}: {self.name}"


@dataclass
class ScheduleEntry:
    """Represents a single entry in the schedule."""
    course: Course
    faculty: Faculty
    classroom: Classroom
    time_slot: TimeSlot
    batch: Optional['Batch'] = None  # The batch attending this class
    session_type: str = "regular"  # "regular", "makeup", "extra"
    week_number: int = 1  # For recurring schedules
    
    def __str__(self):
        return f"{self.course.code} - {self.faculty.name} - {self.classroom.name} - {self.time_slot}"


class Schedule:
    """Represents the complete timetable schedule."""
    
    def __init__(self):
        self.entries: List[ScheduleEntry] = []
        self.conflicts: List[str] = []
        self.optimization_score: float = 0.0
    
    def add_entry(self, entry: ScheduleEntry) -> bool:
        """Add a schedule entry if it doesn't create conflicts."""
        conflicts = self.check_conflicts(entry)
        
        if conflicts:
            self.conflicts.extend(conflicts)
            return False
        
        self.entries.append(entry)
        return True
    
    def check_conflicts(self, new_entry: ScheduleEntry) -> List[str]:
        """Check for conflicts with existing schedule entries."""
        conflicts = []
        
        for existing_entry in self.entries:
            # Check time slot overlap
            if new_entry.time_slot.overlaps_with(existing_entry.time_slot):
                # Faculty conflict
                if new_entry.faculty.id == existing_entry.faculty.id:
                    conflicts.append(f"Faculty {new_entry.faculty.name} has conflicting classes")
                
                # Classroom conflict
                if new_entry.classroom.id == existing_entry.classroom.id:
                    conflicts.append(f"Classroom {new_entry.classroom.name} is double-booked")
        
        return conflicts
    
    def get_faculty_schedule(self, faculty_id: str) -> List[ScheduleEntry]:
        """Get all schedule entries for a specific faculty member."""
        return [entry for entry in self.entries if entry.faculty.id == faculty_id]
    
    def get_classroom_schedule(self, classroom_id: str) -> List[ScheduleEntry]:
        """Get all schedule entries for a specific classroom."""
        return [entry for entry in self.entries if entry.classroom.id == classroom_id]
    
    def get_course_schedule(self, course_id: str) -> List[ScheduleEntry]:
        """Get all schedule entries for a specific course."""
        return [entry for entry in self.entries if entry.course.id == course_id]
    
    def calculate_optimization_score(self) -> float:
        """Calculate optimization score based on various factors."""
        if not self.entries:
            return 0.0
        
        score = 0.0
        total_entries = len(self.entries)
        
        # Faculty preference score
        for entry in self.entries:
            score += entry.faculty.get_preference_score(entry.time_slot)
        
        # Penalty for conflicts
        score -= len(self.conflicts) * 10
        
        # Bonus for efficient room utilization
        room_utilization = self.calculate_room_utilization()
        score += room_utilization * 5
        
        self.optimization_score = score / total_entries if total_entries > 0 else 0
        return self.optimization_score
    
    def calculate_room_utilization(self) -> float:
        """Calculate average room utilization efficiency."""
        if not self.entries:
            return 0.0
        
        utilization_scores = []
        for entry in self.entries:
            capacity_utilization = entry.course.enrolled_students / entry.classroom.capacity
            utilization_scores.append(min(capacity_utilization, 1.0))  # Cap at 100%
        
        return sum(utilization_scores) / len(utilization_scores)
    
    def is_valid(self) -> bool:
        """Check if the schedule is valid (no conflicts)."""
        return len(self.conflicts) == 0
    
    def get_summary(self) -> Dict:
        """Get a summary of the schedule statistics."""
        return {
            "total_entries": len(self.entries),
            "total_conflicts": len(self.conflicts),
            "optimization_score": self.optimization_score,
            "room_utilization": self.calculate_room_utilization(),
            "is_valid": self.is_valid()
        }
    
    def __str__(self):
        return f"Schedule: {len(self.entries)} entries, {len(self.conflicts)} conflicts, Score: {self.optimization_score:.2f}"


@dataclass
class TimetableConfiguration:
    """Global configuration parameters for timetable generation."""
    # General parameters
    institution_name: str = "Default Institution"
    academic_year: str = "2024-25"
    semester_name: str = "Fall 2024"
    
    # Timing parameters
    day_start_time: str = "08:00"  # HH:MM format
    day_end_time: str = "18:00"   # HH:MM format
    break_duration: int = 15      # Minutes
    lunch_duration: int = 60      # Minutes
    lunch_start_time: str = "12:30"
    
    # Class parameters
    default_class_duration: int = 90  # Minutes
    max_classes_per_day_default: int = 6
    min_gap_between_classes: int = 10  # Minutes
    max_consecutive_classes: int = 3
    
    # Working days
    working_days: List[DayOfWeek] = field(default_factory=lambda: [
        DayOfWeek.MONDAY,
        DayOfWeek.TUESDAY, 
        DayOfWeek.WEDNESDAY,
        DayOfWeek.THURSDAY,
        DayOfWeek.FRIDAY
    ])
    
    # Optimization preferences
    priority_core_subjects: bool = True
    allow_back_to_back_labs: bool = False
    prefer_morning_theory_classes: bool = True
    prefer_afternoon_lab_classes: bool = True
    
    # Resource constraints
    classroom_utilization_target: float = 0.8  # 80%
    faculty_workload_balance: bool = True
    
    # Special constraints
    avoid_single_class_days: bool = True  # Don't schedule just one class per day
    enforce_subject_distribution: bool = True  # Spread subjects across week
    
    def get_total_weekly_slots(self) -> int:
        """Calculate total available slots per week."""
        daily_duration = self._time_to_minutes(self.day_end_time) - self._time_to_minutes(self.day_start_time)
        slots_per_day = (daily_duration - self.lunch_duration) // (self.default_class_duration + self.break_duration)
        return slots_per_day * len(self.working_days)
    
    def _time_to_minutes(self, time_str: str) -> int:
        """Convert time string to minutes since midnight."""
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    
    def is_working_day(self, day: DayOfWeek) -> bool:
        """Check if a day is a working day."""
        return day in self.working_days
    
    def __str__(self):
        return f"Timetable Config: {self.institution_name} - {self.semester_name}"
