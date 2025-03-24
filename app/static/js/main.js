// app/static/js/main.js

document.addEventListener('DOMContentLoaded', function() {
    // Add animation classes to elements
    animateOnScroll();
    
    // Form validation
    setupFormValidation();
    
    // Mobile menu toggle
    setupMobileMenu();
});

/**
 * Add animations to elements when they come into view
 */
function animateOnScroll() {
    const elements = document.querySelectorAll('.animate-on-scroll');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                const animation = el.dataset.animation || 'fade-in';
                el.classList.add(animation);
                observer.unobserve(el);
            }
        });
    }, { threshold: 0.1 });
    
    elements.forEach(element => {
        observer.observe(element);
    });
}

/**
 * Setup form validation for signup and login forms
 */
function setupFormValidation() {
    const signupForm = document.getElementById('signup-form');
    const loginForm = document.getElementById('login-form');
    
    if (signupForm) {
        signupForm.addEventListener('submit', function(e) {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const idNumber = document.getElementById('id_number').value;
            const phoneNumber = document.getElementById('phone_number').value;
            
            let isValid = true;
            let errorMessages = [];
            
            // Username validation
            if (username.length < 3 || username.length > 10) {
                errorMessages.push('نام کاربری باید بین 3 تا 10 کاراکتر باشد.');
                isValid = false;
            }
            
            if (!/^[a-zA-Z0-9_]+$/.test(username)) {
                errorMessages.push('نام کاربری فقط می‌تواند شامل حروف انگلیسی، اعداد و _ باشد.');
                isValid = false;
            }
            
            if (/^\d+$/.test(username)) {
                errorMessages.push('نام کاربری نمی‌تواند فقط شامل اعداد باشد.');
                isValid = false;
            }
            
            // Password validation
            if (password.length < 5 || password.length > 30) {
                errorMessages.push('رمز عبور باید بین 5 تا 30 کاراکتر باشد.');
                isValid = false;
            }
            
            if (!/[a-zA-Z]/.test(password) || !/\d/.test(password) || !/[^a-zA-Z0-9]/.test(password)) {
                errorMessages.push('رمز عبور باید شامل حروف، اعداد و حداقل یک کاراکتر خاص باشد.');
                isValid = false;
            }
            
            // ID number validation
            if (!/^\d{10}$/.test(idNumber)) {
                errorMessages.push('کد ملی باید دقیقاً 10 رقم باشد.');
                isValid = false;
            }
            
            // Phone number validation
            if (!/^09\d{9}$/.test(phoneNumber)) {
                errorMessages.push('شماره تلفن باید با 09 شروع شود و دقیقاً 11 رقم باشد.');
                isValid = false;
            }
            
            if (!isValid) {
                e.preventDefault();
                
                const errorContainer = document.getElementById('error-container');
                if (errorContainer) {
                    errorContainer.innerHTML = errorMessages.map(msg => `<div class="alert alert-danger">${msg}</div>`).join('');
                    
                    // Animate the error container
                    errorContainer.classList.add('shake');
                    setTimeout(() => {
                        errorContainer.classList.remove('shake');
                    }, 1000);
                    
                    // Scroll to errors
                    errorContainer.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    }
    
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            let isValid = true;
            let errorMessages = [];
            
            if (!username) {
                errorMessages.push('لطفاً نام کاربری را وارد کنید.');
                isValid = false;
            }
            
            if (!password) {
                errorMessages.push('لطفاً رمز عبور را وارد کنید.');
                isValid = false;
            }
            
            if (!isValid) {
                e.preventDefault();
                
                const errorContainer = document.getElementById('error-container');
                if (errorContainer) {
                    errorContainer.innerHTML = errorMessages.map(msg => `<div class="alert alert-danger">${msg}</div>`).join('');
                    
                    // Animate the error container
                    errorContainer.classList.add('shake');
                    setTimeout(() => {
                        errorContainer.classList.remove('shake');
                    }, 1000);
                }
            }
        });
    }
}

/**
 * Setup mobile menu toggle
 */
function setupMobileMenu() {
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (mobileMenuToggle && navLinks) {
        mobileMenuToggle.addEventListener('click', function() {
            navLinks.classList.toggle('show');
            
            if (navLinks.classList.contains('show')) {
                navLinks.style.maxHeight = navLinks.scrollHeight + 'px';
            } else {
                navLinks.style.maxHeight = '0';
            }
        });
    }
}

/**
 * Add input highlight animation to form fields on focus
 */
document.addEventListener('focusin', function(e) {
    if (e.target.classList.contains('form-control')) {
        e.target.classList.add('input-highlight');
    }
});

document.addEventListener('focusout', function(e) {
    if (e.target.classList.contains('form-control')) {
        e.target.classList.remove('input-highlight');
    }
});

/**
 * Format date input for Shamsi calendar
 */
function setupShamsiDatePicker() {
    const dateInput = document.getElementById('birth_date');
    if (dateInput) {
        // This is a simplified implementation
        // In a real project, you'd use a proper Shamsi date picker library
        dateInput.addEventListener('keyup', function(e) {
            let value = e.target.value.replace(/[^0-9/]/g, '');
            
            // Format as 1400/01/01
            if (value.length > 4 && value.charAt(4) !== '/') {
                value = value.slice(0, 4) + '/' + value.slice(4);
            }
            if (value.length > 7 && value.charAt(7) !== '/') {
                value = value.slice(0, 7) + '/' + value.slice(7);
            }
            
            // Limit to 10 characters (YYYY/MM/DD)
            if (value.length > 10) {
                value = value.slice(0, 10);
            }
            
            e.target.value = value;
        });
    }
}

// Call the function when the DOM is loaded
document.addEventListener('DOMContentLoaded', setupShamsiDatePicker);