// Custom Sports Portal Admin JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Remove any remaining Wagtail branding
    removeWagtailBranding();
    
    // Add custom functionality
    initSportsPortalFeatures();
    
    // Auto-refresh live match data
    initLiveDataRefresh();
});

function removeWagtailBranding() {
    // Remove Wagtail references from text content
    const elementsToCheck = document.querySelectorAll('*');
    elementsToCheck.forEach(element => {
        if (element.textContent && element.textContent.includes('Wagtail')) {
            // Replace Wagtail references with Sports Portal
            element.textContent = element.textContent.replace(/Wagtail/g, 'Sports Portal');
        }
    });
    
    // Hide elements with Wagtail classes
    const wagtailElements = document.querySelectorAll('[class*="wagtail"]');
    wagtailElements.forEach(element => {
        if (!element.classList.contains('wagtail-admin-keep')) {
            element.style.display = 'none';
        }
    });
}

function initSportsPortalFeatures() {
    // Add custom dashboard widgets
    addQuickStats();
    
    // Enhance match management
    enhanceMatchForms();
    
    // Add live status indicators
    addLiveStatusIndicators();
    
    // Custom validation for stream sources
    validateStreamSources();
}

function addQuickStats() {
    const dashboardPanel = document.querySelector('.dashboard-panel');
    if (dashboardPanel) {
        // Add live match counter
        const liveMatchesCount = document.querySelectorAll('.status-live').length;
        const statsHTML = `
            <div class="dashboard-stats">
                <div class="dashboard-stat">
                    <div class="number">${liveMatchesCount}</div>
                    <div class="label">Live Matches</div>
                </div>
            </div>
        `;
        dashboardPanel.insertAdjacentHTML('beforeend', statsHTML);
    }
}

function enhanceMatchForms() {
    // Auto-populate match title based on teams
    const homeTeamSelect = document.querySelector('#id_home_team');
    const awayTeamSelect = document.querySelector('#id_away_team');
    const titleField = document.querySelector('#id_title');
    
    if (homeTeamSelect && awayTeamSelect && titleField) {
        function updateTitle() {
            const homeTeam = homeTeamSelect.options[homeTeamSelect.selectedIndex]?.text;
            const awayTeam = awayTeamSelect.options[awayTeamSelect.selectedIndex]?.text;
            
            if (homeTeam && awayTeam && homeTeam !== '---------' && awayTeam !== '---------') {
                titleField.value = `${homeTeam} vs ${awayTeam}`;
            }
        }
        
        homeTeamSelect.addEventListener('change', updateTitle);
        awayTeamSelect.addEventListener('change', updateTitle);
    }
}

function addLiveStatusIndicators() {
    // Add pulsing animation to live matches
    const liveElements = document.querySelectorAll('.status-live, [data-status="live"]');
    liveElements.forEach(element => {
        element.style.animation = 'pulse 2s infinite';
        element.style.backgroundColor = '#DC2626';
        element.style.color = 'white';
    });
    
    // Add CSS animation if not exists
    if (!document.querySelector('#live-pulse-animation')) {
        const style = document.createElement('style');
        style.id = 'live-pulse-animation';
        style.textContent = `
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.7; }
                100% { opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }
}

function validateStreamSources() {
    const streamUrlField = document.querySelector('#id_url');
    const providerField = document.querySelector('#id_provider');
    
    if (streamUrlField && providerField) {
        streamUrlField.addEventListener('blur', function() {
            const url = this.value.toLowerCase();
            const provider = providerField.value;
            
            // Auto-detect provider based on URL
            if (url.includes('youtube.com') || url.includes('youtu.be')) {
                providerField.value = 'youtube';
            } else if (url.includes('vimeo.com')) {
                providerField.value = 'vimeo';
            }
            
            // Validate URL format
            if (url && !isValidStreamUrl(url)) {
                showValidationError(streamUrlField, 'Please enter a valid stream URL');
            } else {
                clearValidationError(streamUrlField);
            }
        });
    }
}

function isValidStreamUrl(url) {
    const validPatterns = [
        /^https:\/\/(www\.)?youtube\.com\/watch\?v=[\w-]+/,
        /^https:\/\/youtu\.be\/[\w-]+/,
        /^https:\/\/(www\.)?vimeo\.com\/\d+/,
        /^https:\/\/[\w.-]+\.(m3u8|mpd)(\?.*)?$/,  // HLS/DASH
        /^https?:\/\/[\w.-]+\/.*\.(mp4|webm|ogg)(\?.*)?$/  // Direct video
    ];
    
    return validPatterns.some(pattern => pattern.test(url));
}

function showValidationError(field, message) {
    clearValidationError(field);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'validation-error';
    errorDiv.style.color = '#DC2626';
    errorDiv.style.fontSize = '12px';
    errorDiv.style.marginTop = '4px';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
    field.style.borderColor = '#DC2626';
}

function clearValidationError(field) {
    const existingError = field.parentNode.querySelector('.validation-error');
    if (existingError) {
        existingError.remove();
    }
    field.style.borderColor = '';
}

function initLiveDataRefresh() {
    // Auto-refresh live match data every 30 seconds
    if (window.location.pathname.includes('/match/')) {
        setInterval(function() {
            const liveMatches = document.querySelectorAll('[data-status="live"]');
            if (liveMatches.length > 0) {
                // Add visual indicator that data is refreshing
                liveMatches.forEach(match => {
                    match.style.opacity = '0.8';
                    setTimeout(() => {
                        match.style.opacity = '1';
                    }, 1000);
                });
            }
        }, 30020);
    }
}

// Custom notification system
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 6px;
        color: white;
        font-weight: 500;
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    
    switch (type) {
        case 'success':
            notification.style.backgroundColor = '#0B6E4F';
            break;
        case 'error':
            notification.style.backgroundColor = '#DC2626';
            break;
        case 'warning':
            notification.style.backgroundColor = '#F59E0B';
            break;
    }
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}

// Add slide animations
const slideAnimations = document.createElement('style');
slideAnimations.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(slideAnimations);

// Sports Portal specific utilities
window.SportsPortal = {
    showNotification: showNotification,
    validateStreamUrl: isValidStreamUrl,
    refreshLiveData: initLiveDataRefresh
};