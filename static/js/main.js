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


});