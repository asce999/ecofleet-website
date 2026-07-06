/**
 * EcoFleet Generic Dashboard Interactions
 * 
 * Handles generic UI behaviors across any dashboard:
 * - Counter animations (count-up)
 * - Intersection observers for lazy loading or animation triggers
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Counter Animations
    const animatedCounters = document.querySelectorAll('.df-count-up');
    
    if ('IntersectionObserver' in window) {
        const counterObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateValue(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        animatedCounters.forEach(counter => counterObserver.observe(counter));
    } else {
        // Fallback
        animatedCounters.forEach(counter => animateValue(counter));
    }

    function animateValue(obj) {
        const text = obj.innerText.trim();
        // Remove commas before parsing to handle thousands separators
        const cleanText = text.replace(/,/g, '');
        // Extract numeric part (ignores ₹, %, ms etc but assumes suffix)
        const match = cleanText.match(/^([^\d]*)(\d+(?:\.\d+)?)(.*)$/);
        
        if (!match) return; // not a standard number format
        
        const prefix = match[1];
        const endStr = match[2];
        const suffix = match[3];
        const end = parseFloat(endStr);
        
        // Don't animate very small numbers unnecessarily
        if (isNaN(end) || end < 2) return;
        
        const duration = 1500;
        let startTimestamp = null;
        
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            
            // easeOutQuart
            const easeProgress = 1 - Math.pow(1 - progress, 4);
            const current = progress === 1 ? end : (end * easeProgress);
            
            // Preserve decimal places if original had them
            const hasDecimals = endStr.includes('.');
            let formatted = hasDecimals ? current.toFixed(2) : Math.floor(current).toString();
            
            // Add thousands separators back
            const parts = formatted.split('.');
            parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
            formatted = parts.join('.');
            
            obj.innerText = `${prefix}${formatted}${suffix}`;
            
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        
        window.requestAnimationFrame(step);
    }
});
