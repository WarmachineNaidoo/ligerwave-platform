document.addEventListener('DOMContentLoaded', () => {

    // Navbar scroll effect
    const navbar = document.getElementById('navbar');
    let lastScroll = 0;

    window.addEventListener('scroll', () => {
        const currentScroll = window.scrollY;
        navbar.classList.toggle('scrolled', currentScroll > 80);
        lastScroll = currentScroll;
    });

    // Mobile nav toggle
    const navToggle = document.getElementById('navToggle');
    const navLinks = document.getElementById('navLinks');

    navToggle.addEventListener('click', () => {
        navToggle.classList.toggle('active');
        navLinks.classList.toggle('active');
    });

    navLinks.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            navToggle.classList.remove('active');
            navLinks.classList.remove('active');
        });
    });

    // Cursor tracking
    const cursorDot = document.querySelector('.cursor-dot');
    const cursorRing = document.querySelector('.cursor-ring');

    if (cursorDot && cursorRing) {
        let mouseX = 0, mouseY = 0;
        let ringX = 0, ringY = 0;

        document.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
            cursorDot.style.left = mouseX + 'px';
            cursorDot.style.top = mouseY + 'px';
        });

        function animateRing() {
            ringX += (mouseX - ringX) * 0.1;
            ringY += (mouseY - ringY) * 0.1;
            cursorRing.style.left = ringX + 'px';
            cursorRing.style.top = ringY + 'px';
            requestAnimationFrame(animateRing);
        }
        animateRing();
    }

    // Animated counter
    const counters = document.querySelectorAll('.stat-number[data-count]');

    function animateCounter(el) {
        const target = parseInt(el.dataset.count);
        const duration = 2000;
        const steps = 60;
        const increment = target / steps;
        let current = 0;
        let step = 0;

        const timer = setInterval(() => {
            step++;
            current = Math.min(current + increment, target);
            el.textContent = Math.round(current);
            if (step >= steps) {
                el.textContent = target;
                clearInterval(timer);
            }
        }, duration / steps);
    }

    // Counters with Intersection Observer
    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counter = entry.target;
                if (!counter.dataset.animated) {
                    counter.dataset.animated = 'true';
                    animateCounter(counter);
                }
                counterObserver.unobserve(counter);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(c => counterObserver.observe(c));

    // Reveal animations with Intersection Observer
    const revealElements = document.querySelectorAll('.reveal');

    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                revealObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    revealElements.forEach(el => revealObserver.observe(el));

    // GSAP scroll animations
    if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
        gsap.registerPlugin(ScrollTrigger);

        // Hero parallax
        gsap.to('.hero-bg', {
            scrollTrigger: {
                trigger: '.hero',
                start: 'top top',
                end: 'bottom top',
                scrub: 1.5
            },
            y: 80,
            scale: 1.05
        });

        gsap.to('.hero-content', {
            scrollTrigger: {
                trigger: '.hero',
                start: 'top top',
                end: 'bottom center',
                scrub: 1
            },
            y: 60,
            opacity: 0.6
        });

        // Tech cards stagger
        gsap.from('.tech-card', {
            scrollTrigger: {
                trigger: '.tech-grid',
                start: 'top 85%',
                once: true
            },
            y: 60,
            opacity: 0,
            duration: 0.6,
            stagger: 0.08,
            ease: 'power2.out'
        });

        // Mission cards stagger
        gsap.from('.mission-card', {
            scrollTrigger: {
                trigger: '.mission-grid',
                start: 'top 85%',
                once: true
            },
            y: 50,
            opacity: 0,
            duration: 0.6,
            stagger: 0.12,
            ease: 'power2.out'
        });

        // Team cards stagger
        gsap.from('.team-card', {
            scrollTrigger: {
                trigger: '.team-grid',
                start: 'top 85%',
                once: true
            },
            y: 50,
            opacity: 0,
            duration: 0.6,
            stagger: 0.1,
            ease: 'power2.out'
        });

        // Approach timeline - animate steps on scroll
        gsap.from('.approach-step', {
            scrollTrigger: {
                trigger: '.approach-timeline',
                start: 'top 80%',
                end: 'bottom center',
                scrub: 1
            },
            x: -30,
            opacity: 0,
            stagger: 0.2
        });

        // Hero title reveal
        const heroTitle = document.querySelector('.hero-title');
        if (heroTitle) {
            gsap.from(heroTitle, {
                y: 60,
                opacity: 0,
                duration: 1,
                delay: 0.2,
                ease: 'power3.out'
            });
        }

        gsap.from('.hero-subtitle', {
            y: 40,
            opacity: 0,
            duration: 0.8,
            delay: 0.4,
            ease: 'power3.out'
        });

        gsap.from('.hero-actions', {
            y: 30,
            opacity: 0,
            duration: 0.8,
            delay: 0.6,
            ease: 'power3.out'
        });

        gsap.from('.hero-stats', {
            y: 30,
            opacity: 0,
            duration: 0.8,
            delay: 0.8,
            ease: 'power3.out'
        });

        gsap.from('.hero-badge', {
            y: 20,
            opacity: 0,
            duration: 0.6,
            delay: 0.1,
            ease: 'power3.out'
        });

        // Section header animations
        document.querySelectorAll('.section-header').forEach(header => {
            const tag = header.querySelector('.section-tag');
            const title = header.querySelector('h2');
            const desc = header.querySelector('.section-desc');

            if (tag) {
                gsap.from(tag, {
                    scrollTrigger: {
                        trigger: header,
                        start: 'top 80%',
                        once: true
                    },
                    y: 20,
                    opacity: 0,
                    duration: 0.4
                });
            }

            if (title) {
                gsap.from(title, {
                    scrollTrigger: {
                        trigger: header,
                        start: 'top 80%',
                        once: true
                    },
                    y: 30,
                    opacity: 0,
                    duration: 0.6,
                    delay: 0.1
                });
            }

            if (desc) {
                gsap.from(desc, {
                    scrollTrigger: {
                        trigger: header,
                        start: 'top 80%',
                        once: true
                    },
                    y: 20,
                    opacity: 0,
                    duration: 0.5,
                    delay: 0.2
                });
            }
        });
    }

    // Contact form handler
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const btn = contactForm.querySelector('button[type="submit"]');
            const originalText = btn.textContent;
            btn.textContent = 'Message Sent ✓';
            btn.style.background = 'var(--green-400)';
            setTimeout(() => {
                btn.textContent = originalText;
                btn.style.background = '';
                contactForm.reset();
            }, 3000);
        });
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', (e) => {
            const href = anchor.getAttribute('href');
            if (href === '#') return;
            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // Back to top button
    const backToTop = document.getElementById('backToTop');
    if (backToTop) {
        window.addEventListener('scroll', () => {
            backToTop.classList.toggle('visible', window.scrollY > 400);
        }, { passive: true });

        backToTop.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
});
