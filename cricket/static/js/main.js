/**
 * Main JavaScript functionality for the BoundaryLine app
 */
document.addEventListener('DOMContentLoaded', function() {
    initLoader();
    initToasts();
    initPageTransitions();
    initFormValidation();
});

/**
 * Initialize the page loader
 */
function initLoader() {
    const loader = document.getElementById('pageLoader');
    
    // Show loader on page load
    if (loader) {
        loader.classList.add('show');
        
        // Hide loader when content is loaded
        window.addEventListener('load', () => {
            setTimeout(() => {
                loader.classList.remove('show');
            }, 300);
        });
        
        // Fallback: hide loader after 3 seconds if it's still showing
        setTimeout(() => {
            if (loader.classList.contains('show')) {
                loader.classList.remove('show');
            }
        }, 3000);
    }
}

/**
 * Initialize toast notifications
 */
function initToasts() {
    const toastElements = document.querySelectorAll('.toast');
    toastElements.forEach(toastEl => {
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
    });
}

/**
 * Initialize smooth page transitions
 */
function initPageTransitions() {
    const pageContent = document.querySelector('.page-content');
    
    // Show content when page is loaded
    if (pageContent) {
        window.addEventListener('load', () => {
            setTimeout(() => {
                pageContent.classList.add('loaded');
            }, 100);
        });
    }
    
    document.querySelectorAll('a:not([target="_blank"]):not([href^="#"])').forEach(link => {
        link.addEventListener('click', function(e) {
            // Skip for links that should open directly
            if (this.dataset.direct || this.classList.contains('direct-link')) {
                return;
            }
            
            const href = this.getAttribute('href');
            const isExternal = href.startsWith('http') || href.startsWith('//');
            
            if (!isExternal) {
                e.preventDefault();
                const pageContent = document.querySelector('.page-content');
                const loader = document.getElementById('pageLoader');
                
                // Fade out the content
                if (pageContent) {
                    pageContent.classList.remove('loaded');
                }
                
                // Show loader
                if (loader) {
                    loader.classList.add('show');
                }
                
                // Navigate after animation completes
                setTimeout(() => {
                    window.location.href = href;
                }, 300);
            }
        });
    });
}

/**
 * Initialize form validation styling
 */
function initFormValidation() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!this.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            this.classList.add('was-validated');
        });
    });
} 