// Update statistics on page load
document.addEventListener('DOMContentLoaded', function() {
    updateStats();
});

function updateStats() {
    // Get data counts from session storage or make API calls
    const courses = JSON.parse(sessionStorage.getItem('courses') || '[]');
    const faculty = JSON.parse(sessionStorage.getItem('faculty') || '[]');
    const classrooms = JSON.parse(sessionStorage.getItem('classrooms') || '[]');
    
    document.getElementById('courseCount').textContent = courses.length || 0;
    document.getElementById('facultyCount').textContent = faculty.length || 0;
    document.getElementById('classroomCount').textContent = classrooms.length || 0;
}

function clearAllData() {
    if (confirm('Are you sure you want to clear all data? This cannot be undone.')) {
        fetch('/api/clear_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                sessionStorage.clear();
                alert('All data cleared successfully!');
                updateStats();
                location.reload();
            }
        })
        .catch(error => {
            alert('Error clearing data: ' + error.message);
        });
    }
}

function exportData() {
    // Implementation for data export
    alert('Export functionality coming soon!');
}

function showHelp() {
    alert('Help: 1. Add courses, faculty, and classrooms. 2. Use the Generate Timetable feature. 3. Review and optimize the results.');
}