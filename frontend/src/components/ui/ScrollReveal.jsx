import { useEffect, useRef, useMemo } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

const ScrollReveal = ({
  children,
  scrollContainerRef,
  enableBlur = true,
  baseOpacity = 0.1,
  baseRotation = 3,
  blurStrength = 4,
  containerClassName = '',
  textClassName = '',
  as = 'div',
  textStyle
}) => {
  const containerRef = useRef(null);

  const splitText = useMemo(() => {
    const text = typeof children === 'string' ? children : '';
    return text.split(/(\s+)/).map((word, index) => {
      if (word.match(/^\s+$/)) return word;
      return (
        <span className="inline-block word" key={index}>
          {word}
        </span>
      );
    });
  }, [children]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const scroller =
      scrollContainerRef && scrollContainerRef.current
        ? scrollContainerRef.current
        : document.getElementById('app-scroll-container') || window;

    const wordElements = el.querySelectorAll('.word');
    if (!wordElements.length) return;

    // Content already sitting inside the visible viewport at load time
    // has nothing to "reveal" -- animating it anyway just plays the
    // whole effect immediately on page load, which reads as a flash
    // rather than a scroll-driven reveal. Only elements that start
    // below the fold get the blur/fade-in treatment; anything already
    // on-screen just renders normally.
    const viewportHeight = scroller === window ? window.innerHeight : scroller.clientHeight;
    const elTopWithinScroller =
      scroller === window
        ? el.getBoundingClientRect().top
        : el.getBoundingClientRect().top - scroller.getBoundingClientRect().top;
    const alreadyInView = elTopWithinScroller < viewportHeight * 0.88;

    if (alreadyInView) {
      gsap.set(el, { rotate: 0 });
      gsap.set(wordElements, { opacity: 1, filter: 'blur(0px)' });
      return;
    }

    gsap.set(el, { transformOrigin: '0% 50%', rotate: baseRotation });
    gsap.set(wordElements, {
      opacity: baseOpacity,
      filter: enableBlur ? `blur(${blurStrength}px)` : 'none',
      willChange: 'opacity, filter'
    });

    const tl = gsap.timeline({
      scrollTrigger: {
        trigger: el,
        scroller,
        start: 'top 88%',
        toggleActions: 'play none none none',
        once: true
      },
      defaults: { ease: 'power2.out', duration: 0.7 }
    });

    tl.to(el, { rotate: 0 }, 0);
    tl.to(wordElements, { opacity: 1, stagger: 0.04 }, 0);
    if (enableBlur) {
      tl.to(wordElements, { filter: 'blur(0px)', stagger: 0.04 }, 0);
    }

    // Fonts, async data, and the animated background can all shift
    // layout after this effect runs -- re-measure trigger positions
    // once things settle so "start: top 88%" is checked against the
    // real, final layout instead of a half-rendered one.
    const raf = requestAnimationFrame(() => ScrollTrigger.refresh());

    return () => {
      cancelAnimationFrame(raf);
      tl.scrollTrigger?.kill();
      tl.kill();
    };
  }, [scrollContainerRef, enableBlur, baseRotation, baseOpacity, blurStrength]);

  const Wrapper = as;
  return (
    <Wrapper ref={containerRef} className={containerClassName}>
      <p
        className={`text-[clamp(1.6rem,4vw,3rem)] leading-[1.5] font-semibold text-ink ${textClassName}`}
        style={textStyle}
      >
        {splitText}
      </p>
    </Wrapper>
  );
};

export default ScrollReveal;
