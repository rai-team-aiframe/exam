// app/static/js/puzzle.js - Improved version

document.addEventListener('DOMContentLoaded', function() {
    // Initialize puzzle functionality
    initPuzzles();
    
    // Setup animations for puzzle page
    setupPuzzleAnimations();
});

/**
 * Initialize puzzle functionality
 */
function initPuzzles() {
    // Initialize specific puzzle types based on current puzzle
    initPuzzleVisualizations();
    
    // Setup attempts indicators
    setupAttemptsIndicators();
}

/**
 * Initialize puzzle visualizations based on puzzle type
 */
function initPuzzleVisualizations() {
    const puzzleCard = document.querySelector('.puzzle-card');
    if (!puzzleCard) return;
    
    const puzzleVisual = document.getElementById('puzzle-visual');
    if (!puzzleVisual) return;
    
    // Get puzzle type
    const puzzleType = puzzleCard.dataset.puzzleType;
    
    // If no puzzle type, use a fallback SVG visualization
    if (!puzzleType || puzzleType === 'undefined') {
        createFallbackVisualization(puzzleVisual);
        return;
    }
    
    // Try to parse puzzle data
    let puzzleData;
    try {
        puzzleData = JSON.parse(puzzleCard.dataset.puzzleData || '{}');
    } catch (error) {
        console.error('Error parsing puzzle data:', error);
        createFallbackVisualization(puzzleVisual);
        return;
    }
    
    // Create visualization based on puzzle type
    switch (puzzleType) {
        case 'path_finding':
            createPathFindingVisualization(puzzleVisual, puzzleData);
            break;
        case 'pattern_match':
            createPatternMatchVisualization(puzzleVisual, puzzleData);
            break;
        case 'color_pattern':
            createColorPatternVisualization(puzzleVisual, puzzleData);
            break;
        case 'number_sequence':
            createNumberSequenceVisualization(puzzleVisual, puzzleData);
            break;
        case 'maze':
            createMazeVisualization(puzzleVisual, puzzleData);
            break;
        case 'chess_move':
            createChessMoveVisualization(puzzleVisual, puzzleData);
            break;
        default:
            createFallbackVisualization(puzzleVisual);
    }
}

/**
 * Create a fallback visualization when puzzle type is unknown or data is missing
 */
function createFallbackVisualization(container) {
    container.innerHTML = `
        <div style="text-align: center; padding: 20px;">
            <img src="/static/img/path-finding.svg" alt="پازل" style="max-width: 100%; height: auto;">
            <p style="margin-top: 15px;">لطفاً گزینه مناسب را انتخاب کنید.</p>
        </div>
    `;
}

/**
 * Create path finding visualization
 */
function createPathFindingVisualization(container, puzzleData) {
    container.innerHTML = `
        <div style="text-align: center; padding: 20px;">
            <img src="/static/img/path-finding.svg" alt="پازل مسیریابی" style="max-width: 100%; height: auto;">
            <p style="margin-top: 15px;">مسیری را انتخاب کنید که انسان را به خانه برساند.</p>
        </div>
    `;
}

/**
 * Create pattern match visualization
 */
function createPatternMatchVisualization(container, puzzleData) {
    container.innerHTML = `
        <div style="text-align: center; padding: 20px;">
            <img src="/static/img/pattern-match.svg" alt="پازل الگو" style="max-width: 100%; height: auto;">
            <p style="margin-top: 15px;">الگو را بررسی کرده و قطعه مناسب را انتخاب کنید.</p>
        </div>
    `;
}

/**
 * Create color pattern visualization
 */
function createColorPatternVisualization(container, puzzleData) {
    container.innerHTML = `
        <div style="text-align: center; padding: 20px;">
            <img src="/static/img/color-pattern.svg" alt="پازل الگوی رنگی" style="max-width: 100%; height: auto;">
            <p style="margin-top: 15px;">الگوی رنگی را بررسی کرده و رنگ مناسب را انتخاب کنید.</p>
        </div>
    `;
}

/**
 * Create number sequence visualization
 */
function createNumberSequenceVisualization(container, puzzleData) {
    container.innerHTML = `
        <div style="text-align: center; padding: 20px;">
            <img src="/static/img/number-sequence.svg" alt="پازل دنباله اعداد" style="max-width: 100%; height: auto;">
            <p style="margin-top: 15px;">الگوی عددی را بررسی کرده و عدد بعدی را انتخاب کنید.</p>
        </div>
    `;
}

/**
 * Create chess move visualization
 */
function createChessMoveVisualization(container, puzzleData) {
    container.innerHTML = `
        <div style="text-align: center; padding: 20px;">
            <img src="/static/img/chess-move.svg" alt="پازل شطرنج" style="max-width: 100%; height: auto;">
            <p style="margin-top: 15px;">کدام حرکت را باید انجام دهید؟</p>
        </div>
    `;
}

/**
 * Create maze visualization
 */
function createMazeVisualization(container, puzzleData) {
    container.innerHTML = `
        <div style="text-align: center; padding: 20px;">
            <img src="/static/img/maze.svg" alt="پازل هزارتو" style="max-width: 100%; height: auto;">
            <p style="margin-top: 15px;">مسیری را انتخاب کنید که از هزارتو خارج شوید.</p>
        </div>
    `;
}

/**
 * Setup attempts indicators
 */
function setupAttemptsIndicators() {
    const puzzleCard = document.querySelector('.puzzle-card');
    if (!puzzleCard) return;
    
    const attemptsLeft = document.getElementById('attempts-left');
    if (!attemptsLeft) return;
    
    const attemptCount = parseInt(attemptsLeft.value || 2);
    
    // Create attempts indicators if they don't exist
    let attemptsContainer = document.getElementById('attempts-indicators');
    
    if (!attemptsContainer) {
        attemptsContainer = document.createElement('div');
        attemptsContainer.id = 'attempts-indicators';
        attemptsContainer.className = 'attempts-container';
        attemptsContainer.style.cssText = 'display: flex; justify-content: center; gap: 10px; margin: 15px 0;';
        
        for (let i = 0; i < 2; i++) {
            const indicator = document.createElement('div');
            indicator.className = 'attempt-indicator';
            indicator.style.cssText = 'width: 20px; height: 20px; border-radius: 50%; background-color: #3498db;';
            
            // Mark as used if needed
            if (i >= attemptCount) {
                indicator.style.backgroundColor = '#e74c3c';
            }
            
            attemptsContainer.appendChild(indicator);
        }
        
        // Add to page
        const puzzleNumber = puzzleCard.querySelector('.puzzle-number');
        if (puzzleNumber) {
            puzzleNumber.after(attemptsContainer);
        } else {
            puzzleCard.insertBefore(attemptsContainer, puzzleCard.firstChild);
        }
    }
}

/**
 * Update attempts indicators
 */
function updateAttemptsIndicators(attemptsLeft) {
    const indicators = document.querySelectorAll('.attempt-indicator');
    
    indicators.forEach((indicator, index) => {
        if (index >= attemptsLeft) {
            indicator.style.backgroundColor = '#e74c3c';
        } else {
            indicator.style.backgroundColor = '#3498db';
        }
    });
}

/**
 * Setup animations for puzzle elements
 */
function setupPuzzleAnimations() {
    // Add scale-in animation to puzzle visualizations
    const puzzleVisual = document.getElementById('puzzle-visual');
    if (puzzleVisual) {
        puzzleVisual.classList.add('scale-in');
    }
    
    // Add fade-in animation to options
    const radioOptions = document.querySelectorAll('.radio-option');
    radioOptions.forEach((option, index) => {
        option.classList.add('fade-in');
        option.style.animationDelay = `${0.1 + (index * 0.1)}s`;
    });
}