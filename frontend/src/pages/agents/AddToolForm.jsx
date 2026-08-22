import { useId, useState } from "react";
import Button from "../../components/ui/Button";
import ErrorBanner from "../../components/ui/ErrorBanner";
import { RISK_LEVELS } from "../../utils/constants";
import { humanize } from "../../utils/format";

const EMPTY_TOOL = { name: "", description: "", destructive: false, risk_level: "low" };

export default function AddToolForm({ onSubmit, onCancel }) {
  const nameId = useId();
  const riskId = useId();
  const descriptionId = useId();
  const [tool, setTool] = useState(EMPTY_TOOL);
  const [fieldError, setFieldError] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [saving, setSaving] = useState(false);

  const update = (key) => (e) => {
    const value = e.target.type === "checkbox" ? e.target.checked : e.target.value;
    setTool((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!tool.name.trim()) {
      setFieldError("Tool name is required.");
      return;
    }
    setFieldError("");
    setSubmitError("");
    setSaving(true);
    try {
      await onSubmit(tool);
      setTool(EMPTY_TOOL);
    } catch (err) {
      setSubmitError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3 rounded-md border border-line bg-canvas p-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label htmlFor={nameId} className="mb-1 block text-xs font-medium text-ink-soft">
            Tool name
          </label>
          <input
            id={nameId}
            value={tool.name}
            onChange={update("name")}
            placeholder="e.g. refund_order"
            className="mono w-full rounded-md border border-line bg-surface px-3 py-2 text-sm focus:border-accent focus:outline-none"
          />
        </div>
        <div>
          <label htmlFor={riskId} className="mb-1 block text-xs font-medium text-ink-soft">
            Risk level
          </label>
          <select
            id={riskId}
            value={tool.risk_level}
            onChange={update("risk_level")}
            className="w-full rounded-md border border-line bg-surface px-3 py-2 text-sm focus:border-accent focus:outline-none"
          >
            {RISK_LEVELS.map((level) => (
              <option key={level} value={level}>
                {humanize(level)}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label htmlFor={descriptionId} className="mb-1 block text-xs font-medium text-ink-soft">
          Tool description
        </label>
        <textarea
          id={descriptionId}
          value={tool.description}
          onChange={update("description")}
          rows={2}
          placeholder="What does this tool do, and what can it affect?"
          className="w-full rounded-md border border-line bg-surface px-3 py-2 text-sm focus:border-accent focus:outline-none"
        />
      </div>

      <label className="flex items-center gap-2 text-sm text-ink-soft">
        <input
          type="checkbox"
          checked={tool.destructive}
          onChange={update("destructive")}
          className="h-4 w-4 rounded border-line text-accent focus:ring-accent"
        />
        This tool performs a destructive or irreversible action
      </label>

      {fieldError && <ErrorBanner message={fieldError} />}
      {submitError && <ErrorBanner message={submitError} />}

      <div className="flex justify-end gap-2">
        <Button type="button" variant="ghost" size="sm" onClick={onCancel} disabled={saving}>
          Cancel
        </Button>
        <Button type="submit" size="sm" loading={saving}>
          Add tool
        </Button>
      </div>
    </form>
  );
}
