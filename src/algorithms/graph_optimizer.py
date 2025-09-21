"""
Graph-based optimization for timetable generation.
Uses graph theory concepts to detect conflicts and optimize schedules.
"""

import networkx as nx
from typing import List, Dict, Tuple, Set, Optional
import matplotlib.pyplot as plt
from collections import defaultdict

from models.data_models import (
    Course, Faculty, Classroom, TimeSlot, Schedule, ScheduleEntry,
    DayOfWeek, CourseType
)


class ConflictGraph:
    """Graph representation of scheduling conflicts between courses."""
    
    def __init__(self, courses: List[Course], faculty: List[Faculty], 
                 classrooms: List[Classroom], time_slots: List[TimeSlot]):
        self.courses = courses
        self.faculty = faculty
        self.classrooms = classrooms
        self.time_slots = time_slots
        
        # Create conflict graph
        self.graph = nx.Graph()
        self._build_conflict_graph()
    
    def _build_conflict_graph(self):
        """Build the conflict graph where nodes are courses and edges represent conflicts."""
        # Add nodes for each course session
        course_sessions = []
        for course in self.courses:
            for session in range(course.sessions_per_week):
                session_id = f"{course.id}_session_{session + 1}"
                course_sessions.append((session_id, course, session + 1))
                self.graph.add_node(session_id, course=course, session=session + 1)
        
        # Add edges for conflicts
        for i, (session1_id, course1, session1_num) in enumerate(course_sessions):
            for j, (session2_id, course2, session2_num) in enumerate(course_sessions[i+1:], i+1):
                if self._has_potential_conflict(course1, course2):
                    self.graph.add_edge(session1_id, session2_id, 
                                      conflict_type=self._get_conflict_type(course1, course2))
    
    def _has_potential_conflict(self, course1: Course, course2: Course) -> bool:
        """Check if two courses have potential conflicts."""
        # Same faculty conflict
        if course1.faculty_id == course2.faculty_id and course1.faculty_id:
            return True
        
        # Same department (might share faculty)
        if course1.department == course2.department:
            return True
        
        # Resource conflicts (lab equipment, room type)
        if (course1.course_type == CourseType.LAB and course2.course_type == CourseType.LAB and
            any(eq in course2.required_equipment for eq in course1.required_equipment)):
            return True
        
        return False
    
    def _get_conflict_type(self, course1: Course, course2: Course) -> str:
        """Determine the type of conflict between two courses."""
        if course1.faculty_id == course2.faculty_id and course1.faculty_id:
            return "faculty"
        elif course1.department == course2.department:
            return "department"
        elif (course1.course_type == CourseType.LAB and course2.course_type == CourseType.LAB):
            return "resource"
        return "general"
    
    def get_conflict_cliques(self) -> List[Set[str]]:
        """Find maximal cliques in the conflict graph."""
        return [set(clique) for clique in nx.find_cliques(self.graph)]
    
    def get_chromatic_number(self) -> int:
        """Get the chromatic number (minimum colors needed for graph coloring)."""
        try:
            # Use greedy coloring as approximation
            coloring = nx.greedy_color(self.graph, strategy='largest_first')
            return max(coloring.values()) + 1 if coloring else 0
        except:
            return len(self.graph.nodes())
    
    def color_graph(self) -> Dict[str, int]:
        """Color the graph to identify non-conflicting groups."""
        return nx.greedy_color(self.graph, strategy='largest_first')
    
    def visualize_graph(self, save_path: str = None):
        """Visualize the conflict graph."""
        plt.figure(figsize=(12, 8))
        
        # Create layout
        pos = nx.spring_layout(self.graph, k=1, iterations=50)
        
        # Color nodes by course department
        departments = set(self.graph.nodes[node]['course'].department for node in self.graph.nodes())
        color_map = {dept: i for i, dept in enumerate(departments)}
        node_colors = [color_map[self.graph.nodes[node]['course'].department] for node in self.graph.nodes()]
        
        # Draw the graph
        nx.draw(self.graph, pos, node_color=node_colors, node_size=500, 
                with_labels=True, font_size=8, font_weight='bold')
        
        # Add edge labels for conflict types
        edge_labels = nx.get_edge_attributes(self.graph, 'conflict_type')
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels, font_size=6)
        
        plt.title("Course Conflict Graph")
        plt.axis('off')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()


class GraphBasedOptimizer:
    """Uses graph theory to optimize timetable schedules."""
    
    def __init__(self, courses: List[Course], faculty: List[Faculty], 
                 classrooms: List[Classroom], time_slots: List[TimeSlot]):
        self.courses = courses
        self.faculty = faculty
        self.classrooms = classrooms
        self.time_slots = time_slots
        
        self.conflict_graph = ConflictGraph(courses, faculty, classrooms, time_slots)
    
    def optimize_schedule(self, initial_schedule: Schedule) -> Schedule:
        """Optimize an existing schedule using graph-based techniques."""
        optimized_schedule = Schedule()
        
        # Create assignment graph from current schedule
        assignment_graph = self._create_assignment_graph(initial_schedule)
        
        # Find and resolve conflicts using graph coloring
        colored_groups = self._resolve_conflicts_with_coloring(assignment_graph)
        
        # Reassign courses based on coloring
        for group_id, course_sessions in colored_groups.items():
            self._assign_courses_in_group(course_sessions, optimized_schedule)
        
        optimized_schedule.calculate_optimization_score()
        return optimized_schedule
    
    def _create_assignment_graph(self, schedule: Schedule) -> nx.Graph:
        """Create a graph from the current schedule assignments."""
        graph = nx.Graph()
        
        # Add nodes for each schedule entry
        for i, entry in enumerate(schedule.entries):
            node_id = f"{entry.course.id}_{i}"
            graph.add_node(node_id, entry=entry)
        
        # Add edges for conflicts
        for i, entry1 in enumerate(schedule.entries):
            for j, entry2 in enumerate(schedule.entries[i+1:], i+1):
                if self._entries_conflict(entry1, entry2):
                    node1 = f"{entry1.course.id}_{i}"
                    node2 = f"{entry2.course.id}_{j}"
                    graph.add_edge(node1, node2)
        
        return graph
    
    def _entries_conflict(self, entry1: ScheduleEntry, entry2: ScheduleEntry) -> bool:
        """Check if two schedule entries conflict."""
        if entry1.time_slot.overlaps_with(entry2.time_slot):
            return (entry1.faculty.id == entry2.faculty.id or 
                   entry1.classroom.id == entry2.classroom.id)
        return False
    
    def _resolve_conflicts_with_coloring(self, assignment_graph: nx.Graph) -> Dict[int, List]:
        """Use graph coloring to resolve conflicts."""
        coloring = nx.greedy_color(assignment_graph, strategy='largest_first')
        
        # Group assignments by color
        color_groups = defaultdict(list)
        for node_id, color in coloring.items():
            entry = assignment_graph.nodes[node_id]['entry']
            color_groups[color].append(entry)
        
        return color_groups
    
    def _assign_courses_in_group(self, course_entries: List[ScheduleEntry], 
                                schedule: Schedule):
        """Assign courses within a non-conflicting group."""
        for entry in course_entries:
            # Try to find a better assignment for this entry
            better_assignment = self._find_better_assignment(entry, schedule)
            
            if better_assignment:
                new_entry = ScheduleEntry(*better_assignment)
                schedule.add_entry(new_entry)
            else:
                schedule.add_entry(entry)
    
    def _find_better_assignment(self, original_entry: ScheduleEntry, 
                               current_schedule: Schedule) -> Optional[Tuple]:
        """Find a better assignment for a course."""
        course = original_entry.course
        best_score = -1
        best_assignment = None
        
        # Get available faculty
        if course.faculty_id:
            available_faculty = [f for f in self.faculty if f.id == course.faculty_id]
        else:
            available_faculty = [f for f in self.faculty if f.department == course.department]
        
        for time_slot in self.time_slots:
            for classroom in self.classrooms:
                for faculty in available_faculty:
                    if (faculty.is_available(time_slot) and 
                        course.is_compatible_with_room(classroom)):
                        
                        temp_entry = ScheduleEntry(course, faculty, classroom, time_slot)
                        conflicts = current_schedule.check_conflicts(temp_entry)
                        
                        if not conflicts:
                            score = self._calculate_assignment_score(course, faculty, classroom, time_slot)
                            if score > best_score:
                                best_score = score
                                best_assignment = (course, faculty, classroom, time_slot)
        
        return best_assignment
    
    def _calculate_assignment_score(self, course: Course, faculty: Faculty, 
                                  classroom: Classroom, time_slot: TimeSlot) -> float:
        """Calculate optimization score for an assignment."""
        score = 0.0
        
        # Faculty preference
        score += faculty.get_preference_score(time_slot) * 10
        
        # Room utilization
        utilization = course.enrolled_students / classroom.capacity
        if 0.7 <= utilization <= 1.0:
            score += 20
        else:
            score += 10 * utilization
        
        # Time preference (avoid early morning and late evening)
        hour = int(time_slot.start_time.split(':')[0])
        if 9 <= hour <= 16:
            score += 5
        
        # Course type compatibility
        if course.course_type == CourseType.LAB and classroom.room_type == "Lab":
            score += 15
        
        return score
    
    def get_schedule_metrics(self, schedule: Schedule) -> Dict:
        """Get graph-based metrics for a schedule."""
        assignment_graph = self._create_assignment_graph(schedule)
        
        return {
            "total_conflicts": len(assignment_graph.edges()),
            "conflict_density": nx.density(assignment_graph),
            "largest_conflict_component": len(max(nx.connected_components(assignment_graph), 
                                                 key=len, default=[])),
            "chromatic_number_estimate": self.conflict_graph.get_chromatic_number(),
            "clustering_coefficient": nx.average_clustering(assignment_graph) if assignment_graph.nodes() else 0
        }
    
    def suggest_schedule_improvements(self, schedule: Schedule) -> List[str]:
        """Suggest improvements based on graph analysis."""
        suggestions = []
        metrics = self.get_schedule_metrics(schedule)
        
        if metrics["total_conflicts"] > 0:
            suggestions.append(f"Schedule has {metrics['total_conflicts']} conflicts that need resolution")
        
        if metrics["conflict_density"] > 0.5:
            suggestions.append("High conflict density - consider redistributing courses across time slots")
        
        if metrics["largest_conflict_component"] > 5:
            suggestions.append("Large conflict cluster detected - may need manual intervention")
        
        # Check for resource utilization
        room_utilization = schedule.calculate_room_utilization()
        if room_utilization < 0.6:
            suggestions.append("Low room utilization - consider consolidating courses")
        
        return suggestions
    
    def find_optimal_time_slots(self) -> List[TimeSlot]:
        """Find optimal time slots based on faculty availability and preferences."""
        slot_scores = {}
        
        for time_slot in self.time_slots:
            score = 0
            available_faculty_count = 0
            
            for faculty in self.faculty:
                if faculty.is_available(time_slot):
                    available_faculty_count += 1
                    score += faculty.get_preference_score(time_slot)
            
            # Normalize by number of available faculty
            if available_faculty_count > 0:
                slot_scores[time_slot] = score / available_faculty_count
            else:
                slot_scores[time_slot] = 0
        
        # Sort by score and return top slots
        sorted_slots = sorted(slot_scores.items(), key=lambda x: x[1], reverse=True)
        return [slot for slot, _ in sorted_slots[:len(sorted_slots)//2]]  # Top 50%


class TimeSlotOptimizer:
    """Optimizes time slot distribution using graph theory."""
    
    def __init__(self, time_slots: List[TimeSlot], courses: List[Course]):
        self.time_slots = time_slots
        self.courses = courses
        
        # Create bipartite graph for time slot assignment
        self.bipartite_graph = nx.Graph()
        self._build_bipartite_graph()
    
    def _build_bipartite_graph(self):
        """Build bipartite graph with courses and time slots."""
        # Add course nodes
        for course in self.courses:
            for session in range(course.sessions_per_week):
                course_session_id = f"{course.id}_session_{session + 1}"
                self.bipartite_graph.add_node(course_session_id, bipartite=0, 
                                            course=course, session=session + 1)
        
        # Add time slot nodes
        for time_slot in self.time_slots:
            self.bipartite_graph.add_node(time_slot.id, bipartite=1, time_slot=time_slot)
        
        # Add edges based on compatibility
        for course in self.courses:
            for session in range(course.sessions_per_week):
                course_session_id = f"{course.id}_session_{session + 1}"
                for time_slot in self.time_slots:
                    if time_slot.duration >= course.duration:
                        self.bipartite_graph.add_edge(course_session_id, time_slot.id)
    
    def find_maximum_matching(self) -> Dict[str, str]:
        """Find maximum matching between courses and time slots."""
        course_nodes = [n for n, d in self.bipartite_graph.nodes(data=True) if d['bipartite'] == 0]
        try:
            matching = nx.bipartite.maximum_matching(self.bipartite_graph, course_nodes)
            return matching
        except:
            return {}
    
    def get_time_slot_utilization(self, schedule: Schedule) -> Dict[str, float]:
        """Calculate utilization for each time slot."""
        slot_usage = defaultdict(int)
        slot_capacity = {}
        
        # Initialize capacity
        for time_slot in self.time_slots:
            slot_capacity[time_slot.id] = len([c for c in self.courses 
                                             if time_slot.duration >= c.duration])
        
        # Count usage
        for entry in schedule.entries:
            slot_usage[entry.time_slot.id] += 1
        
        # Calculate utilization
        utilization = {}
        for time_slot in self.time_slots:
            if slot_capacity[time_slot.id] > 0:
                utilization[time_slot.id] = slot_usage[time_slot.id] / slot_capacity[time_slot.id]
            else:
                utilization[time_slot.id] = 0
        
        return utilization