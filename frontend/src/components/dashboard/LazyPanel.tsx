"use client";

import { useEffect, useRef, useState } from "react";
import type React from "react";

type LazyPanelProps = {
  children: React.ReactNode;
  label?: string;
  minHeight?: number;
  rootMargin?: string;
};

export function LazyPanel({ children, label = "Dashboard module", minHeight = 420, rootMargin = "700px" }: LazyPanelProps) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [active, setActive] = useState(() => typeof window !== "undefined" && !("IntersectionObserver" in window));

  useEffect(() => {
    const node = ref.current;
    if (!node || active) return;

    const margin = Number.parseFloat(rootMargin) || 700;
    const activateIfNearViewport = () => {
      const rect = node.getBoundingClientRect();
      if (rect.top <= window.innerHeight + margin && rect.bottom >= -margin) {
        setActive(true);
        return true;
      }
      return false;
    };

    if (activateIfNearViewport()) return;

    window.addEventListener("scroll", activateIfNearViewport, { passive: true });
    window.addEventListener("resize", activateIfNearViewport);

    if (!("IntersectionObserver" in window)) {
      return () => {
        window.removeEventListener("scroll", activateIfNearViewport);
        window.removeEventListener("resize", activateIfNearViewport);
      };
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) {
          setActive(true);
          observer.disconnect();
        }
      },
      { rootMargin },
    );
    observer.observe(node);
    return () => {
      observer.disconnect();
      window.removeEventListener("scroll", activateIfNearViewport);
      window.removeEventListener("resize", activateIfNearViewport);
    };
  }, [active, rootMargin]);

  return (
    <div ref={ref} style={{ minHeight: active ? undefined : minHeight }}>
      {active ? (
        children
      ) : (
        <div className="border border-line/70 bg-panel2/45 p-4 text-sm text-slate-500">
          {label}: preparing module.
        </div>
      )}
    </div>
  );
}
