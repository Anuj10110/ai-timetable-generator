"""
Enhanced timetable generation engine that handles faculty unavailability,
rescheduling, and faculty substitution with intelligent conflict resolution.
"""

from typing import List, Dict, Optional, Tuple, Set
import time
import logging
from datetime import datetime, timedelta
from copy import deepcopy
from enum import Enum

from models.data_models import (
    Course, Faculty, Classroom, TimeSlot, Schedule, ScheduleEntry,
    DayOfWeek, CourseType
)
from algorithms.csp_solver import CSPSolver, GreedySolver
from algorithms.graph_optimizer import GraphBasedOptimizer


class UnavailabilityReason(Enum):
    PERSONAL_LEAVE = "personal_leave"
    CONFERENCE = "conference" 
    MEETING = "meeting"
    OTHER_COMMITMENT = "other_commitment"
    SICK_LEAVE = "sick_leave"
    EMERGENCY = "emergency"


class FacultyUnavailability:
    """Represents a period when faculty is unavailable."""
    
    def __init__(self, faculty_id: str, start_time: datetime, end_time: datetime, 
                 reason: UnavailabilityReason, priority: int = 1):
        self.faculty_id = faculty_id
        self.start_time = start_time
        self.end_time = end_time
        self.reason = reason
        self.priority = priority  # 1=low, 2=medium, 3=high, 4=critical
        
    def conflicts_with_timeslot(self, time_slot: TimeSlot) -> bool:
        """Check if this unavailability conflicts with a time slot."""
        # Convert time slot to datetime for comparison
        slot_start = datetime.combine(datetime.today(), 
                                     datetime.strptime(time_slot.start_time, "%H:%M").time())
        slot_end = datetime.combine(datetime.today(),
                                   datetime.strptime(time_slot.end_time, "%H:%M").time())
        
        return not (self.end_time <= slot_start or self.start_time >= slot_end)


class RescheduleOption:
    """Represents a rescheduling option for a displaced class."""
    
    def __init__(self, original_entry: ScheduleEntry, new_time_slot: TimeSlot, 
                 new_classroom: Optional[Classroom] = None, 
                 substitute_faculty: Optional[Faculty] = None):
        self.original_entry = original_entry
        self.new_time_slot = new_time_slot
        self.new_classroom = new_classroom or original_entry.classroom
        self.substitute_faculty = substitute_faculty or original_entry.faculty
        self.feasibility_score = 0.0


class EnhancedTimetableGenerator:
    """Enhanced timetable generator with faculty unavailability handling."""
    
    def __init__(self):
        self.courses: List[Course] = []
        self.faculty: List[Faculty] = []
        self.classrooms: List[Classroom] = []
        self.time_slots: List[TimeSlot] = []
        self.unavailabilities: List[FacultyUnavailability] = []
        
        # Base solvers
        self.csp_solver: Optional[CSPSolver] = None
        self.greedy_solver: Optional[GreedySolver] = None
        self.graph_optimizer: Optional[GraphBasedOptimizer] = None
        
        # Enhanced features
        self.free_period_slots: List[TimeSlot] = []
        self.faculty_substitution_matrix: Dict[str, List[str]] = {}
        
        # Statistics
        self.generation_stats = {}
        self.rescheduling_stats = {}
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def set_data(self, courses: List[Course], faculty: List[Faculty], 
                 classrooms: List[Classroom], time_slots: List[TimeSlot]):
        """Set the input data for timetable generation."""
        self.courses = courses
        self.faculty = faculty
        self.classrooms = classrooms
        self.time_slots = time_slots
        
        # Initialize base solvers
        self.csp_solver = CSPSolver(courses, faculty, classrooms, time_slots)
        self.greedy_solver = GreedySolver(courses, faculty, classrooms, time_slots)
        self.graph_optimizer = GraphBasedOptimizer(courses, faculty, classrooms, time_slots)
        
        # Identify free periods and build substitution matrix
        self._identify_free_periods()
        self._build_faculty_substitution_matrix()
        
        self.logger.info(f"Enhanced generator initialized with {len(courses)} courses, "
                        f"{len(faculty)} faculty, {len(classrooms)} classrooms, "
                        f"{len(time_slots)} time slots, {len(self.free_period_slots)} free periods")
    
    def add_faculty_unavailability(self, unavailability: FacultyUnavailability):
        """Add a faculty unavailability period."""
        self.unavailabilities.append(unavailability)
        self.logger.info(f"Added unavailability for faculty {unavailability.faculty_id}: "
                        f"{unavailability.reason.value} from {unavailability.start_time} "
                        f"to {unavailability.end_time}")
    
    def generate_adaptive_timetable(self, max_time: int = 300) -> Optional[Schedule]:
        """
        Generate a timetable that adapts to faculty unavailabilities.
        
        Args:
            max_time: Maximum time to spend on generation
            
        Returns:
            Adaptive schedule or None if no solution found
        """
        start_time = time.time()
        
        # Step 1: Generate initial timetable
        self.logger.info("Step 1: Generating initial timetable...")
        initial_schedule = self._generate_initial_schedule(max_time // 2)
        
        if not initial_schedule:
            self.logger.error("Failed to generate initial schedule")
            return None
        
        # Step 2: Handle unavailabilities
        self.logger.info("Step 2: Handling faculty unavailabilities...")
        adaptive_schedule = self._handle_unavailabilities(initial_schedule)
        
        # Step 3: Optimize the adapted schedule
        if adaptive_schedule and self.graph_optimizer:
            self.logger.info("Step 3: Optimizing adapted schedule...")
            adaptive_schedule = self.graph_optimizer.optimize_schedule(adaptive_schedule)
        
        generation_time = time.time() - start_time
        
        # Record statistics
        self.generation_stats = {
            "generation_time": generation_time,
            "total_unavailabilities": len(self.unavailabilities),
            "rescheduled_classes": self.rescheduling_stats.get("rescheduled", 0),
            "substituted_faculty": self.rescheduling_stats.get("substituted", 0),
            "moved_to_free_periods": self.rescheduling_stats.get("free_periods", 0)
        }
        
        if adaptive_schedule:
            self.logger.info(f"Adaptive timetable generated in {generation_time:.2f}s")
            self.logger.info(f"Handled {len(self.unavailabilities)} unavailabilities with "
                           f"{self.rescheduling_stats.get('rescheduled', 0)} rescheduled classes")
        
        return adaptive_schedule
    
    def _generate_initial_schedule(self, max_time: int) -> Optional[Schedule]:
        """Generate initial schedule using hybrid approach."""
        # Try CSP first with limited time
        csp_time = min(max_time // 2, 120)
        schedule = self.csp_solver.solve(use_heuristics=True, max_time=csp_time)
        
        if not schedule or not schedule.is_valid():
            self.logger.info("CSP failed, trying greedy approach...")
            schedule = self.greedy_solver.solve()
        
        return schedule
    
    def _handle_unavailabilities(self, schedule: Schedule) -> Schedule:
        """Handle all faculty unavailabilities in the schedule."""
        adapted_schedule = deepcopy(schedule)
        self.rescheduling_stats = {"rescheduled": 0, "substituted": 0, "free_periods": 0}
        
        # Group unavailabilities by priority (handle critical first)
        sorted_unavailabilities = sorted(self.unavailabilities, 
                                       key=lambda x: x.priority, reverse=True)
        
        for unavailability in sorted_unavailabilities:
            self._handle_single_unavailability(adapted_schedule, unavailability)
        
        # Recalculate optimization score
        adapted_schedule.calculate_optimization_score()
        return adapted_schedule
    
    def _handle_single_unavailability(self, schedule: Schedule, 
                                    unavailability: FacultyUnavailability):
        """Handle a single faculty unavailability."""
        affected_entries = self._find_affected_entries(schedule, unavailability)
        
        if not affected_entries:
            return
        
        self.logger.info(f"Handling unavailability for faculty {unavailability.faculty_id}: "
                        f"{len(affected_entries)} classes affected")
        
        for entry in affected_entries:
            success = self._reschedule_entry(schedule, entry, unavailability)
            if success:
                self.rescheduling_stats["rescheduled"] += 1
            else:
                self.logger.warning(f"Failed to reschedule {entry.course.code}")
    
    def _find_affected_entries(self, schedule: Schedule, 
                             unavailability: FacultyUnavailability) -> List[ScheduleEntry]:
        """Find schedule entries affected by the unavailability."""
        affected = []
        
        for entry in schedule.entries:
            if (entry.faculty.id == unavailability.faculty_id and 
                unavailability.conflicts_with_timeslot(entry.time_slot)):
                affected.append(entry)
        
        return affected
    
    def _reschedule_entry(self, schedule: Schedule, entry: ScheduleEntry, 
                         unavailability: FacultyUnavailability) -> bool:
        """Attempt to reschedule a single entry."""
        # Generate rescheduling options
        options = self._generate_reschedule_options(schedule, entry, unavailability)
        
        if not options:
            return False
        
        # Select best option
        best_option = max(options, key=lambda x: x.feasibility_score)
        
        # Apply the rescheduling
        return self._apply_reschedule_option(schedule, best_option)
    
    def _generate_reschedule_options(self, schedule: Schedule, entry: ScheduleEntry,
                                   unavailability: FacultyUnavailability) -> List[RescheduleOption]:
        """Generate possible rescheduling options for an entry."""
        options = []
        
        # Option 1: Move to free period with same faculty
        free_period_options = self._try_free_period_rescheduling(schedule, entry)
        options.extend(free_period_options)
        
        # Option 2: Move to different time slot with same faculty
        time_shift_options = self._try_time_shift_rescheduling(schedule, entry, unavailability)
        options.extend(time_shift_options)
        
        # Option 3: Use substitute faculty at same time
        substitution_options = self._try_faculty_substitution(schedule, entry)
        options.extend(substitution_options)
        
        # Option 4: Combine time shift + room change
        complex_options = self._try_complex_rescheduling(schedule, entry, unavailability)
        options.extend(complex_options)
        
        # Calculate feasibility scores
        for option in options:
            option.feasibility_score = self._calculate_feasibility_score(schedule, option)
        
        return options
    
    def _try_free_period_rescheduling(self, schedule: Schedule, 
                                    entry: ScheduleEntry) -> List[RescheduleOption]:
        """Try to reschedule to a free period slot."""
        options = []
        
        for free_slot in self.free_period_slots:
            if (entry.faculty.is_available(free_slot) and 
                not self._conflicts_with_schedule(schedule, entry.course, 
                                                entry.faculty, entry.classroom, free_slot)):
                
                option = RescheduleOption(entry, free_slot)
                options.append(option)
        
        return options
    
    def _try_time_shift_rescheduling(self, schedule: Schedule, entry: ScheduleEntry,
                                   unavailability: FacultyUnavailability) -> List[RescheduleOption]:
        """Try to reschedule to a different time slot."""
        options = []
        
        for time_slot in self.time_slots:
            # Skip if it's the original slot or conflicts with unavailability
            if (time_slot.id == entry.time_slot.id or 
                unavailability.conflicts_with_timeslot(time_slot)):
                continue
            
            if (entry.faculty.is_available(time_slot) and 
                not self._conflicts_with_schedule(schedule, entry.course, 
                                                entry.faculty, entry.classroom, time_slot)):
                
                option = RescheduleOption(entry, time_slot)
                options.append(option)
        
        return options
    
    def _try_faculty_substitution(self, schedule: Schedule, 
                                entry: ScheduleEntry) -> List[RescheduleOption]:
        """Try to use a substitute faculty member."""
        options = []
        original_faculty_id = entry.faculty.id
        
        if original_faculty_id in self.faculty_substitution_matrix:
            for substitute_id in self.faculty_substitution_matrix[original_faculty_id]:
                substitute_faculty = self._find_faculty_by_id(substitute_id)
                
                if (substitute_faculty and 
                    substitute_faculty.is_available(entry.time_slot) and
                    not self._conflicts_with_schedule(schedule, entry.course, 
                                                    substitute_faculty, 
                                                    entry.classroom, entry.time_slot)):
                    
                    option = RescheduleOption(entry, entry.time_slot, 
                                            entry.classroom, substitute_faculty)
                    options.append(option)
        
        return options
    
    def _try_complex_rescheduling(self, schedule: Schedule, entry: ScheduleEntry,
                                unavailability: FacultyUnavailability) -> List[RescheduleOption]:
        """Try complex rescheduling involving both time and room changes."""
        options = []
        
        for time_slot in self.time_slots:
            if (time_slot.id == entry.time_slot.id or 
                unavailability.conflicts_with_timeslot(time_slot)):
                continue
            
            for classroom in self.classrooms:
                if (entry.faculty.is_available(time_slot) and
                    entry.course.is_compatible_with_room(classroom) and
                    not self._conflicts_with_schedule(schedule, entry.course, 
                                                    entry.faculty, classroom, time_slot)):
                    
                    option = RescheduleOption(entry, time_slot, classroom)
                    options.append(option)
        
        return options
    
    def _calculate_feasibility_score(self, schedule: Schedule, 
                                   option: RescheduleOption) -> float:
        """Calculate a feasibility score for a rescheduling option."""
        score = 100.0  # Base score
        
        # Penalize time changes
        if option.new_time_slot.id != option.original_entry.time_slot.id:
            score -= 10
        
        # Penalize room changes
        if option.new_classroom.id != option.original_entry.classroom.id:
            score -= 5
        
        # Heavily penalize faculty substitution
        if option.substitute_faculty.id != option.original_entry.faculty.id:
            score -= 20
        
        # Reward free period usage
        if option.new_time_slot in self.free_period_slots:
            score += 15
        
        # Consider student convenience (prefer morning slots)
        hour = int(option.new_time_slot.start_time.split(':')[0])
        if 9 <= hour <= 11:  # Morning preference
            score += 5
        elif hour >= 16:     # Late afternoon penalty
            score -= 10
        
        # Avoid conflicts with break times
        if self._is_break_time(option.new_time_slot):
            score -= 15
        
        return max(score, 0)
    
    def _apply_reschedule_option(self, schedule: Schedule, 
                               option: RescheduleOption) -> bool:
        """Apply a rescheduling option to the schedule."""
        try:
            # Remove original entry
            schedule.entries.remove(option.original_entry)
            
            # Create new entry
            new_entry = ScheduleEntry(
                course=option.original_entry.course,
                faculty=option.substitute_faculty,
                classroom=option.new_classroom,
                time_slot=option.new_time_slot
            )
            
            # Add new entry
            schedule.add_entry(new_entry)
            
            # Update statistics
            if option.substitute_faculty.id != option.original_entry.faculty.id:
                self.rescheduling_stats["substituted"] += 1
            
            if option.new_time_slot in self.free_period_slots:
                self.rescheduling_stats["free_periods"] += 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply rescheduling option: {str(e)}")
            return False
    
    def _identify_free_periods(self):
        """Identify time slots designated as free periods."""
        # Common free period times
        free_period_times = [
            ("11:00", "12:00"),  # Late morning break
            ("13:00", "14:00"),  # Lunch break extended
            ("15:00", "16:00"),  # Afternoon break
        ]
        
        for start_time, end_time in free_period_times:
            for day in DayOfWeek:
                # Create free period slot
                free_slot = TimeSlot(
                    id=f"free_{day.value}_{start_time}_{end_time}",
                    day=day,
                    start_time=start_time,
                    end_time=end_time,
                    duration=60
                )
                self.free_period_slots.append(free_slot)
    
    def _build_faculty_substitution_matrix(self):
        """Build a matrix of faculty substitution possibilities."""
        for faculty in self.faculty:
            substitutes = []
            
            # Find faculty from same department
            dept_faculty = [f for f in self.faculty 
                          if f.department == faculty.department and f.id != faculty.id]
            
            # Prioritize by expertise overlap (simplified)
            for substitute in dept_faculty:
                # In a real system, you'd check teaching qualifications, 
                # subject expertise, etc.
                substitutes.append(substitute.id)
            
            self.faculty_substitution_matrix[faculty.id] = substitutes
    
    def _conflicts_with_schedule(self, schedule: Schedule, course: Course, 
                               faculty: Faculty, classroom: Classroom, 
                               time_slot: TimeSlot) -> bool:
        """Check if a potential assignment conflicts with existing schedule."""
        for entry in schedule.entries:
            if time_slot.overlaps_with(entry.time_slot):
                # Faculty conflict
                if faculty.id == entry.faculty.id:
                    return True
                # Classroom conflict
                if classroom.id == entry.classroom.id:
                    return True
                # Student group conflict (same course/batch)
                if course.id == entry.course.id:
                    return True
        
        return False
    
    def _find_faculty_by_id(self, faculty_id: str) -> Optional[Faculty]:
        """Find faculty member by ID."""
        for faculty in self.faculty:
            if faculty.id == faculty_id:
                return faculty
        return None
    
    def _is_break_time(self, time_slot: TimeSlot) -> bool:
        """Check if time slot conflicts with common break times."""
        start_hour = int(time_slot.start_time.split(':')[0])
        # Common break times: 10:30-11:00, 12:00-13:00, 15:00-15:30
        break_hours = [10, 12, 15]
        return start_hour in break_hours
    
    def get_rescheduling_report(self) -> Dict:
        """Get detailed report of rescheduling actions."""
        return {
            "total_unavailabilities": len(self.unavailabilities),
            "rescheduling_stats": self.rescheduling_stats.copy(),
            "unavailabilities_by_reason": self._group_unavailabilities_by_reason(),
            "faculty_substitution_matrix": self.faculty_substitution_matrix.copy(),
            "free_periods_available": len(self.free_period_slots)
        }
    
    def _group_unavailabilities_by_reason(self) -> Dict[str, int]:
        """Group unavailabilities by reason."""
        reasons = {}
        for unavail in self.unavailabilities:
            reason = unavail.reason.value
            reasons[reason] = reasons.get(reason, 0) + 1
        return reasons
    
    def export_schedule_to_dict(self, schedule: Schedule) -> Dict:
        """Export schedule to dictionary format for JSON serialization."""
        if not schedule:
            return {}
        
        entries_data = []
        for entry in schedule.entries:
            entries_data.append({
                "course": {
                    "id": entry.course.id,
                    "code": entry.course.code,
                    "name": entry.course.name,
                    "department": entry.course.department,
                    "credits": entry.course.credits,
                    "enrolled_students": entry.course.enrolled_students,
                    "course_type": entry.course.course_type.value
                },
                "faculty": {
                    "id": entry.faculty.id,
                    "name": entry.faculty.name,
                    "department": entry.faculty.department
                },
                "classroom": {
                    "id": entry.classroom.id,
                    "name": entry.classroom.name,
                    "capacity": entry.classroom.capacity,
                    "room_type": entry.classroom.room_type
                },
                "time_slot": {
                    "id": entry.time_slot.id,
                    "day": entry.time_slot.day.value,
                    "start_time": entry.time_slot.start_time,
                    "end_time": entry.time_slot.end_time,
                    "duration": entry.time_slot.duration
                }
            })
        
        return {
            "entries": entries_data,
            "summary": schedule.get_summary(),
            "conflicts": schedule.conflicts,
            "generation_stats": self.generation_stats,
            "rescheduling_stats": self.rescheduling_stats
        }
