import { useEffect } from 'react';

export default function useScrollAnimation(selector = '[data-reveal]', options = {}) {
  useEffect(() => {
    const { threshold = 0.15, rootMargin = '0px' } = options;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold, rootMargin }
    );

    const elements = document.querySelectorAll(selector);
    elements.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, [selector, options.threshold, options.rootMargin]);
}
