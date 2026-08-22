import { useEffect } from "react";
import { NavLink } from "react-router-dom";
import Icon from "../ui/Icon";
import { NAV_ITEMS } from "../../utils/constants";

// The one dark surface in the app. Framing it as a "control rail" mirrors
// the product's own subject matter — a slim colored rail is also how
// TraceTimeline and Card mark severity, so the sidebar's active-item
// indicator uses the same 3px rail language.
//
// Below the `md` breakpoint this renders as an off-canvas drawer (fixed,
// translated out of view, toggled by Navbar's menu button) with a
// backdrop; at `md` and above it's always-visible and the drawer/backdrop
// classes are inert.
export default function Sidebar({ open, onClose }) {
  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (e) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-40 bg-ink/40 md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 flex h-screen w-60 shrink-0 flex-col bg-rail text-white/70
          transition-transform duration-200 ease-out
          md:static md:z-auto md:translate-x-0
          ${open ? "translate-x-0" : "-translate-x-full"}`}
      >
        <div className="flex items-center justify-between gap-2 px-5 py-5">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-accent">
              <Icon name="shield" className="h-4 w-4 text-white" />
            </div>
            <div>
              <p className="text-sm font-semibold leading-tight text-white">AgentGuard</p>
              <p className="text-[11px] leading-tight text-white/40">Reliability Engine</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-white/50 hover:text-white md:hidden"
            aria-label="Close navigation menu"
          >
            <Icon name="x" className="h-4 w-4" />
          </button>
        </div>

        <nav className="flex-1 space-y-0.5 px-3 py-2">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `relative flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-rail-soft text-white before:absolute before:left-0 before:top-1.5 before:bottom-1.5 before:w-[3px] before:rounded-full before:bg-accent"
                    : "hover:bg-rail-soft hover:text-white"
                }`
              }
            >
              <Icon name={item.icon} className="h-4 w-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-white/10 px-5 py-4 text-[11px] text-white/35">
          Sandbox mode — all tool calls are mocked.
        </div>
      </aside>
    </>
  );
}
