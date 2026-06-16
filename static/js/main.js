// EcoFleet Express - Main JS

// Theme toggle (light / dark). Persists choice in localStorage.
// The initial theme is applied pre-paint by an inline script in the <head>;
// here we just wire up the toggle buttons.
window.EcoFleetTheme = (function () {
  var KEY = 'ef-theme';

  function current() {
    return document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
  }

  function apply(theme) {
    if (theme === 'light') {
      document.documentElement.setAttribute('data-theme', 'light');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
    document.querySelectorAll('.theme-toggle').forEach(function (btn) {
      btn.setAttribute('aria-pressed', theme === 'light' ? 'true' : 'false');
    });
  }

  function toggle() {
    var next = current() === 'light' ? 'dark' : 'light';
    try { localStorage.setItem(KEY, next); } catch (e) {}
    apply(next);
  }

  function init() {
    apply(current());
    document.querySelectorAll('.theme-toggle').forEach(function (btn) {
      btn.addEventListener('click', toggle);
    });
  }

  return { init: init, toggle: toggle, apply: apply };
})();

document.addEventListener('DOMContentLoaded', function () {

  window.EcoFleetTheme.init();

  // Mobile nav toggle
  const hamburger = document.getElementById('hamburger');
  const navLinks = document.querySelector('.nav-links');
  const mobileNavOverlay = document.getElementById('mobileNavOverlay');

  if (hamburger && navLinks) {
    const toggleMenu = () => {
      const isOpen = navLinks.classList.toggle('open');
      if (mobileNavOverlay) {
        if (isOpen) {
          mobileNavOverlay.classList.add('visible');
        } else {
          mobileNavOverlay.classList.remove('visible');
        }
      }
      hamburger.classList.toggle('active');
    };

    const closeMenu = () => {
      navLinks.classList.remove('open');
      if (mobileNavOverlay) {
        mobileNavOverlay.classList.remove('visible');
      }
      hamburger.classList.remove('active');
    };

    hamburger.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleMenu();
    });

    if (mobileNavOverlay) {
      mobileNavOverlay.addEventListener('click', closeMenu);
    }

    // Close nav on link click
    navLinks.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', closeMenu);
    });

    // Close on escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeMenu();
      }
    });
  }

  // Smooth scroll for nav track link
  const navTrackLink = document.getElementById('navTrackLink');
  if (navTrackLink) {
    navTrackLink.addEventListener('click', (e) => {
      const pathname = window.location.pathname;
      if (pathname === '/' || pathname === '/home/' || pathname.indexOf('/portal/') === -1) {
        const trackSec = document.querySelector('.track-section');
        if (trackSec) {
          e.preventDefault();
          trackSec.scrollIntoView({ behavior: 'smooth' });
        }
      }
    });
  }

  // Cookie banner
  const cookieBanner = document.getElementById('cookieBanner');
  const cookieAccept = document.getElementById('cookieAccept');
  const cookieDecline = document.getElementById('cookieDecline');

  if (cookieBanner) {
    // Show banner if not already accepted
    if (!localStorage.getItem('cookieConsent')) {
      cookieBanner.classList.remove('hidden');
    } else {
      cookieBanner.classList.add('hidden');
    }

    cookieAccept.addEventListener('click', () => {
      localStorage.setItem('cookieConsent', 'accepted');
      cookieBanner.classList.add('hidden');
    });

    cookieDecline.addEventListener('click', () => {
      localStorage.setItem('cookieConsent', 'declined');
      cookieBanner.classList.add('hidden');
    });
  }

  // Scroll to top
  const scrollTop = document.getElementById('scrollTop');

  window.addEventListener('scroll', () => {
    if (scrollTop) {
      if (window.scrollY > 400) {
        scrollTop.classList.add('visible');
      } else {
        scrollTop.classList.remove('visible');
      }
    }
  });

  if (scrollTop) {
    scrollTop.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // Contact Form Submission Feedback
  const contactForm = document.querySelector('.contact-form');
  if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
      e.preventDefault();
      
      const submitBtn = contactForm.querySelector('.contact-submit');
      if (!submitBtn) return;
      
      // Loading State
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="ti ti-loader animate-spin" style="margin-right: 8px;"></i> Sending...';
      
      // Simulate network request
      setTimeout(() => {
        // Success State
        const formWrap = document.querySelector('.contact-form-wrap');
        if (formWrap) {
          formWrap.innerHTML = `
            <div class="contact-success-state" style="text-align: center; padding: 40px 20px; animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);">
              <div style="font-size: 64px; color: var(--cyan); margin-bottom: 20px;"><i class="ti ti-circle-check"></i></div>
              <h2 style="font-size: 24px; margin-bottom: 12px; font-weight: 700; color: var(--text);">Message Sent Successfully!</h2>
              <p style="color: var(--muted); font-size: 15px; margin-bottom: 24px; max-width: 400px; margin-left: auto; margin-right: auto; line-height: 1.6;">
                Thank you for reaching out. Our operations team will review your message and get back to you within 24 hours.
              </p>
              <button class="btn-primary" onclick="window.location.reload()" style="margin: 0 auto; display: inline-flex; align-items: center; gap: 8px; justify-content: center;">
                <i class="ti ti-arrow-left"></i> Send Another Message
              </button>
            </div>
          `;
        }
      }, 1500);
    });
  }

});