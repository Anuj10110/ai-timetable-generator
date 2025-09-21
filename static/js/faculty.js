let slotCounter = 1;

function addTimeSlot() {
    const container = document.getElementById('timeSlotsContainer');
    const newSlot = document.createElement('div');
    newSlot.className = 'time-slot-input';
    newSlot.innerHTML = `
        <div class="row">
            <div class="col-4">
                <select class="form-select form-select-sm" name="day_${slotCounter}">
                    <option value="">Day</option>
                    <option value="Monday">Monday</option>
                    <option value="Tuesday">Tuesday</option>
                    <option value="Wednesday">Wednesday</option>
                    <option value="Thursday">Thursday</option>
                    <option value="Friday">Friday</option>
                </select>
            </div>
            <div class="col-4">
                <input type="time" class="form-control form-control-sm" 
                       name="start_time_${slotCounter}" placeholder="Start">
            </div>
            <div class="col-3">
                <input type="time" class="form-control form-control-sm" 
                       name="end_time_${slotCounter}" placeholder="End">
            </div>
            <div class="col-1">
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeTimeSlot(this)">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `;
    container.appendChild(newSlot);
    slotCounter++;
}

function removeTimeSlot(button) {
    button.closest('.time-slot-input').remove();
}