import Icon from "./Icon";

export default function ErrorBanner({ message, className = "" }) {
  if (!message) return null;
  return (
    <div
      className={`flex items-start gap-2 rounded-md border border-signal-danger/30 bg-signal-danger-soft px-3 py-2.5 text-sm text-signal-danger ${className}`}
      role="alert"
    >
      <Icon name="alert" className="mt-0.5 h-4 w-4 shrink-0" />
      <span>{message}</span>
    </div>
  );
}
