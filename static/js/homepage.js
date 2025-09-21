// Homepage JavaScript for interactions and animations

document.addEventListener('DOMContentLoaded', function() {
    // Ensure section headers are immediately visible
    ensureSectionHeadersVisible();
    
    initializeScrollEffects();
    initializeAnimations();
    initializeInteractiveElements();
    initializeSectionNavigation();
});

// Ensure section headers are always visible
function ensureSectionHeadersVisible() {
    document.querySelectorAll('.section-header, .section-badge, .section-title, .section-description').forEach(el => {
        el.style.opacity = '1';
        el.style.visibility = 'visible';
        el.style.transform = 'translateY(0)';
    });
}

// Initialize scroll-based effects
function initializeScrollEffects() {
    const navbar = document.querySelector('.navbar');
    
    // Navbar scroll effect
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const offsetTop = target.offsetTop - 80;
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Intersection Observer for animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                
                // Special animations for specific elements
                if (entry.target.classList.contains('feature-card')) {
                    setTimeout(() => {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }, Math.random() * 300);
                }
                
                if (entry.target.classList.contains('step-card')) {
                    setTimeout(() => {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }, Math.random() * 200);
                }
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    document.querySelectorAll('.feature-card, .step-card, .benefit-item, .hero-stats').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'all 0.6s ease';
        observer.observe(el);
    });
    
    // Observe section headers separately with immediate visibility
    document.querySelectorAll('.section-header').forEach(el => {
        el.style.opacity = '1';
        el.style.transform = 'translateY(0)';
        el.style.transition = 'all 0.6s ease';
        observer.observe(el);
    });
}

// Initialize page animations
function initializeAnimations() {
    // Animate hero stats on load
    setTimeout(() => {
        animateCounters();
    }, 1000);
    
    // Animate timetable demo cells
    animateDemoCells();
    
    // Progress bar animations
    setTimeout(() => {
        animateProgressBars();
    }, 2000);
}

// Animate counter numbers
function animateCounters() {
    const counters = document.querySelectorAll('.stat-number');
    
    counters.forEach(counter => {
        const target = parseInt(counter.textContent.replace(/\D/g, ''));
        const suffix = counter.textContent.replace(/\d/g, '');
        const increment = target / 50;
        let current = 0;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                counter.textContent = target + suffix;
                clearInterval(timer);
            } else {
                counter.textContent = Math.floor(current) + suffix;
            }
        }, 30);
    });
}

// Animate demo timetable cells
function animateDemoCells() {
    const cells = document.querySelectorAll('.demo-cell');
    
    setInterval(() => {
        // Remove all active classes
        cells.forEach(cell => cell.classList.remove('active'));
        
        // Add active class to random cells
        const numActive = Math.floor(Math.random() * 3) + 2;
        const shuffled = Array.from(cells).sort(() => 0.5 - Math.random());
        
        for (let i = 0; i < numActive; i++) {
            setTimeout(() => {
                shuffled[i].classList.add('active');
            }, i * 200);
        }
    }, 4000);
}

// Animate progress bars
function animateProgressBars() {
    const progressFills = document.querySelectorAll('.progress-fill');
    
    progressFills.forEach(fill => {
        const targetWidth = fill.style.width;
        fill.style.width = '0%';
        
        setTimeout(() => {
            fill.style.width = targetWidth;
        }, Math.random() * 500);
    });
}

// Initialize interactive elements
function initializeInteractiveElements() {
    // Add hover effects to cards
    const cards = document.querySelectorAll('.feature-card, .step-card');
    
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // Floating cards interaction
    const floatingCards = document.querySelectorAll('.floating-card');
    
    floatingCards.forEach((card, index) => {
        card.addEventListener('mouseenter', function() {
            this.style.animationPlayState = 'paused';
            this.style.transform = 'translateY(-5px) scale(1.05)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.animationPlayState = 'running';
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // Button interactions
    const buttons = document.querySelectorAll('.btn-hero-primary, .btn-hero-secondary, .btn-cta-primary, .btn-cta-secondary');
    
    buttons.forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px)';
        });
        
        btn.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
        
        btn.addEventListener('click', function() {
            // Add ripple effect
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = (event.clientX - rect.left - size / 2) + 'px';
            ripple.style.top = (event.clientY - rect.top - size / 2) + 'px';
            ripple.style.position = 'absolute';
            ripple.style.borderRadius = '50%';
            ripple.style.background = 'rgba(255, 255, 255, 0.3)';
            ripple.style.transform = 'scale(0)';
            ripple.style.animation = 'ripple 0.6s ease-out';
            ripple.style.pointerEvents = 'none';
            
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
    
    // Add ripple animation CSS
    const style = document.createElement('style');
    style.textContent = `
        @keyframes ripple {
            to {
                transform: scale(2);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

// Parallax effect for hero section
window.addEventListener('scroll', function() {
    const scrolled = window.pageYOffset;
    const hero = document.querySelector('.hero-section');
    const particles = document.querySelector('.hero-particles');
    
    if (hero && particles) {
        particles.style.transform = `translateY(${scrolled * 0.5}px)`;
    }
});

// Add loading animation
window.addEventListener('load', function() {
    document.body.classList.add('loaded');
    
    // Animate elements in sequence
    setTimeout(() => {
        document.querySelector('.hero-title').style.animation = 'slideIn 0.8s ease-out forwards';
    }, 300);
    
    setTimeout(() => {
        document.querySelector('.hero-description').style.animation = 'fadeIn 0.8s ease-out forwards';
    }, 600);
    
    setTimeout(() => {
        document.querySelector('.hero-actions').style.animation = 'slideIn 0.8s ease-out forwards';
    }, 900);
});

// Mobile menu interactions
const navbarToggler = document.querySelector('.navbar-toggler');
const navbarCollapse = document.querySelector('.navbar-collapse');

if (navbarToggler && navbarCollapse) {
    navbarToggler.addEventListener('click', function() {
        // Add custom mobile menu animations
        if (navbarCollapse.classList.contains('show')) {
            navbarCollapse.style.animation = 'slideUp 0.3s ease-out forwards';
        } else {
            navbarCollapse.style.animation = 'slideDown 0.3s ease-out forwards';
        }
    });
}

// Performance optimization - debounce scroll events
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Apply debouncing to scroll events
const debouncedScroll = debounce(() => {
    // Scroll-based animations here
}, 10);

// Section navigation functionality
function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        const offsetTop = section.offsetTop - 80;
        window.scrollTo({
            top: offsetTop,
            behavior: 'smooth'
        });
    }
}

// Initialize section navigation
function initializeSectionNavigation() {
    const sections = ['home', 'features', 'how-it-works', 'benefits'];
    const dots = document.querySelectorAll('.section-dot');
    
    // Update active dot on scroll
    window.addEventListener('scroll', debounce(() => {
        const scrollPosition = window.scrollY + 150;
        
        sections.forEach((sectionId, index) => {
            const section = document.getElementById(sectionId);
            if (section) {
                const sectionTop = section.offsetTop;
                const sectionHeight = section.offsetHeight;
                
                if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                    dots.forEach(dot => dot.classList.remove('active'));
                    if (dots[index]) {
                        dots[index].classList.add('active');
                    }
                }
            }
        });
    }, 50));
}

// Make scrollToSection available globally
window.scrollToSection = scrollToSection;
