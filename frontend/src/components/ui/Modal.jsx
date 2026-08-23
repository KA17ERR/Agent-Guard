import { useEffect, useId } from "react";
import Icon from "./Icon";

export default function Modal({ open, title, children, onClose }) {
  const titleId = useId();

  // Close on Escape while open — standard dialog behavior, and the only
  // keyboard path to dismiss besides tabbing to the close button.
  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (e) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md rounded-lg border border-line/70 bg-surface/95 backdrop-blur-sm p-5 shadow-card"
      >
        <div className="mb-3 flex items-start justify-between">
          <h3 id={titleId} className="text-sm font-semibold text-ink">
            {title}
          </h3>
          <button onClick={onClose} className="text-ink-faint hover:text-ink" aria-label="Close">
            <Icon name="x" className="h-4 w-4" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
