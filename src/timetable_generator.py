"""
Main timetable generation engine that orchestrates the entire process.
Combines CSP solving, graph optimization, and various heuristics.
"""

from typing import List, Dict, Optional, Tuple
import time
from enum import Enum
import logging

from models.data_models import (
    Course, Faculty, Classroom, TimeSlot, Schedule, ScheduleEntry,
    DayOfWeek, CourseType
)
from algorithms.csp_solver import CSPSolver, GreedySolver
from algorithms.graph_optimizer import GraphBasedOptimizer, ConflictGraph


class SolverType(Enum):
    CSP_BACKTRACKING = "csp_backtracking"
    GREEDY = "greedy"
    HYBRID = "hybrid"


class TimetableGenerator:
    """Main class for generating optimized timetables."""
    
    def __init__(self):
        self.courses: List[Course] = []
        self.faculty: List[Faculty] = []
        self.classrooms: List[Classroom] = []
        self.time_slots: List[TimeSlot] = []
        
        # Optimization components
        self.csp_solver: Optional[CSPSolver] = None
        self.greedy_solver: Optional[GreedySolver] = None
        self.graph_optimizer: Optional[GraphBasedOptimizer] = None
        
        # Generation statistics
        self.generation_stats = {}
        
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
        
        # Initialize solvers
        self.csp_solver = CSPSolver(courses, faculty, classrooms, time_slots)
        self.greedy_solver = GreedySolver(courses, faculty, classrooms, time_slots)
        self.graph_optimizer = GraphBasedOptimizer(courses, faculty, classrooms, time_slots)
        
        self.logger.info(f"Initialized with {len(courses)} courses, {len(faculty)} faculty, "
                        f"{len(classrooms)} classrooms, {len(time_slots)} time slots")
    
    def generate_timetable(self, solver_type: SolverType = SolverType.HYBRID, 
                          max_time: int = 300, optimize: bool = True) -> Optional[Schedule]:
        """
        Generate a timetable using the specified solver.
        
        Args:
            solver_type: Type of solver to use
            max_time: Maximum time to spend on generation (seconds)
            optimize: Whether to apply graph-based optimization
            
        Returns:
            Generated schedule or None if no solution found
        """
        start_time = time.time()
        
        # Validate input data
        if not self._validate_input_data():
            self.logger.error("Input data validation failed")
            return None
        
        schedule = None
        
        try:
            if solver_type == SolverType.CSP_BACKTRACKING:
                schedule = self._generate_with_csp(max_time)
            elif solver_type == SolverType.GREEDY:
                schedule = self._generate_with_greedy()
            elif solver_type == SolverType.HYBRID:
                schedule = self._generate_with_hybrid_approach(max_time)
            
            if schedule and optimize:
                self.logger.info("Applying graph-based optimization...")
                schedule = self.graph_optimizer.optimize_schedule(schedule)
            
        except Exception as e:
            self.logger.error(f"Error during timetable generation: {str(e)}")
            return None
        
        generation_time = time.time() - start_time
        
        # Record statistics
        self.generation_stats = {
            "solver_type": solver_type.value,
            "generation_time": generation_time,
            "total_entries": len(schedule.entries) if schedule else 0,
            "total_conflicts": len(schedule.conflicts) if schedule else 0,
            "optimization_score": schedule.optimization_score if schedule else 0,
            "is_valid": schedule.is_valid() if schedule else False
        }
        
        if schedule:
            self.logger.info(f"Timetable generated successfully in {generation_time:.2f}s")
            self.logger.info(f"Schedule: {len(schedule.entries)} entries, "
                           f"{len(schedule.conflicts)} conflicts, "
                           f"Score: {schedule.optimization_score:.2f}")
        else:
            self.logger.warning("Failed to generate a valid timetable")
        
        return schedule
    
    def _validate_input_data(self) -> bool:
        """Validate that input data is sufficient for timetable generation."""
        if not self.courses:
            self.logger.error("No courses provided")
            return False
        
        if not self.faculty:
            self.logger.error("No faculty provided")
            return False
        
        if not self.classrooms:
            self.logger.error("No classrooms provided")
            return False
        
        if not self.time_slots:
            self.logger.error("No time slots provided")
            return False
        
        # Check if there are enough resources
        total_course_sessions = sum(course.sessions_per_week for course in self.courses)
        available_slots = len(self.time_slots)
        
        if total_course_sessions > available_slots * len(self.classrooms):
            self.logger.warning("May not have enough time slots and classrooms for all courses")
        
        # Check faculty assignments
        unassigned_courses = [c for c in self.courses if not c.faculty_id]
        if unassigned_courses:
            self.logger.info(f"{len(unassigned_courses)} courses without specific faculty assignment")
        
        return True
    
    def _generate_with_csp(self, max_time: int) -> Optional[Schedule]:
        """Generate timetable using CSP solver."""
        self.logger.info("Generating timetable using CSP backtracking algorithm...")
        
        schedule = self.csp_solver.solve(use_heuristics=True, max_time=max_time)
        
        if schedule:
            stats = self.csp_solver.get_statistics()
            self.logger.info(f"CSP solver explored {stats['nodes_explored']} nodes, "
                           f"max depth: {stats['max_depth']}")
        
        return schedule
    
    def _generate_with_greedy(self) -> Schedule:
        """Generate timetable using greedy solver."""
        self.logger.info("Generating timetable using greedy algorithm...")
        
        schedule = self.greedy_solver.solve()
        return schedule
    
    def _generate_with_hybrid_approach(self, max_time: int) -> Optional[Schedule]:
        """Generate timetable using hybrid approach (CSP + Greedy fallback)."""
        self.logger.info("Generating timetable using hybrid approach...")
        
        # First try CSP with limited time
        csp_time_limit = min(max_time // 2, 180)  # Use half time or max 3 minutes for CSP
        
        schedule = self.csp_solver.solve(use_heuristics=True, max_time=csp_time_limit)
        
        if not schedule or not schedule.is_valid():
            self.logger.info("CSP solver didn't find valid solution, trying greedy approach...")
            schedule = self.greedy_solver.solve()
        
        return schedule
    
    def get_generation_statistics(self) -> Dict:
        """Get detailed statistics about the last generation process."""
        stats = self.generation_stats.copy()
        
        if self.csp_solver:
            stats.update({
                "csp_stats": self.csp_solver.get_statistics()
            })
        
        return stats
    
    def analyze_schedule(self, schedule: Schedule) -> Dict:
        """Perform detailed analysis of a generated schedule."""
        if not schedule:
            return {"error": "No schedule provided"}
        
        analysis = {
            "basic_stats": schedule.get_summary(),
            "faculty_workload": self._analyze_faculty_workload(schedule),
            "classroom_utilization": self._analyze_classroom_utilization(schedule),
            "time_distribution": self._analyze_time_distribution(schedule),
        }
        
        if self.graph_optimizer:
            analysis["graph_metrics"] = self.graph_optimizer.get_schedule_metrics(schedule)
            analysis["improvement_suggestions"] = self.graph_optimizer.suggest_schedule_improvements(schedule)
        
        return analysis
    
    def _analyze_faculty_workload(self, schedule: Schedule) -> Dict:
        """Analyze workload distribution among faculty."""
        faculty_hours = {}
        faculty_courses = {}
        
        for entry in schedule.entries:
            faculty_id = entry.faculty.id
            course_duration = entry.course.duration / 60  # Convert to hours
            
            if faculty_id not in faculty_hours:
                faculty_hours[faculty_id] = 0
                faculty_courses[faculty_id] = []
            
            faculty_hours[faculty_id] += course_duration
            faculty_courses[faculty_id].append(entry.course.code)
        
        # Calculate statistics
        if faculty_hours:
            avg_hours = sum(faculty_hours.values()) / len(faculty_hours)
            max_hours = max(faculty_hours.values())
            min_hours = min(faculty_hours.values())
        else:
            avg_hours = max_hours = min_hours = 0
        
        return {
            "faculty_hours": faculty_hours,
            "faculty_courses": faculty_courses,
            "average_hours": avg_hours,
            "max_hours": max_hours,
            "min_hours": min_hours,
            "workload_distribution": "balanced" if max_hours - min_hours <= 5 else "unbalanced"
        }
    
    def _analyze_classroom_utilization(self, schedule: Schedule) -> Dict:
        """Analyze classroom utilization patterns."""
        room_usage = {}
        room_hours = {}
        
        for entry in schedule.entries:
            room_id = entry.classroom.id
            room_name = entry.classroom.name
            duration = entry.time_slot.duration / 60  # Convert to hours
            
            if room_id not in room_usage:
                room_usage[room_id] = {
                    "name": room_name,
                    "sessions": 0,
                    "courses": []
                }
                room_hours[room_id] = 0
            
            room_usage[room_id]["sessions"] += 1
            room_usage[room_id]["courses"].append(entry.course.code)
            room_hours[room_id] += duration
        
        # Calculate utilization rates
        total_available_hours = len(self.time_slots) * sum(slot.duration for slot in self.time_slots) / 60
        
        utilization_rates = {}
        for room_id, hours in room_hours.items():
            utilization_rates[room_id] = hours / total_available_hours if total_available_hours > 0 else 0
        
        return {
            "room_usage": room_usage,
            "room_hours": room_hours,
            "utilization_rates": utilization_rates,
            "average_utilization": sum(utilization_rates.values()) / len(utilization_rates) if utilization_rates else 0
        }
    
    def _analyze_time_distribution(self, schedule: Schedule) -> Dict:
        """Analyze distribution of courses across time slots."""
        time_distribution = {}
        day_distribution = {}
        
        for entry in schedule.entries:
            time_slot = entry.time_slot
            day = time_slot.day.value
            hour = int(time_slot.start_time.split(':')[0])
            
            # Time slot distribution
            slot_key = f"{day} {time_slot.start_time}-{time_slot.end_time}"
            if slot_key not in time_distribution:
                time_distribution[slot_key] = 0
            time_distribution[slot_key] += 1
            
            # Day distribution
            if day not in day_distribution:
                day_distribution[day] = 0
            day_distribution[day] += 1
        
        return {
            "time_slot_distribution": time_distribution,
            "day_distribution": day_distribution,
            "peak_times": self._find_peak_times(time_distribution),
            "balanced_distribution": self._check_time_balance(day_distribution)
        }
    
    def _find_peak_times(self, time_distribution: Dict) -> List[str]:
        """Find peak time slots with highest course load."""
        if not time_distribution:
            return []
        
        max_courses = max(time_distribution.values())
        peak_times = [time_slot for time_slot, count in time_distribution.items() 
                     if count == max_courses]
        
        return peak_times
    
    def _check_time_balance(self, day_distribution: Dict) -> bool:
        """Check if courses are evenly distributed across days."""
        if not day_distribution:
            return True
        
        values = list(day_distribution.values())
        avg = sum(values) / len(values)
        
        # Consider balanced if all values are within 20% of average
        return all(abs(v - avg) / avg <= 0.2 for v in values if avg > 0)
    
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
            "generation_stats": self.generation_stats
        }