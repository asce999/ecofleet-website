// EcoFleet Express - Scroll Reveal & Count-Up Animations
document.addEventListener('DOMContentLoaded', function () {
  // 1. Initial Page Load Animation for Hero Section
  const heroElements = document.querySelectorAll('.hero > *');
  heroElements.forEach((el, index) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1), transform 0.8s cubic-bezier(0.16, 1, 0.3, 1)';
    // Stagger hero elements slightly
    setTimeout(() => {
      el.style.opacity = '1';
      el.style.transform = 'translateY(0)';
    }, 100 + index * 100);
  });

  // 2. Setup Reveal Elements
  const revealSelectors = [
    '.track-section',
    '.section-header',
    '.cards-grid',
    '.why-grid',
    '.cta-band',
    '.about-section',
    '.about-values',
    '.apart-grid',
    '.service-block',
    '.process-flow',
    '.contact-section',
    '.location-section'
  ];

  // Helper to add reveal classes and handle animation
  const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.15
  };

  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed');
        
        // If it's a staggered container, animate children
        if (entry.target.classList.contains('cards-grid') || 
            entry.target.classList.contains('why-grid') ||
            entry.target.classList.contains('about-values') ||
            entry.target.classList.contains('apart-grid') ||
            entry.target.classList.contains('process-flow')) {
          const children = entry.target.children;
          Array.from(children).forEach((child, index) => {
            child.style.transitionDelay = `${index * 150}ms`;
            child.style.opacity = '1';
            child.style.transform = 'translateY(0)';
          });
        }
        
        // If we revealed the stats strip/hero, trigger count-up
        if (entry.target.querySelector('.stats-strip') || entry.target.classList.contains('stats-strip') || entry.target.classList.contains('hero')) {
          triggerStatsCountUp();
        }

        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  // Auto-apply classes and observe elements
  revealSelectors.forEach(selector => {
    const elements = document.querySelectorAll(selector);
    elements.forEach(el => {
      // For grid layouts, we prepare the children for stagger
      if (selector === '.cards-grid' || 
          selector === '.why-grid' || 
          selector === '.about-values' || 
          selector === '.apart-grid' || 
          selector === '.process-flow') {
        el.classList.add('scroll-reveal-stagger');
        Array.from(el.children).forEach(child => {
          child.style.opacity = '0';
          child.style.transform = 'translateY(30px)';
          child.style.transition = 'opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1), transform 0.8s cubic-bezier(0.16, 1, 0.3, 1)';
        });
      } else {
        el.classList.add('scroll-reveal');
      }
      revealObserver.observe(el);
    });
  });

  // Observe the stats strip separately if not inside hero
  const statsStrip = document.querySelector('.stats-strip');
  if (statsStrip) {
    revealObserver.observe(statsStrip);
  }

  // 3. Stats Count-Up Animation
  let countUpTriggered = false;
  function triggerStatsCountUp() {
    if (countUpTriggered) return;
    countUpTriggered = true;

    const statNumbers = document.querySelectorAll('.stat-num');
    statNumbers.forEach(statEl => {
      const text = statEl.innerText.trim();
      // Extract number and suffix (like "+", " Lakh+")
      const match = text.match(/^([\d,]+)\s*(.*)$/);
      if (!match) return;

      const rawNumString = match[1].replace(/,/g, '');
      const targetValue = parseInt(rawNumString, 10);
      const suffix = match[2];

      if (isNaN(targetValue)) return;

      let start = 0;
      const duration = 2000; // 2 seconds
      const startTime = performance.now();

      function updateNumber(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Ease-out quad formula
        const easeProgress = progress * (2 - progress);
        const currentValue = Math.floor(easeProgress * targetValue);

        // Format with commas if target was > 999
        if (targetValue >= 1000) {
          statEl.innerText = currentValue.toLocaleString('en-IN') + suffix;
        } else {
          statEl.innerText = currentValue + suffix;
        }

        if (progress < 1) {
          requestAnimationFrame(updateNumber);
        } else {
          statEl.innerText = text; // ensure final text is exact
        }
      }

      requestAnimationFrame(updateNumber);
    });
  }
});
