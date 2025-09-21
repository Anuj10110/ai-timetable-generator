"""
Constraint Satisfaction Problem (CSP) solver for timetable generation.
Implements backtracking algorithm with various heuristics for optimization.
"""

from typing import List, Dict, Tuple, Optional, Set
import random
from copy import deepcopy
import time

from models.data_models import (
    Course, Faculty, Classroom, TimeSlot, Schedule, ScheduleEntry,
    DayOfWeek, CourseType
)


class CSPVariable:
    """Represents a variable in the CSP (a course that needs to be scheduled)."""
    
    def __init__(self, course: Course, session_number: int = 1):
        self.course = course
        self.session_number = session_number  # For courses with multiple sessions per week
        self.domain: List[Tuple[TimeSlot, Classroom, Faculty]] = []  # Possible assignments
        
    def __str__(self):
        return f"{self.course.code}_session_{self.session_number}"


class CSPConstraint:
    """Base class for constraints in the CSP."""
    
    def is_satisfied(self, assignment: Dict[CSPVariable, Tuple[TimeSlot, Classroom, Faculty]]) -> bool:
        """Check if the constraint is satisfied given the current assignment."""
        raise NotImplementedError
    
    def get_conflicting_variables(self, assignment: Dict[CSPVariable, Tuple[TimeSlot, Classroom, Faculty]]) -> Set[CSPVariable]:
        """Return variables that are involved in constraint violations."""
        raise NotImplementedError


class NoConflictConstraint(CSPConstraint):
    """Constraint to ensure no two courses have conflicting time slots for the same resource."""
    
    def is_satisfied(self, assignment: Dict[CSPVariable, Tuple[TimeSlot, Classroom, Faculty]]) -> bool:
        assigned_slots = list(assignment.values())
        
        for i, (time1, room1, faculty1) in enumerate(assigned_slots):
            for j, (time2, room2, faculty2) in enumerate(assigned_slots[i+1:], i+1):
                if time1.overlaps_with(time2):
                    # Check for faculty conflict
                    if faculty1.id == faculty2.id:
                        return False
                    # Check for classroom conflict
                    if room1.id == room2.id:
                        return False
        
        return True
    
    def get_conflicting_variables(self, assignment: Dict[CSPVariable, Tuple[TimeSlot, Classroom, Faculty]]) -> Set[CSPVariable]:
        conflicting = set()
        variables = list(assignment.keys())
        assigned_slots = list(assignment.values())
        
        for i, (time1, room1, faculty1) in enumerate(assigned_slots):
            for j, (time2, room2, faculty2) in enumerate(assigned_slots[i+1:], i+1):
                if time1.overlaps_with(time2):
                    if faculty1.id == faculty2.id or room1.id == room2.id:
                        conflicting.add(variables[i])
                        conflicting.add(variables[j])
        
        return conflicting


class FacultyAvailabilityConstraint(CSPConstraint):
    """Constraint to ensure faculty is available for assigned time slots."""
    
    def is_satisfied(self, assignment: Dict[CSPVariable, Tuple[TimeSlot, Classroom, Faculty]]) -> bool:
        for variable, (time_slot, _, faculty) in assignment.items():
            if not faculty.is_available(time_slot):
                return False
        return True
    
    def get_conflicting_variables(self, assignment: Dict[CSPVariable, Tuple[TimeSlot, Classroom, Faculty]]) -> Set[CSPVariable]:
        conflicting = set()
        for variable, (time_slot, _, faculty) in assignment.items():
            if not faculty.is_available(time_slot):
                conflicting.add(variable)
        return conflicting


class RoomCompatibilityConstraint(CSPConstraint):
    """Constraint to ensure courses are assigned to compatible rooms."""
    
    def is_satisfied(self, assignment: Dict[CSPVariable, Tuple[TimeSlot, Classroom, Faculty]]) -> bool:
        for variable, (_, classroom, _) in assignment.items():
            if not variable.course.is_compatible_with_room(classroom):
                return False
        return True
    
    def get_conflicting_variables(self, assignment: Dict[CSPVariable, Tuple[TimeSlot, Classroom, Faculty]]) -> Set[CSPVariable]:
        conflicting = set()
        for variable, (_, classroom, _) in assignment.items():
            if not variable.course.is_compatible_with_room(classroom):
                conflicting.add(variable)
        return conflicting


class CSPSolver:
    """CSP solver using backtracking with various heuristics."""
    
    def __init__(self, courses: List[Course], faculty: List[Faculty], 
                 classrooms: List[Classroom], time_slots: List[TimeSlot]):
        self.courses = courses
        self.faculty = faculty
        self.classrooms = classrooms
        self.time_slots = time_slots
        
        # Create variables (one for each course session)
        self.variables: List[CSPVariable] = []
        for course in courses:
            for session in range(course.sessions_per_week):
                self.variables.append(CSPVariable(course, session + 1))
        
        # Initialize constraints
        self.constraints = [
            NoConflictConstraint(),
            FacultyAvailabilityConstraint(),
            RoomCompatibilityConstraint()
        ]
        
        # Initialize domains for each variable
        self._initialize_domains()
        
        # Statistics
        self.nodes_explored = 0
        self.max_depth = 0
        self.start_time = 0
        
    def _initialize_domains(self):
        """Initialize the domain for each variable with all possible assignments."""
        for variable in self.variables:
            variable.domain = []
            course = variable.course
            
            # Find faculty member assigned to this course
            assigned_faculty = None
            for faculty in self.faculty:
                if faculty.id == course.faculty_id:
                    assigned_faculty = faculty
                    break
            
            if not assigned_faculty:
                # If no specific faculty assigned, consider all faculty from same department
                available_faculty = [f for f in self.faculty if f.department == course.department]
            else:
                available_faculty = [assigned_faculty]
            
            # Generate all valid combinations
            for time_slot in self.time_slots:
                for classroom in self.classrooms:
                    for faculty in available_faculty:
                        if (faculty.is_available(time_slot) and 
                            course.is_compatible_with_room(classroom) and
                            time_slot.duration >= course.duration):
                            
                            variable.domain.append((time_slot, classroom, faculty))
    
    def solve(self, use_heuristics: bool = True, max_time: int = 300) -> Optional[Schedule]:
        """
        Solve the CSP and return a valid schedule.
        
        Args:
            use_heuristics: Whether to use heuristics for variable and value ordering
            max_time: Maximum time to spend solving (in seconds)
        
        Returns:
            Schedule object if solution found, None otherwise
        """
        self.start_time = time.time()
        self.nodes_explored = 0
        self.max_depth = 0
        
        assignment = {}
        result = self._backtrack(assignment, use_heuristics, max_time)
        
        if result:
            return self._assignment_to_schedule(result)
        return None
    
    def _backtrack(self, assignment: Dict[CSPVariable, Tuple[TimeSlot, Classroom, Faculty]], 
                   use_heuristics: bool, max_time: int, depth: int = 0) -> Optional[Dict]:
        """Recursive backtracking algorithm."""
        
        # Check time limit
        if time.time() - self.start_time > max_time:
            return None
        
        self.nodes_explored += 1
        self.max_depth = max(self.max_depth, depth)
        
        # Check if assignment is complete
        if len(assignment) == len(self.variables):
            if self._is_consistent(assignment):
                return assignment
            return None
        
        # Select next variable
        if use_heuristics:
            variable = self._select_unassigned_variable_mrv(assignment)
        else:
            variable = self._select_unassigned_variable_naive(assignment)
        
        if not variable:
            return None
        
        # Order domain values
        if use_heuristics:
            domain_values = self._order_domain_values_lcv(variable, assignment)
        else:
            domain_values = variable.domain.copy()
            random.shuffle(domain_values)
        
        for value in domain_values:
            assignment[variable] = value
            
            if self._is_consistent_with_assignment(variable, value, assignment):
                # Forward checking: reduce domains of unassigned variables
                old_domains = self._forward_check(variable, value, assignment)
                
                result = self._backtrack(assignment, use_heuristics, max_time, depth + 1)
                if result:
                    return result
                
                # Restore domains
                self._restore_domains(old_domains)
            
            del assignment[variable]
        
        return None
    
    def _select_unassigned_variable_naive(self, assignment: Dict) -> Optional[CSPVariable]:
        """Select next unassigned variable naively (first available)."""
        for variable in self.variables:
            if variable not in assignment:
                return variable
        return None
    
    def _select_unassigned_variable_mrv(self, assignment: Dict) -> Optional[CSPVariable]:
        """Select unassigned variable with Minimum Remaining Values (MRV) heuristic."""
        unassigned = [v for v in self.variables if v not in assignment]
        if not unassigned:
            return None
        
        # Choose variable with smallest domain
        return min(unassigned, key=lambda v: len(v.domain))
    
    def _order_domain_values_lcv(self, variable: CSPVariable, assignment: Dict) -> List:
        """Order domain values using Least Constraining Value (LCV) heuristic."""
        def count_eliminated_values(value):
            """Count how many values would be eliminated from other variables' domains."""
            count = 0
            test_assignment = assignment.copy()
            test_assignment[variable] = value
            
            for other_var in self.variables:
                if other_var not in assignment and other_var != variable:
                    for other_value in other_var.domain:
                        test_assignment[other_var] = other_value
                        if not self._is_consistent(test_assignment):
                            count += 1
                        del test_assignment[other_var]
            
            return count
        
        # Sort by least constraining first (ascending order of eliminated values)
        return sorted(variable.domain, key=count_eliminated_values)
    
    def _forward_check(self, variable: CSPVariable, value: Tuple, 
                      assignment: Dict) -> Dict[CSPVariable, List]:
        """
        Perform forward checking by reducing domains of unassigned variables.
        Returns the old domains for backtracking.
        """
        old_domains = {}
        time_slot, classroom, faculty = value
        
        for other_var in self.variables:
            if other_var not in assignment and other_var != variable:
                old_domains[other_var] = other_var.domain.copy()
                new_domain = []
                
                for other_value in other_var.domain:
                    other_time, other_room, other_faculty = other_value
                    
                    # Check if this value would create a conflict
                    valid = True
                    if time_slot.overlaps_with(other_time):
                        if faculty.id == other_faculty.id or classroom.id == other_room.id:
                            valid = False
                    
                    if valid:
                        new_domain.append(other_value)
                
                other_var.domain = new_domain
        
        return old_domains
    
    def _restore_domains(self, old_domains: Dict[CSPVariable, List]):
        """Restore domains after backtracking."""
        for variable, domain in old_domains.items():
            variable.domain = domain
    
    def _is_consistent(self, assignment: Dict[CSPVariable, Tuple]) -> bool:
        """Check if the current assignment satisfies all constraints."""
        for constraint in self.constraints:
            if not constraint.is_satisfied(assignment):
                return False
        return True
    
    def _is_consistent_with_assignment(self, variable: CSPVariable, value: Tuple, 
                                     assignment: Dict) -> bool:
        """Check if assigning value to variable is consistent with current assignment."""
        test_assignment = assignment.copy()
        test_assignment[variable] = value
        return self._is_consistent(test_assignment)
    
    def _assignment_to_schedule(self, assignment: Dict[CSPVariable, Tuple]) -> Schedule:
        """Convert CSP assignment to Schedule object."""
        schedule = Schedule()
        
        for variable, (time_slot, classroom, faculty) in assignment.items():
            entry = ScheduleEntry(
                course=variable.course,
                faculty=faculty,
                classroom=classroom,
                time_slot=time_slot
            )
            schedule.add_entry(entry)
        
        schedule.calculate_optimization_score()
        return schedule
    
    def get_statistics(self) -> Dict:
        """Get solver statistics."""
        return {
            "nodes_explored": self.nodes_explored,
            "max_depth": self.max_depth,
            "total_variables": len(self.variables),
            "average_domain_size": sum(len(v.domain) for v in self.variables) / len(self.variables) if self.variables else 0
        }


class GreedySolver:
    """Greedy solver for timetable generation as an alternative to CSP."""
    
    def __init__(self, courses: List[Course], faculty: List[Faculty], 
                 classrooms: List[Classroom], time_slots: List[TimeSlot]):
        self.courses = courses
        self.faculty = faculty
        self.classrooms = classrooms
        self.time_slots = time_slots
    
    def solve(self) -> Schedule:
        """Solve using greedy approach - assign courses to best available slots."""
        schedule = Schedule()
        course_sessions = []
        
        # Create course sessions
        for course in self.courses:
            for session in range(course.sessions_per_week):
                course_sessions.append((course, session + 1))
        
        # Sort courses by priority (enrollment size, then by course type)
        course_sessions.sort(key=lambda x: (-x[0].enrolled_students, x[0].course_type.value))
        
        for course, session_num in course_sessions:
            best_assignment = self._find_best_assignment(course, schedule)
            
            if best_assignment:
                time_slot, classroom, faculty = best_assignment
                entry = ScheduleEntry(course, faculty, classroom, time_slot)
                schedule.add_entry(entry)
        
        schedule.calculate_optimization_score()
        return schedule
    
    def _find_best_assignment(self, course: Course, schedule: Schedule) -> Optional[Tuple]:
        """Find the best assignment for a course given the current schedule."""
        best_score = -1
        best_assignment = None
        
        # Find assigned faculty or available faculty
        assigned_faculty = None
        for faculty in self.faculty:
            if faculty.id == course.faculty_id:
                assigned_faculty = faculty
                break
        
        if not assigned_faculty:
            available_faculty = [f for f in self.faculty if f.department == course.department]
        else:
            available_faculty = [assigned_faculty]
        
        for time_slot in self.time_slots:
            for classroom in self.classrooms:
                for faculty in available_faculty:
                    # Check basic compatibility
                    if (faculty.is_available(time_slot) and 
                        course.is_compatible_with_room(classroom) and
                        time_slot.duration >= course.duration):
                        
                        # Create temporary entry to check conflicts
                        temp_entry = ScheduleEntry(course, faculty, classroom, time_slot)
                        conflicts = schedule.check_conflicts(temp_entry)
                        
                        if not conflicts:
                            # Calculate score for this assignment
                            score = self._calculate_assignment_score(course, faculty, classroom, time_slot)
                            
                            if score > best_score:
                                best_score = score
                                best_assignment = (time_slot, classroom, faculty)
        
        return best_assignment
    
    def _calculate_assignment_score(self, course: Course, faculty: Faculty, 
                                  classroom: Classroom, time_slot: TimeSlot) -> float:
        """Calculate score for an assignment (higher is better)."""
        score = 0.0
        
        # Faculty preference score
        score += faculty.get_preference_score(time_slot) * 10
        
        # Room utilization score
        capacity_utilization = course.enrolled_students / classroom.capacity
        if 0.7 <= capacity_utilization <= 1.0:  # Optimal utilization
            score += 20
        elif capacity_utilization < 0.7:
            score += 10 * capacity_utilization
        
        # Time slot preference (morning classes preferred)
        hour = int(time_slot.start_time.split(':')[0])
        if 9 <= hour <= 11:  # Morning preference
            score += 5
        elif 14 <= hour <= 16:  # Afternoon preference
            score += 3
        
        # Course type preference
        if course.course_type == CourseType.LAB and classroom.room_type == "Lab":
            score += 15
        
        return score