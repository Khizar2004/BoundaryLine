/**
 * Dark mode functionality for the BoundaryLine app
 */
document.addEventListener('DOMContentLoaded', function() {
    initDarkMode();
});

/**
 * Initialize dark mode toggle functionality
 */
function initDarkMode() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (!darkModeToggle) return; // Exit if toggle doesn't exist
    
    const modeIcon = darkModeToggle.querySelector('.mode-icon');
    const modeText = darkModeToggle.querySelector('.mode-text');
    
    function setTheme(theme) {
        // Set the theme attribute for Bootstrap 5
        document.documentElement.setAttribute('data-bs-theme', theme);
        
        // Set body background and text colors directly for immediate feedback
        document.body.style.backgroundColor = theme === 'dark' ? '#121212' : '#f8f9fa';
        document.body.style.color = theme === 'dark' ? '#f8f9fa' : '#212529';
        
        // Store theme preference in localStorage
        localStorage.setItem('theme', theme);
        
        // Set a cookie for server-side rendering
        document.cookie = `theme=${theme}; path=/; max-age=31536000`; // 1 year expiration
        
        // Update the toggle appearance
        if (theme === 'dark') {
            modeIcon.classList.remove('fa-moon');
            modeIcon.classList.add('fa-sun');
            modeText.textContent = 'Light Mode';
        } else {
            modeIcon.classList.remove('fa-sun');
            modeIcon.classList.add('fa-moon');
            modeText.textContent = 'Dark Mode';
        }
    }
    
    // Check for current theme on page
    const currentTheme = document.documentElement.getAttribute('data-bs-theme') || 'light';
    
    // Initialize the correct icon based on current theme
    if (currentTheme === 'dark') {
        modeIcon.classList.remove('fa-moon');
        modeIcon.classList.add('fa-sun');
        modeText.textContent = 'Light Mode';
    } else {
        modeIcon.classList.remove('fa-sun');
        modeIcon.classList.add('fa-moon');
        modeText.textContent = 'Dark Mode';
    }
    
    // Check for saved theme preference or prefers-color-scheme
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme) {
        setTheme(savedTheme);
    } else if (prefersDark) {
        setTheme('dark');
    } else {
        setTheme('light');
    }

    // Toggle theme when button is clicked
    darkModeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
    });
} 