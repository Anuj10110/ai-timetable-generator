function toggleRoleFields() {
    const role = document.getElementById('roleSelect').value;
    const roleFields = document.querySelectorAll('.role-specific');
    
    // Hide all role-specific fields
    roleFields.forEach(field => {
        field.style.display = 'none';
    });
    
    // Show relevant fields based on selected role
    if (role === 'student') {
        document.getElementById('studentFields').style.display = 'block';
    } else if (role === 'faculty') {
        document.getElementById('facultyFields').style.display = 'block';
    }
}

// Form validation
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('registerForm').addEventListener('submit', function(e) {
        const password = document.querySelector('input[name="password"]').value;
        const confirmPassword = document.querySelector('input[name="confirm_password"]').value;
        
        if (password !== confirmPassword) {
            e.preventDefault();
            alert('Passwords do not match!');
            return false;
        }
        
        if (password.length < 6) {
            e.preventDefault();
            alert('Password must be at least 6 characters long!');
            return false;
        }
    });
});