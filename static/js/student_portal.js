// Initialize animations on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeAnimations();
    initializeInteractiveElements();
});

function initializeAnimations() {
    // Stagger animation for content cards
    const cards = document.querySelectorAll('.content-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.animation = `fadeIn 0.6s ease-out ${index * 0.2}s forwards`;
    });
    
    // Add hover effects to course entries
    const courseEntries = document.querySelectorAll('.course-entry');
    courseEntries.forEach(entry => {
        entry.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(5px) scale(1.02)';
            this.style.boxShadow = '0 5px 15px rgba(78,205,196,0.3)';
        });
        
        entry.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0) scale(1)';
            this.style.boxShadow = 'none';
        });
    });
}

function initializeInteractiveElements() {
    // Add loading states to buttons
    const actionButtons = document.querySelectorAll('.btn');
    actionButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            if (!this.classList.contains('loading')) {
                this.classList.add('loading');
                const originalText = this.innerHTML;
                this.innerHTML = '<span class="spinner"></span> ' + this.textContent;
                
                setTimeout(() => {
                    this.classList.remove('loading');
                    this.innerHTML = originalText;
                }, 1000);
            }
        });
    });
}

function printSchedule() {
    // Add confirmation with smooth transition
    showNotification('Preparing to print schedule...', 'info');
    
    setTimeout(() => {
        window.print();
        showNotification('Print dialog opened successfully!', 'success');
    }, 500);
}

function exportSchedule() {
    showNotification('Export feature is coming soon!', 'info', true);
    
    // Simulate download preparation
    const btn = event.target;
    btn.style.transform = 'scale(0.95)';
    
    setTimeout(() => {
        btn.style.transform = 'scale(1)';
        // In future: implement actual PDF export
        showNotification('PDF export will be available in the next update!', 'warning');
    }, 300);
}

// Enhanced notification system
function showNotification(message, type = 'info', persistent = false) {
    // Remove existing notifications
    const existing = document.querySelectorAll('.toast-notification');
    existing.forEach(notification => notification.remove());
    
    const notification = document.createElement('div');
    notification.className = `toast-notification alert alert-${type === 'info' ? 'primary' : type} fade-in`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        border-radius: 15px;
        padding: 1rem 1.5rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.2);
        animation: slideIn 0.5s ease-out;
    `;
    
    const icons = {
        success: '✅',
        info: 'ℹ️',
        warning: '⚠️',
        danger: '❌'
    };
    
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 1.2rem;">${icons[type] || icons.info}</span>
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" style="
                background: none;
                border: none;
                color: inherit;
                font-size: 1.2rem;
                cursor: pointer;
                margin-left: auto;
                opacity: 0.7;
                transition: opacity 0.3s ease;
            " onmouseover="this.style.opacity='1'" onmouseout="this.style.opacity='0.7'">×</button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    if (!persistent) {
        setTimeout(() => {
            notification.style.animation = 'fadeOut 0.5s ease-out forwards';
            setTimeout(() => notification.remove(), 500);
        }, 3000);
    }
}

// Enhanced auto-refresh with visual feedback
let refreshInterval;
function startAutoRefresh() {
    const refreshIndicator = createRefreshIndicator();
    
    refreshInterval = setInterval(function() {
        refreshIndicator.style.animation = 'pulse 2s ease-in-out';
        console.log('Checking for schedule updates...');
        
        // Simulate API call
        setTimeout(() => {
            refreshIndicator.style.animation = '';
            // In a real application, this would check for updates
        }, 1000);
    }, 300000); // 5 minutes
}

function createRefreshIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'refresh-indicator';
    indicator.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: rgba(78,205,196,0.9);
        backdrop-filter: blur(10px);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 1.2rem;
        box-shadow: 0 5px 15px rgba(78,205,196,0.3);
        cursor: pointer;
        transition: all 0.3s ease;
        z-index: 1000;
    `;
    
    indicator.innerHTML = '🔄';
    indicator.title = 'Auto-refresh active';
    
    indicator.addEventListener('click', () => {
        showNotification('Manually checking for updates...', 'info');
        // Trigger manual refresh
    });
    
    indicator.addEventListener('mouseenter', () => {
        indicator.style.transform = 'scale(1.1)';
        indicator.style.boxShadow = '0 8px 25px rgba(78,205,196,0.4)';
    });
    
    indicator.addEventListener('mouseleave', () => {
        indicator.style.transform = 'scale(1)';
        indicator.style.boxShadow = '0 5px 15px rgba(78,205,196,0.3)';
    });
    
    document.body.appendChild(indicator);
    return indicator;
}

// Start auto-refresh when page loads
startAutoRefresh();

// Add smooth scrolling for navigation
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});
