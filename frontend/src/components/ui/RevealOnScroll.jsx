import { useEffect, useRef } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

// Fades + slides a single block in as it scrolls into view. Unlike
// ScrollReveal (which splits text word-by-word for headings), this is
// for wrapping whole chunks of repeating content -- list rows, cards,
// etc. -- where a simple opacity/translate reveal per item, staggered
// via the `delay` prop, reads better than per-word text animation.
export default function RevealOnScroll({ children, className = '', delay = 0, scrollContainerRef }) {
  const ref = useRef(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const scroller =
      (scrollContainerRef && scrollContainerRef.current) ||
      document.getElementById('app-scroll-container') ||
      window;

    // Same rule as ScrollReveal: content already visible on load has
    // nothing to "reveal" -- only animate items that start below the
    // fold, as the user actually scrolls to them.
    const viewportHeight = scroller === window ? window.innerHeight : scroller.clientHeight;
    const elTop =
      scroller === window
        ? el.getBoundingClientRect().top
        : el.getBoundingClientRect().top - scroller.getBoundingClientRect().top;
    const alreadyInView = elTop < viewportHeight * 0.92;

    if (alreadyInView) {
      gsap.set(el, { opacity: 1, y: 0 });
      return;
    }

    gsap.set(el, { opacity: 0, y: 24 });

    const tween = gsap.to(el, {
      opacity: 1,
      y: 0,
      duration: 0.6,
      delay,
      ease: 'power2.out',
      scrollTrigger: {
        trigger: el,
        scroller,
        start: 'top 92%',
        toggleActions: 'play none none none',
        once: true
      }
    });

    const raf = requestAnimationFrame(() => ScrollTrigger.refresh());

    return () => {
      cancelAnimationFrame(raf);
      tween.scrollTrigger?.kill();
      tween.kill();
    };
  }, [delay, scrollContainerRef]);

  return (
    <div ref={ref} className={className}>
      {children}
    </div>
  );
}
