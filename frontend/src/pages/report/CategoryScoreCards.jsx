import ProgressBar from "../../components/ui/ProgressBar";

const DIMENSIONS = [
  { key: "task_success", label: "Task Success" },
  { key: "safety", label: "Safety" },
  { key: "tool_reliability", label: "Tool Reliability" },
  { key: "goal_adherence", label: "Goal Adherence" },
  { key: "truthfulness", label: "Truthfulness" },
];

export default function CategoryScoreCards({ categoryScores }) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
      {DIMENSIONS.map((d) => (
        <div key={d.key} className="rounded-md border border-line bg-canvas p-3">
          <ProgressBar value={categoryScores[d.key]} label={d.label} />
        </div>
      ))}
    </div>
  );
}
