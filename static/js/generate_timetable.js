let currentSchedule = null;
let currentAnalysis = null;

// Load data on page load
document.addEventListener('DOMContentLoaded', function() {
    loadCoursesAndFaculty();
    setupSelectionHandlers();
});

// Load courses, faculty, and batches data
async function loadCoursesAndFaculty() {
    try {
        // Get session data (courses, faculty, and batches are stored in session)
        await loadCourses();
        await loadFaculty();
        await loadBatches();
    } catch (error) {
        console.error('Error loading data:', error);
    }
}

// Load courses from backend
async function loadCourses() {
    try {
        const response = await fetch('/api/courses');
        const data = await response.json();
        const courses = data.courses || [];
        
        const coursesList = document.getElementById('coursesList');
        coursesList.innerHTML = '';
        
        if (courses.length === 0) {
            coursesList.innerHTML = '<p class="text-muted">No courses available. Please add courses first.</p>';
            return;
        }
        
        courses.forEach(course => {
            const courseItem = document.createElement('div');
            courseItem.className = 'form-check course-item';
            courseItem.innerHTML = `
                <input class="form-check-input course-checkbox" type="checkbox" 
                       value="${course.id}" id="course_${course.id}" checked>
                <label class="form-check-label" for="course_${course.id}">
                    <div class="item-details">
                        <div class="item-name">${course.code} - ${course.name}</div>
                        <div class="item-meta">${course.department} | ${course.credits} credits | ${course.course_type}</div>
                    </div>
                </label>
            `;
            coursesList.appendChild(courseItem);
        });
    } catch (error) {
        console.error('Error loading courses:', error);
        const coursesList = document.getElementById('coursesList');
        coursesList.innerHTML = '<p class="text-danger">Error loading courses. Please refresh the page.</p>';
    }
}

// Load faculty from backend
async function loadFaculty() {
    try {
        const response = await fetch('/api/faculty');
        const data = await response.json();
        const faculty = data.faculty || [];
        
        const facultyList = document.getElementById('facultyList');
        facultyList.innerHTML = '';
        
        if (faculty.length === 0) {
            facultyList.innerHTML = '<p class="text-muted">No faculty available. Please add faculty first.</p>';
            return;
        }
        
        faculty.forEach(member => {
            const facultyItem = document.createElement('div');
            facultyItem.className = 'form-check faculty-item';
            facultyItem.innerHTML = `
                <input class="form-check-input faculty-checkbox" type="checkbox" 
                       value="${member.id}" id="faculty_${member.id}" checked>
                <label class="form-check-label" for="faculty_${member.id}">
                    <div class="item-details">
                        <div class="item-name">${member.name}</div>
                        <div class="item-meta">${member.department} | ${member.email}</div>
                    </div>
                </label>
            `;
            facultyList.appendChild(facultyItem);
        });
    } catch (error) {
        console.error('Error loading faculty:', error);
        const facultyList = document.getElementById('facultyList');
        facultyList.innerHTML = '<p class="text-danger">Error loading faculty. Please refresh the page.</p>';
    }
}

// Load batches from backend
async function loadBatches() {
    try {
        const response = await fetch('/api/batches');
        const data = await response.json();
        const batches = data.batches || [];
        
        const batchesList = document.getElementById('batchesList');
        batchesList.innerHTML = '';
        
        if (batches.length === 0) {
            batchesList.innerHTML = '<p class="text-muted">No batches available. Please add batches first.</p>';
            return;
        }
        
        batches.forEach(batch => {
            const batchItem = document.createElement('div');
            batchItem.className = 'form-check batch-item';
            batchItem.innerHTML = `
                <input class="form-check-input batch-checkbox" type="checkbox" 
                       value="${batch.id}" id="batch_${batch.id}" checked>
                <label class="form-check-label" for="batch_${batch.id}">
                    <div class="item-details">
                        <div class="item-name">${batch.name}</div>
                        <div class="item-meta">${batch.department} | ${batch.semester} | ${batch.student_count} students</div>
                    </div>
                </label>
            `;
            batchesList.appendChild(batchItem);
        });
    } catch (error) {
        console.error('Error loading batches:', error);
        const batchesList = document.getElementById('batchesList');
        batchesList.innerHTML = '<p class="text-danger">Error loading batches. Please refresh the page.</p>';
    }
}

// Setup selection handlers
function setupSelectionHandlers() {
    // Handle "Select All Courses"
    const selectAllCourses = document.getElementById('selectAllCourses');
    if (selectAllCourses) {
        selectAllCourses.addEventListener('change', function() {
            const courseCheckboxes = document.querySelectorAll('.course-checkbox');
            courseCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
    }
    
    // Handle "Select All Faculty"
    const selectAllFaculty = document.getElementById('selectAllFaculty');
    if (selectAllFaculty) {
        selectAllFaculty.addEventListener('change', function() {
            const facultyCheckboxes = document.querySelectorAll('.faculty-checkbox');
            facultyCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
    }
    
    // Handle "Select All Batches"
    const selectAllBatches = document.getElementById('selectAllBatches');
    if (selectAllBatches) {
        selectAllBatches.addEventListener('change', function() {
            const batchCheckboxes = document.querySelectorAll('.batch-checkbox');
            batchCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
    }
    
    // Handle individual checkboxes
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('course-checkbox')) {
            updateSelectAllState('courses');
        } else if (e.target.classList.contains('faculty-checkbox')) {
            updateSelectAllState('faculty');
        } else if (e.target.classList.contains('batch-checkbox')) {
            updateSelectAllState('batches');
        }
    });
}

// Update "Select All" state based on individual selections
function updateSelectAllState(type) {
    let selectAllId, checkboxClass;
    
    switch(type) {
        case 'courses':
            selectAllId = 'selectAllCourses';
            checkboxClass = '.course-checkbox';
            break;
        case 'faculty':
            selectAllId = 'selectAllFaculty';
            checkboxClass = '.faculty-checkbox';
            break;
        case 'batches':
            selectAllId = 'selectAllBatches';
            checkboxClass = '.batch-checkbox';
            break;
    }
    
    const selectAll = document.getElementById(selectAllId);
    const checkboxes = document.querySelectorAll(checkboxClass);
    
    const checkedCount = document.querySelectorAll(`${checkboxClass}:checked`).length;
    
    if (checkedCount === 0) {
        selectAll.indeterminate = false;
        selectAll.checked = false;
    } else if (checkedCount === checkboxes.length) {
        selectAll.indeterminate = false;
        selectAll.checked = true;
    } else {
        selectAll.indeterminate = true;
        selectAll.checked = false;
    }
}

// Get selected courses, faculty, and batches
function getSelectedItems() {
    const selectedCourses = Array.from(document.querySelectorAll('.course-checkbox:checked'))
        .map(checkbox => checkbox.value);
    const selectedFaculty = Array.from(document.querySelectorAll('.faculty-checkbox:checked'))
        .map(checkbox => checkbox.value);
    const selectedBatches = Array.from(document.querySelectorAll('.batch-checkbox:checked'))
        .map(checkbox => checkbox.value);
    
    return { selectedCourses, selectedFaculty, selectedBatches };
}

async function generateTimetable() {
    const generateBtn = document.getElementById('generateBtn');
    const loadingSpinner = document.querySelector('.loading-spinner');
    const initialMessage = document.getElementById('initialMessage');
    const resultsSection = document.getElementById('resultsSection');
    const statusCard = document.getElementById('statusCard');
    
    // Disable button and show loading
    generateBtn.disabled = true;
    loadingSpinner.style.display = 'block';
    initialMessage.style.display = 'none';
    resultsSection.style.display = 'none';
    statusCard.style.display = 'none';
    
    // Get configuration
    const { selectedCourses, selectedFaculty, selectedBatches } = getSelectedItems();
    
    // Validate selections
    if (selectedCourses.length === 0) {
        alert('Please select at least one course for timetable generation.');
        generateBtn.disabled = false;
        loadingSpinner.style.display = 'none';
        return;
    }
    
    if (selectedFaculty.length === 0) {
        alert('Please select at least one faculty member for timetable generation.');
        generateBtn.disabled = false;
        loadingSpinner.style.display = 'none';
        return;
    }
    
    if (selectedBatches.length === 0) {
        alert('Please select at least one batch for timetable generation.');
        generateBtn.disabled = false;
        loadingSpinner.style.display = 'none';
        return;
    }
    
    const config = {
        solver_type: document.getElementById('solverType').value,
        max_time: parseInt(document.getElementById('maxTime').value),
        optimize: document.getElementById('optimize').value === 'true',
        selected_courses: selectedCourses,
        selected_faculty: selectedFaculty,
        selected_batches: selectedBatches
    };
    
    // Simulate progress
    simulateProgress();
    
    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentSchedule = data.schedule;
            currentAnalysis = data.analysis;
            displaySchedule(data.schedule);
            displayStatus(data.statistics, true);
        } else {
            displayStatus({ error: data.error }, false);
        }
        
    } catch (error) {
        console.error('Generation error:', error);
        displayStatus({ error: 'Network error occurred' }, false);
    } finally {
        generateBtn.disabled = false;
        loadingSpinner.style.display = 'none';
    }
}

function simulateProgress() {
    const progressBar = document.getElementById('progressBar');
    const statusText = document.getElementById('statusText');
    
    let progress = 0;
    const statuses = [
        { text: 'Analyzing problem complexity...', icon: '🧠' },
        { text: 'Selecting optimal algorithm...', icon: '⚡' },
        { text: 'Processing course constraints...', icon: '📊' },
        { text: 'Checking faculty availability...', icon: '👥' },
        { text: 'Optimizing room assignments...', icon: '🏫' },
        { text: 'Applying intelligent scheduling...', icon: '🎯' },
        { text: 'Finalizing optimal schedule...', icon: '✨' }
    ];
    
    let currentStatusIndex = 0;
    
    const interval = setInterval(() => {
        const increment = Math.random() * 15 + 5; // 5-20% increments
        progress = Math.min(progress + increment, 95);
        
        // Animate progress bar with easing
        progressBar.style.transition = 'width 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
        progressBar.style.width = progress + '%';
        
        // Update status with animation
        const newStatusIndex = Math.min(Math.floor(progress / 15), statuses.length - 1);
        if (newStatusIndex !== currentStatusIndex) {
            currentStatusIndex = newStatusIndex;
            const status = statuses[currentStatusIndex];
            
            // Animate status text change
            statusText.style.opacity = '0';
            statusText.style.transform = 'translateY(10px)';
            
            setTimeout(() => {
                statusText.innerHTML = `<span style="margin-right: 8px;">${status.icon}</span>${status.text}`;
                statusText.style.opacity = '1';
                statusText.style.transform = 'translateY(0)';
                statusText.style.transition = 'all 0.3s ease';
            }, 150);
        }
        
        // Add particle effect
        createProgressParticle();
        
        if (progress >= 95) {
            clearInterval(interval);
            // Complete progress bar
            setTimeout(() => {
                progressBar.style.width = '100%';
                statusText.innerHTML = '<span style="margin-right: 8px;">🎉</span>Generation complete!';
                statusText.style.color = '#28a745';
            }, 300);
        }
    }, 800);
}

function createProgressParticle() {
    const progressContainer = document.querySelector('.progress')?.parentElement;
    if (!progressContainer) return;
    
    const particle = document.createElement('div');
    particle.style.cssText = `
        position: absolute;
        width: 4px;
        height: 4px;
        background: linear-gradient(45deg, #667eea, #764ba2);
        border-radius: 50%;
        pointer-events: none;
        z-index: 10;
        animation: particleFloat 2s ease-out forwards;
    `;
    
    const progressBar = document.getElementById('progressBar');
    const rect = progressBar.getBoundingClientRect();
    particle.style.left = (rect.width * Math.random()) + 'px';
    particle.style.top = '50%';
    
    progressContainer.style.position = 'relative';
    progressContainer.appendChild(particle);
    
    // Add particle animation
    const style = document.createElement('style');
    if (!document.querySelector('#particle-animation')) {
        style.id = 'particle-animation';
        style.textContent = `
            @keyframes particleFloat {
                0% {
                    opacity: 1;
                    transform: translateY(0) scale(1);
                }
                100% {
                    opacity: 0;
                    transform: translateY(-30px) scale(0.5);
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    setTimeout(() => particle.remove(), 2000);
}

function displaySchedule(schedule) {
    const resultsSection = document.getElementById('resultsSection');
    const scheduleBody = document.getElementById('scheduleBody');
    const totalEntries = document.getElementById('totalEntries');
    const optimizationScore = document.getElementById('optimizationScore');
    
    // Update summary
    totalEntries.textContent = schedule.entries.length;
    optimizationScore.textContent = schedule.summary.optimization_score.toFixed(1);
    
    // Clear existing table
    scheduleBody.innerHTML = '';
    
    // Group entries by time slot
    const timeSlots = {};
    schedule.entries.forEach(entry => {
        const timeKey = `${entry.time_slot.start_time}-${entry.time_slot.end_time}`;
        if (!timeSlots[timeKey]) {
            timeSlots[timeKey] = {};
        }
        timeSlots[timeKey][entry.time_slot.day] = entry;
    });
    
    // Create table rows
    Object.keys(timeSlots).sort().forEach(timeKey => {
        const row = document.createElement('tr');
        const timeCell = document.createElement('td');
        timeCell.innerHTML = `<strong>${timeKey}</strong>`;
        row.appendChild(timeCell);
        
        ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'].forEach(day => {
            const cell = document.createElement('td');
            const entry = timeSlots[timeKey][day];
            
            if (entry) {
                cell.innerHTML = `
                    <div class="course-badge course-code">${entry.course.code}</div><br>
                    <div class="faculty-name">${entry.faculty.name}</div>
                    <div class="room-info">${entry.classroom.name}</div>
                `;
            }
            
            row.appendChild(cell);
        });
        
        scheduleBody.appendChild(row);
    });
    
    resultsSection.style.display = 'block';
}

function displayStatus(statistics, success) {
    const statusCard = document.getElementById('statusCard');
    const statusContent = document.getElementById('statusContent');
    
    let content = '';
    if (success) {
        content = `
            <div class="text-success mb-2">
                <i class="fas fa-check-circle me-2"></i><strong>Generation Successful!</strong>
            </div>
            <small class="text-muted">
                Generated in ${statistics.generation_time ? statistics.generation_time.toFixed(2) : 'N/A'}s<br>
                Algorithm: ${statistics.solver_type}<br>
                Total entries: ${statistics.total_entries}
            </small>
        `;
    } else {
        content = `
            <div class="text-danger mb-2">
                <i class="fas fa-exclamation-triangle me-2"></i><strong>Generation Failed</strong>
            </div>
            <small class="text-muted">${statistics.error}</small>
        `;
    }
    
    statusContent.innerHTML = content;
    statusCard.style.display = 'block';
}

function exportSchedule() {
    if (!currentSchedule) return;
    
    const dataStr = JSON.stringify(currentSchedule, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = 'timetable_schedule.json';
    link.click();
    
    URL.revokeObjectURL(url);
}

function showAnalysis() {
    if (!currentAnalysis) return;
    
    const modal = new bootstrap.Modal(document.getElementById('analysisModal'));
    const content = document.getElementById('analysisContent');
    
    let analysisHTML = '<h6>Basic Statistics</h6>';
    analysisHTML += `<ul>`;
    analysisHTML += `<li>Total Entries: ${currentAnalysis.basic_stats.total_entries}</li>`;
    analysisHTML += `<li>Conflicts: ${currentAnalysis.basic_stats.total_conflicts}</li>`;
    analysisHTML += `<li>Room Utilization: ${(currentAnalysis.basic_stats.room_utilization * 100).toFixed(1)}%</li>`;
    analysisHTML += `<li>Valid Schedule: ${currentAnalysis.basic_stats.is_valid ? 'Yes' : 'No'}</li>`;
    analysisHTML += `</ul>`;
    
    if (currentAnalysis.improvement_suggestions && currentAnalysis.improvement_suggestions.length > 0) {
        analysisHTML += '<h6>Improvement Suggestions</h6>';
        analysisHTML += '<ul>';
        currentAnalysis.improvement_suggestions.forEach(suggestion => {
            analysisHTML += `<li>${suggestion}</li>`;
        });
        analysisHTML += '</ul>';
    }
    
    content.innerHTML = analysisHTML;
    modal.show();
}