import Icon from "./Icon";
import BlurText from "./BlurText";

export default function EmptyState({ icon = "flask", title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-line/70 bg-surface-soft px-6 py-16 text-center">
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-accent-soft text-accent">
        <Icon name={icon} className="h-5 w-5" />
      </div>
      <h3 className="text-sm font-semibold text-ink">{title}</h3>
      {description && (
        <BlurText
          text={description}
          animateBy="words"
          direction="top"
          delay={25}
          stepDuration={0.3}
          className="mx-auto mt-1 max-w-sm justify-center text-sm !leading-normal text-ink-faint text-center"
        />
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
