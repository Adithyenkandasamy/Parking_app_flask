// Form validation functions

// Validate registration form
function validateRegistrationForm() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm_password').value;
    const fullName = document.getElementById('full_name').value.trim();
    const address = document.getElementById('address').value.trim();
    const pincode = document.getElementById('pincode').value.trim();

    // Clear previous error messages
    clearFormErrors();

    // Validate username
    if (!username) {
        showError('username', 'Username is required');
    } else if (username.length < 3) {
        showError('username', 'Username must be at least 3 characters');
    }

    // Validate password
    if (!password) {
        showError('password', 'Password is required');
    } else if (password.length < 6) {
        showError('password', 'Password must be at least 6 characters');
    }

    // Validate confirm password
    if (password !== confirmPassword) {
        showError('confirm_password', 'Passwords do not match');
    }

    // Validate full name
    if (!fullName) {
        showError('full_name', 'Full name is required');
    }

    // Validate address
    if (!address) {
        showError('address', 'Address is required');
    }

    // Validate pincode
    if (!pincode) {
        showError('pincode', 'Pincode is required');
    } else if (!/^[1-9][0-9]{5}$/.test(pincode)) {
        showError('pincode', 'Invalid pincode format');
    }

    // If there are any errors, prevent form submission
    const errorElements = document.querySelectorAll('.form-error');
    return errorElements.length === 0;
}

// Validate login form
function validateLoginForm() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;

    // Clear previous error messages
    clearFormErrors();

    if (!username) {
        showError('username', 'Username is required');
    }

    if (!password) {
        showError('password', 'Password is required');
    }

    const errorElements = document.querySelectorAll('.form-error');
    return errorElements.length === 0;
}

// Validate add parking lot form
function validateAddLotForm() {
    const name = document.getElementById('name').value.trim();
    const address = document.getElementById('address').value.trim();
    const pincode = document.getElementById('pincode').value.trim();
    const pricePerHour = document.getElementById('price_per_hour').value;
    const maxSpots = document.getElementById('max_spots').value;

    clearFormErrors();

    if (!name) {
        showError('name', 'Lot name is required');
    }

    if (!address) {
        showError('address', 'Address is required');
    }

    if (!pincode) {
        showError('pincode', 'Pincode is required');
    } else if (!/^[1-9][0-9]{5}$/.test(pincode)) {
        showError('pincode', 'Invalid pincode format');
    }

    if (!pricePerHour) {
        showError('price_per_hour', 'Price per hour is required');
    } else if (pricePerHour <= 0) {
        showError('price_per_hour', 'Price per hour must be greater than 0');
    }

    if (!maxSpots) {
        showError('max_spots', 'Maximum spots is required');
    } else if (maxSpots <= 0) {
        showError('max_spots', 'Maximum spots must be greater than 0');
    }

    const errorElements = document.querySelectorAll('.form-error');
    return errorElements.length === 0;
}

// Helper functions
function showError(fieldId, message) {
    const field = document.getElementById(fieldId);
    if (field) {
        field.classList.add('is-invalid');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback form-error';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }
}

function clearFormErrors() {
    const invalidFields = document.querySelectorAll('.is-invalid');
    invalidFields.forEach(field => {
        field.classList.remove('is-invalid');
    });
    const errorDivs = document.querySelectorAll('.form-error');
    errorDivs.forEach(div => {
        div.remove();
    });
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Register form
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            if (!validateRegistrationForm()) {
                e.preventDefault();
            }
        });
    }

    // Login form
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            if (!validateLoginForm()) {
                e.preventDefault();
            }
        });
    }

    // Add lot form
    const addLotForm = document.getElementById('add-lot-form');
    if (addLotForm) {
        addLotForm.addEventListener('submit', function(e) {
            if (!validateAddLotForm()) {
                e.preventDefault();
            }
        });
    }
});
