import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import apiClient from "../../api/client";
import Icon from "../ui/Icon";
import { NAV_ITEMS } from "../../utils/constants";

function currentTitle(pathname) {
  const match = NAV_ITEMS.find((item) =>
    item.to === "/" ? pathname === "/" : pathname.startsWith(item.to)
  );
  return match?.label || "AgentGuard";
}

export default function Navbar({ onMenuClick }) {
  const { pathname } = useLocation();
  const [backendUp, setBackendUp] = useState(null); // null = checking

  useEffect(() => {
    let cancelled = false;
    const check = () => {
      apiClient
        .get("/api/health")
        .then(() => !cancelled && setBackendUp(true))
        .catch(() => !cancelled && setBackendUp(false));
    };
    check();
    const interval = setInterval(check, 15000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-line bg-surface px-4 sm:px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="text-ink-soft hover:text-ink md:hidden"
          aria-label="Open navigation menu"
        >
          <Icon name="list" className="h-5 w-5" />
        </button>
        <h1 className="text-sm font-semibold text-ink">{currentTitle(pathname)}</h1>
      </div>
      <div className="flex items-center gap-2 text-xs text-ink-faint">
        <span
          className={`h-1.5 w-1.5 rounded-full ${
            backendUp === null ? "bg-signal-neutral" : backendUp ? "bg-signal-safe" : "bg-signal-danger"
          }`}
        />
        <span className="hidden sm:inline">
          {backendUp === null ? "Checking API…" : backendUp ? "API connected" : "API unreachable"}
        </span>
      </div>
    </header>
  );
}
