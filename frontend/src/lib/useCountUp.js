import { useEffect, useRef, useState } from 'react';

// Animates a number from 0 to `target` once, whenever `target` changes.
// easeOutCubic — quick start, gentle settle. No IntersectionObserver:
// this is used in an already-visible workspace panel, not a scroll-in
// marketing section.
export function useCountUp(target, { duration = 900, decimals = 0 } = {}) {
  const [value, setValue] = useState(0);
  const raf = useRef(null);

  useEffect(() => {
    const start = performance.now();
    const from = 0;
    const to = Number.isFinite(target) ? target : 0;

    function tick(now) {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(from + (to - from) * eased);
      if (t < 1) raf.current = requestAnimationFrame(tick);
    }

    raf.current = requestAnimationFrame(tick);
    return () => raf.current && cancelAnimationFrame(raf.current);
  }, [target, duration]);

  return decimals > 0 ? value.toFixed(decimals) : Math.round(value);
}