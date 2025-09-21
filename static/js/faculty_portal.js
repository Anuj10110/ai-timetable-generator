let availabilityData = {};

function toggleAvailability(element) {
    const day = element.dataset.day;
    const time = element.dataset.time;
    
    if (element.classList.contains('available')) {
        element.classList.remove('available');
        element.classList.add('unavailable');
        
        if (!availabilityData[day]) {
            availabilityData[day] = {};
        }
        availabilityData[day][time] = false;
    } else {
        element.classList.remove('unavailable');
        element.classList.add('available');
        
        if (!availabilityData[day]) {
            availabilityData[day] = {};
        }
        availabilityData[day][time] = true;
    }
    
    // Update hidden input
    document.getElementById('availability_data').value = JSON.stringify(availabilityData);
}

function viewCourseDetails(courseCode) {
    alert(`Viewing details for course: ${courseCode}\n\nThis feature will be implemented to show:\n- Student list\n- Course materials\n- Grades and assignments\n- Attendance records`);
}

// Initialize all slots as available
document.addEventListener('DOMContentLoaded', function() {
    const slots = document.querySelectorAll('.time-slot');
    slots.forEach(slot => {
        const day = slot.dataset.day;
        const time = slot.dataset.time;
        
        if (!availabilityData[day]) {
            availabilityData[day] = {};
        }
        availabilityData[day][time] = true;
    });
    
    document.getElementById('availability_data').value = JSON.stringify(availabilityData);
});