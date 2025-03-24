// app/static/js/exam.js

document.addEventListener('DOMContentLoaded', function() {
    // Initialize exam functionality
    initExam();
    
    // Setup animations for exam page
    setupExamAnimations();
    
    // Setup AJAX for question submission
    setupAjaxSubmission();
});

/**
 * Initialize exam functionality
 */
function initExam() {
    const startExamBtn = document.getElementById('start-exam-btn');
    const examIntro = document.getElementById('exam-intro');
    const examContent = document.getElementById('exam-content');
    
    if (startExamBtn && examIntro && examContent) {
        startExamBtn.addEventListener('click', function() {
            // Animate the transition
            examIntro.classList.add('page-exit');
            
            setTimeout(() => {
                examIntro.style.display = 'none';
                examContent.style.display = 'block';
                examContent.classList.add('page-enter');
                
                setTimeout(() => {
                    examContent.classList.add('page-enter-active');
                }, 50);
            }, 400);
        });
    }
    
    // Setup radio options with event delegation
    setupRadioOptionsForNewQuestion();
}

/**
 * Setup radio option selection event handlers using event delegation
 * This works with dynamically loaded content
 */
function setupRadioOptionsForNewQuestion() {
    // Use event delegation for radio buttons
    document.addEventListener('change', function(event) {
        // Check if the changed element is a radio button
        if (event.target && event.target.type === 'radio' && event.target.name === 'response') {
            if (event.target.checked) {
                // Animate the selected option
                const label = event.target.parentElement;
                label.classList.add('pulse');
                
                setTimeout(() => {
                    label.classList.remove('pulse');
                }, 1000);
                
                // Enable the submit button
                const submitBtn = document.getElementById('submit-answer-btn');
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.classList.add('btn-hover-effect');
                }
            }
        }
    });
}

/**
 * Setup animations for exam page elements
 */
function setupExamAnimations() {
    // Animate progress bar
    updateProgressBar();
    
    // Animate question card entrance
    const questionCard = document.querySelector('.question-card') || document.querySelector('.puzzle-card');
    if (questionCard) {
        questionCard.classList.add('scale-in');
    }
    
    // Add staggered animation to radio options
    const radioOptions = document.querySelectorAll('.radio-option');
    radioOptions.forEach((option, index) => {
        option.classList.add('fade-in');
        option.style.animationDelay = `${0.1 + (index * 0.1)}s`;
    });
}

/**
 * Update the progress bar based on current question
 */
function updateProgressBar() {
    const progressBar = document.querySelector('.progress-bar');
    const currentQuestionIndex = parseInt(document.getElementById('current-question-index').value);
    const totalQuestions = parseInt(document.getElementById('total-questions').value);
    
    if (progressBar && !isNaN(currentQuestionIndex) && !isNaN(totalQuestions)) {
        const percentage = (currentQuestionIndex / totalQuestions) * 100;
        progressBar.style.width = `${percentage}%`;
        
        // Add animation to progress bar
        progressBar.classList.add('progress-bar-animated');
    }
}

/**
 * Setup AJAX submission for questions
 */
function setupAjaxSubmission() {
    // We need to use event delegation since the form elements will be replaced via AJAX
    document.addEventListener('click', function(event) {
        // Check if the clicked element is our submit button
        if (event.target && event.target.id === 'submit-answer-btn') {
            event.preventDefault();
            
            // Find the closest form to the button
            const form = event.target.closest('form');
            if (!form) {
                console.error('Form not found!');
                return;
            }
            
            // Get form data
            const questionId = form.querySelector('#question_id').value;
            const currentQuestionIndex = form.querySelector('#current_question_index').value;
            const selectedOption = form.querySelector('input[name="response"]:checked');
            
            if (!selectedOption) {
                alert('لطفاً یک گزینه را انتخاب کنید.');
                return;
            }
            
            const response = selectedOption.value;
            
            // Create form data for submission
            const formData = new FormData();
            formData.append('question_id', questionId);
            formData.append('current_question_index', currentQuestionIndex);
            formData.append('response', response);
            
            // Check if this is a puzzle question with attempts tracking
            const attemptsLeft = form.querySelector('#attempts-left');
            if (attemptsLeft) {
                formData.append('attempts_left', attemptsLeft.value);
            }
            
            // Show loading state
            const submitBtn = document.getElementById('submit-answer-btn');
            submitBtn.disabled = true;
            const originalBtnText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<div class="spinner" style="width: 20px; height: 20px; display: inline-block;"></div> در حال بارگذاری...';
            
            // Start the page turn animation
            const questionCard = document.querySelector('.question-card') || document.querySelector('.puzzle-card');
            if (questionCard) {
                questionCard.classList.add('page-turn-out');
            }
            
            // Send AJAX request
            fetch('/exam/submit_answer', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (response.redirected) {
                    // If redirected to thank you page, follow the redirect
                    window.location.href = response.url;
                    return { redirected: true };
                }
                
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                
                return response.json();
            })
            .then(data => {
                if (data.redirected) {
                    return;
                }

                if (data.redirect) {
                    // If there's a redirect URL, navigate to it
                    window.location.href = data.redirect;
                    return;
                }
                
                // Handle incorrect answer for puzzle questions
                if (data.is_correct === false) {
                    // Update attempts left indicator if present
                    if (attemptsLeft) {
                        attemptsLeft.value = data.attempts_left;
                        updateAttemptsIndicators(data.attempts_left);
                    }
                    
                    // Show feedback
                    const feedbackContainer = document.getElementById('feedback-container') || createFeedbackContainer();
                    feedbackContainer.innerHTML = `<div class="feedback-message feedback-error">${data.feedback}</div>`;
                    
                    // Reset button
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnText;
                    
                    // Remove transition class
                    if (questionCard) {
                        questionCard.classList.remove('page-turn-out');
                    }
                    
                    // Apply error shake animation
                    if (questionCard) {
                        questionCard.classList.add('puzzle-error');
                        setTimeout(() => {
                            questionCard.classList.remove('puzzle-error');
                        }, 500);
                    }
                    
                    return;
                }
                
                if (data && data.html) {
                    // Add new question card with animation
                    setTimeout(() => {
                        // Create a temporary container for the new content
                        const tempContainer = document.createElement('div');
                        tempContainer.innerHTML = data.html;
                        
                        // Extract the new question card
                        const newQuestionCard = tempContainer.querySelector('.question-card') || tempContainer.querySelector('.puzzle-card');
                        if (newQuestionCard) {
                            newQuestionCard.classList.add('page-turn-in');
                            
                            // Replace old card with new one
                            const questionContainer = document.getElementById('question-container');
                            if (questionContainer) {
                                questionContainer.innerHTML = '';
                                questionContainer.appendChild(newQuestionCard);
                                
                                // Update progress bar
                                if (data.progress) {
                                    document.querySelector('.progress-bar').style.width = data.progress + '%';
                                }
                                
                                // Update hidden fields
                                if (data.question_index) {
                                    const hiddenInput = document.getElementById('current-question-index');
                                    if (hiddenInput) {
                                        hiddenInput.value = data.question_index;
                                    }
                                }
                                
                                // If this is a puzzle question, initialize puzzle functionality
                                if (data.question_type === 'puzzle') {
                                    // Initialize puzzle type
                                    if (typeof initSpecificPuzzleType === 'function') {
                                        initSpecificPuzzleType();
                                    }
                                    
                                    // Setup attempts indicators if needed
                                    if (data.attempts_left) {
                                        const attemptsInput = document.getElementById('attempts-left');
                                        if (attemptsInput) {
                                            attemptsInput.value = data.attempts_left;
                                        }
                                        if (typeof setupAttemptsIndicators === 'function') {
                                            setupAttemptsIndicators();
                                        }
                                    }
                                }
                                
                                // Setup radio options for the new question
                                setupRadioOptionsForNewQuestion();
                                
                                // Remove animation classes after animation completes
                                setTimeout(() => {
                                    newQuestionCard.classList.remove('page-turn-in');
                                }, 1000);
                            } else {
                                console.error('Question container not found!');
                            }
                        } else {
                            console.error('New question card not found in response!');
                        }
                    }, 500);
                } else {
                    console.error('No HTML content in the response!', data);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('خطا در ارسال پاسخ. لطفاً دوباره تلاش کنید.');
                
                // Reset button
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
                
                // Remove animation classes
                if (questionCard) {
                    questionCard.classList.remove('page-turn-out');
                }
            });
        }
    });
}

/**
 * Create feedback container for puzzle questions if it doesn't exist
 */
function createFeedbackContainer() {
    const questionCard = document.querySelector('.puzzle-card');
    if (!questionCard) return null;
    
    const existingContainer = document.getElementById('feedback-container');
    if (existingContainer) return existingContainer;
    
    const feedbackContainer = document.createElement('div');
    feedbackContainer.id = 'feedback-container';
    feedbackContainer.className = 'feedback-container';
    
    // Insert after puzzle number
    const puzzleNumber = questionCard.querySelector('.puzzle-number');
    if (puzzleNumber) {
        puzzleNumber.after(feedbackContainer);
    } else {
        questionCard.insertBefore(feedbackContainer, questionCard.firstChild.nextSibling);
    }
    
    return feedbackContainer;
}

/**
 * Update attempts indicators for puzzle questions
 */
function updateAttemptsIndicators(attemptsLeft) {
    const indicators = document.querySelectorAll('.attempt-indicator');
    
    indicators.forEach((indicator, index) => {
        if (index >= attemptsLeft) {
            indicator.classList.add('attempt-used');
        } else {
            indicator.classList.remove('attempt-used');
        }
    });
}

/**
 * Handle the thank you page animations
 */
function initThankYouPage() {
    const checkmarkIcon = document.getElementById('checkmark-icon');
    if (checkmarkIcon) {
        checkmarkIcon.classList.add('checkmark');
    }
    
    const thankYouMessage = document.getElementById('thank-you-message');
    if (thankYouMessage) {
        thankYouMessage.classList.add('fade-in');
        thankYouMessage.style.animationDelay = '0.5s';
    }
    
    const followUpMessage = document.getElementById('follow-up-message');
    if (followUpMessage) {
        followUpMessage.classList.add('fade-in');
        followUpMessage.style.animationDelay = '1s';
    }
}

// Call thank you page animation if on thank you page
if (document.getElementById('thank-you-page')) {
    document.addEventListener('DOMContentLoaded', initThankYouPage);
}