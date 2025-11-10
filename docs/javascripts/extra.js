/**
 * Transire Documentation - Enhanced JavaScript
 * Provides interactive features and improved UX
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {

  // ============================================================================
  // SMOOTH SCROLLING FOR ANCHOR LINKS
  // ============================================================================

  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (href !== '#' && href !== '') {
        e.preventDefault();
        const target = document.querySelector(href);
        if (target) {
          target.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
          // Update URL without jumping
          history.pushState(null, null, href);
        }
      }
    });
  });

  // ============================================================================
  // ENHANCED CODE BLOCK COPY FEEDBACK
  // ============================================================================

  // Add success feedback when code is copied
  document.addEventListener('copy', function(e) {
    // Find the clipboard button that was clicked
    const activeElement = document.activeElement;
    if (activeElement && activeElement.classList.contains('md-clipboard')) {
      // Create temporary success message
      const originalTitle = activeElement.getAttribute('title');
      activeElement.setAttribute('title', 'Copied!');

      // Revert after 2 seconds
      setTimeout(() => {
        activeElement.setAttribute('title', originalTitle || 'Copy to clipboard');
      }, 2000);
    }
  });

  // ============================================================================
  // TABLE OF CONTENTS HIGHLIGHT ON SCROLL
  // ============================================================================

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      const id = entry.target.getAttribute('id');
      if (entry.isIntersecting) {
        // Remove active class from all TOC links
        document.querySelectorAll('.md-nav__link').forEach(link => {
          link.classList.remove('md-nav__link--active');
        });

        // Add active class to current section's TOC link
        const activeLink = document.querySelector(`.md-nav__link[href="#${id}"]`);
        if (activeLink) {
          activeLink.classList.add('md-nav__link--active');
        }
      }
    });
  }, {
    rootMargin: '-20% 0px -80% 0px'
  });

  // Observe all headings
  document.querySelectorAll('h1[id], h2[id], h3[id]').forEach(heading => {
    observer.observe(heading);
  });

  // ============================================================================
  // EXTERNAL LINK INDICATORS
  // ============================================================================

  // Add external link icon to external links
  document.querySelectorAll('a[href^="http"]').forEach(link => {
    // Check if link is not to transire.github.io
    if (!link.href.includes('transire.github.io') && !link.querySelector('img')) {
      link.setAttribute('target', '_blank');
      link.setAttribute('rel', 'noopener noreferrer');
      // Add external link icon if not already present
      if (!link.classList.contains('md-source')) {
        link.innerHTML += ' <svg style="width:12px;height:12px;display:inline;vertical-align:middle;margin-left:2px;opacity:0.6;" viewBox="0 0 24 24"><path fill="currentColor" d="M14,3V5H17.59L7.76,14.83L9.17,16.24L19,6.41V10H21V3M19,19H5V5H12V3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V12H19V19Z" /></svg>';
      }
    }
  });

  // ============================================================================
  // KEYBOARD SHORTCUTS
  // ============================================================================

  document.addEventListener('keydown', function(e) {
    // Open search with '/' key
    if (e.key === '/' && !e.ctrlKey && !e.metaKey && !e.altKey) {
      const searchInput = document.querySelector('.md-search__input');
      if (searchInput && document.activeElement !== searchInput) {
        e.preventDefault();
        searchInput.focus();
      }
    }

    // Close search with Escape
    if (e.key === 'Escape') {
      const searchInput = document.querySelector('.md-search__input');
      if (searchInput && document.activeElement === searchInput) {
        searchInput.blur();
      }
    }
  });

  // ============================================================================
  // COPY CODE BLOCK ENHANCEMENT
  // ============================================================================

  // Add line numbers to code blocks (if not already present)
  document.querySelectorAll('pre > code').forEach(code => {
    // Skip if already has line numbers
    if (code.querySelector('.linenodiv')) return;

    const lines = code.textContent.split('\n');
    // Only add line numbers if more than 10 lines
    if (lines.length > 10) {
      code.classList.add('has-line-numbers');
    }
  });

  // ============================================================================
  // ANIMATED COUNTERS (for feature cards with numbers)
  // ============================================================================

  function animateCounter(element, target, duration = 2000) {
    let start = 0;
    const increment = target / (duration / 16); // 60fps

    const timer = setInterval(() => {
      start += increment;
      if (start >= target) {
        element.textContent = target;
        clearInterval(timer);
      } else {
        element.textContent = Math.floor(start);
      }
    }, 16);
  }

  // Observe elements with data-counter attribute
  const counterObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting && !entry.target.dataset.counted) {
        const target = parseInt(entry.target.dataset.counter);
        animateCounter(entry.target, target);
        entry.target.dataset.counted = 'true';
      }
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('[data-counter]').forEach(el => {
    counterObserver.observe(el);
  });

  // ============================================================================
  // FADE IN ANIMATION ON SCROLL
  // ============================================================================

  const fadeObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-fade-in');
        fadeObserver.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.1
  });

  // Observe all feature cards and admonitions
  document.querySelectorAll('.feature-card, .admonition, .md-typeset table').forEach(el => {
    fadeObserver.observe(el);
  });

  // ============================================================================
  // ENHANCED SEARCH
  // ============================================================================

  const searchInput = document.querySelector('.md-search__input');
  if (searchInput) {
    // Save recent searches to localStorage
    searchInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter' && this.value.trim()) {
        let recentSearches = JSON.parse(localStorage.getItem('transire-recent-searches') || '[]');
        recentSearches = [this.value.trim(), ...recentSearches.filter(s => s !== this.value.trim())].slice(0, 5);
        localStorage.setItem('transire-recent-searches', JSON.stringify(recentSearches));
      }
    });
  }

  // ============================================================================
  // COPY EMAIL LINKS (for support/contact pages)
  // ============================================================================

  document.querySelectorAll('a[href^="mailto:"]').forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      const email = this.href.replace('mailto:', '');
      navigator.clipboard.writeText(email).then(() => {
        // Show temporary tooltip
        const tooltip = document.createElement('span');
        tooltip.textContent = 'Email copied!';
        tooltip.style.cssText = 'position:absolute;background:#10b981;color:white;padding:4px 8px;border-radius:4px;font-size:12px;margin-left:8px;';
        this.parentNode.insertBefore(tooltip, this.nextSibling);
        setTimeout(() => tooltip.remove(), 2000);
      });
    });
  });

  // ============================================================================
  // PERFORMANCE: LAZY LOAD IMAGES
  // ============================================================================

  if ('loading' in HTMLImageElement.prototype) {
    // Browser supports lazy loading
    document.querySelectorAll('img').forEach(img => {
      img.loading = 'lazy';
    });
  } else {
    // Fallback for browsers that don't support lazy loading
    const imageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          if (img.dataset.src) {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
          }
          observer.unobserve(img);
        }
      });
    });

    document.querySelectorAll('img[data-src]').forEach(img => {
      imageObserver.observe(img);
    });
  }

  // ============================================================================
  // TAB MEMORY (remember selected tab on page reload)
  // ============================================================================

  document.querySelectorAll('.tabbed-set input[type="radio"]').forEach(radio => {
    radio.addEventListener('change', function() {
      const tabsetId = this.closest('.tabbed-set').id || 'default';
      const tabId = this.id;
      localStorage.setItem(`transire-tab-${tabsetId}`, tabId);
    });

    // Restore selected tab
    const tabsetId = radio.closest('.tabbed-set').id || 'default';
    const savedTab = localStorage.getItem(`transire-tab-${tabsetId}`);
    if (savedTab === radio.id) {
      radio.checked = true;
    }
  });

  // ============================================================================
  // PRINT STYLES OPTIMIZATION
  // ============================================================================

  window.addEventListener('beforeprint', function() {
    // Expand all collapsed sections before printing
    document.querySelectorAll('details').forEach(details => {
      details.setAttribute('open', '');
      details.dataset.wasOpen = 'true';
    });
  });

  window.addEventListener('afterprint', function() {
    // Collapse sections that were collapsed before printing
    document.querySelectorAll('details[data-was-open]').forEach(details => {
      details.removeAttribute('open');
      details.removeAttribute('data-was-open');
    });
  });

  // ============================================================================
  // CONSOLE EASTER EGG
  // ============================================================================

  console.log('%c🚀 Transire Documentation', 'color: #4c51bf; font-size: 20px; font-weight: bold;');
  console.log('%cBuilt with Material for MkDocs', 'color: #06b6d4; font-size: 14px;');
  console.log('%cFound a bug? Report it: https://github.com/transire/transire/issues', 'color: #666; font-size: 12px;');

});
