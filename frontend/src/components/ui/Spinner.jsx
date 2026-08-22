export default function Spinner({ label = "Loading…", className = "" }) {
  return (
    <div className={`flex items-center gap-2.5 text-sm text-ink-faint ${className}`}>
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-line border-t-accent" />
      {label}
    </div>
  );
}
