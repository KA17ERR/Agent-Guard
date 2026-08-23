import { useEffect, useRef, useState } from "react";
import { useLocation, Outlet } from "react-router-dom";
import { motion, AnimatePresence } from "motion/react";
import logo from "../../assets/logo-shield.svg";
import CircularText from "../ui/CircularText";

// How long the logo loader stays on screen for each navigation. Long enough
// to read as a deliberate transition, short enough to never feel like the
// app is stuck "loading" something real.
const LOADER_DURATION = 650;

export default function PageTransition() {
  const location = useLocation();
  const [displayLocation, setDisplayLocation] = useState(location);
  const [showLoader, setShowLoader] = useState(false);
  const timeoutRef = useRef(null);
  const isFirstRender = useRef(true);

  useEffect(() => {
    // Never show the loader for the very first page the app boots into.
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    // A change in query string / hash on the same route (e.g. ?runId=...)
    // isn't a "new page" — only swap on an actual path change.
    if (location.pathname === displayLocation.pathname) return;

    setShowLoader(true);
    clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      // The outgoing page is fully hidden behind the opaque loader by now,
      // so swapping straight to the new route here is invisible to the
      // user — no separate exit animation needed on the page itself.
      setDisplayLocation(location);
      setShowLoader(false);
    }, LOADER_DURATION);

    return () => clearTimeout(timeoutRef.current);
  }, [location, displayLocation.pathname]);

  return (
    <>
      <motion.div
        key={displayLocation.pathname}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      >
        <Outlet />
      </motion.div>

      <AnimatePresence>
        {showLoader && (
          <motion.div
            key="page-loader"
            className="fixed inset-0 z-[9999] flex items-center justify-center bg-[#0B0D13]/85 backdrop-blur-md"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
          >
            <div className="relative flex h-[200px] w-[200px] items-center justify-center">
              {/* Spinning text ring around the logo */}
              <CircularText
                text="AGENTGUARD*RELIABILITY*ENGINE*"
                onHover="speedUp"
                spinDuration={20}
                className="text-[13px] tracking-widest drop-shadow-[0_0_6px_rgba(99,102,241,0.65)]"
              />

              {/* Soft expanding pulse rings + logo, centered inside the ring */}
              <div className="absolute inset-0 flex items-center justify-center">
                {[0, 0.35].map((delay) => (
                  <motion.span
                    key={delay}
                    className="absolute h-16 w-16 rounded-full border-2 border-accent/50"
                    initial={{ scale: 0.8, opacity: 0.7 }}
                    animate={{ scale: 2, opacity: 0 }}
                    transition={{ duration: 1.3, repeat: Infinity, ease: "easeOut", delay }}
                  />
                ))}

                <motion.img
                  src={logo}
                  alt="AgentGuard"
                  className="relative h-14 w-14 rounded-2xl"
                  style={{ boxShadow: "0 0 32px rgba(79, 70, 229, 0.65)" }}
                  initial={{ scale: 0.4, rotate: -20, opacity: 0 }}
                  animate={{
                    scale: [0.4, 1.15, 1],
                    rotate: [-20, 8, 0],
                    opacity: 1
                  }}
                  transition={{ duration: 0.55, ease: [0.34, 1.56, 0.64, 1] }}
                />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
