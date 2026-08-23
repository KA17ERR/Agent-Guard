import { cloneElement, useEffect, useId, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import agentsApi from "../../api/agents";
import Card, { CardHeader } from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import ErrorBanner from "../../components/ui/ErrorBanner";
import Table from "../../components/ui/Table";
import Icon from "../../components/ui/Icon";
import { RiskBadge, DestructiveBadge } from "../../components/ui/StatusBadge";
import AddToolForm from "./AddToolForm";

const EMPTY_AGENT = { name: "", domain: "", system_prompt: "", version: "v1", description: "" };

function validate(agent) {
  const errors = {};
  if (!agent.name.trim()) errors.name = "Agent name is required.";
  if (!agent.domain.trim()) errors.domain = "Domain is required.";
  if (!agent.system_prompt.trim()) errors.system_prompt = "System prompt is required.";
  return errors;
}

function Field({ label, error, hint, children }) {
  const inputId = useId();
  const hintId = useId();
  const errorId = useId();
  return (
    <div>
      <label htmlFor={inputId} className="mb-1 block text-sm font-medium text-ink">
        {label}
      </label>
      {cloneElement(children, {
        id: inputId,
        "aria-describedby": error ? errorId : hint ? hintId : undefined,
        "aria-invalid": error ? "true" : undefined,
      })}
      {hint && !error && (
        <p id={hintId} className="mt-1 text-xs text-ink-faint">
          {hint}
        </p>
      )}
      {error && (
        <p id={errorId} className="mt-1 text-xs text-signal-danger">
          {error}
        </p>
      )}
    </div>
  );
}

const inputClass =
  "w-full rounded-md border bg-surface text-ink px-3 py-2 text-sm placeholder:text-ink-faint focus:outline-none focus:border-accent";

export default function AgentFormPage() {
  const { agentId } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(agentId);

  const [agent, setAgent] = useState(EMPTY_AGENT);
  const [tools, setTools] = useState([]);
  const [loading, setLoading] = useState(isEditing);
  const [loadError, setLoadError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [saveError, setSaveError] = useState("");
  const [saving, setSaving] = useState(false);
  const [savedNotice, setSavedNotice] = useState(false);
  const [showAddTool, setShowAddTool] = useState(false);
  const [toolsError, setToolsError] = useState("");

  useEffect(() => {
    if (!isEditing) return;
    setLoading(true);
    agentsApi
      .get(agentId)
      .then((data) => {
        setAgent({
          name: data.name,
          domain: data.domain,
          system_prompt: data.system_prompt,
          version: data.version,
          description: data.description || "",
        });
        setTools(data.tools || []);
      })
      .catch((err) => setLoadError(err.message))
      .finally(() => setLoading(false));
  }, [agentId, isEditing]);

  const update = (key) => (e) => setAgent((prev) => ({ ...prev, [key]: e.target.value }));

  const handleSave = async (e) => {
    e.preventDefault();
    const errors = validate(agent);
    setFieldErrors(errors);
    setSaveError("");
    setSavedNotice(false);
    if (Object.keys(errors).length > 0) return;

    setSaving(true);
    try {
      if (isEditing) {
        const updated = await agentsApi.update(agentId, agent);
        setAgent({
          name: updated.name,
          domain: updated.domain,
          system_prompt: updated.system_prompt,
          version: updated.version,
          description: updated.description || "",
        });
        setSavedNotice(true);
      } else {
        const created = await agentsApi.create(agent);
        navigate(`/agents/${created.id}`, { replace: true });
      }
    } catch (err) {
      setSaveError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleAddTool = async (toolPayload) => {
    setToolsError("");
    const created = await agentsApi.createTool(agentId, toolPayload);
    setTools((prev) => [...prev, created]);
    setShowAddTool(false);
  };

  if (loading) return <Spinner label="Loading agent…" />;
  if (loadError) return <ErrorBanner message={loadError} />;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center gap-2 text-sm text-ink-faint">
        <Link to="/agents" className="hover:text-ink">
          Agent Configuration
        </Link>
        <Icon name="chevronRight" className="h-3.5 w-3.5" />
        <span className="text-ink">{isEditing ? agent.name || "Edit agent" : "New agent"}</span>
      </div>

      <Card>
        <CardHeader
          title={isEditing ? "Agent details" : "Configure a new agent"}
          subtitle="This is what AgentGuard will target when generating and running test scenarios."
        />
        <form onSubmit={handleSave} className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Agent name" error={fieldErrors.name}>
              <input
                value={agent.name}
                onChange={update("name")}
                placeholder="Customer Support Agent"
                className={`${inputClass} ${fieldErrors.name ? "border-signal-danger" : "border-line"}`}
              />
            </Field>
            <Field label="Domain" error={fieldErrors.domain} hint="What the agent operates on, e.g. e-commerce support.">
              <input
                value={agent.domain}
                onChange={update("domain")}
                placeholder="Customer support"
                className={`${inputClass} ${fieldErrors.domain ? "border-signal-danger" : "border-line"}`}
              />
            </Field>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Version" hint="Used to compare reliability across agent versions.">
              <input
                value={agent.version}
                onChange={update("version")}
                placeholder="v1"
                className={`mono ${inputClass} border-line`}
              />
            </Field>
            <Field label="Description (optional)">
              <input
                value={agent.description}
                onChange={update("description")}
                placeholder="Short internal note about this agent"
                className={`${inputClass} border-line`}
              />
            </Field>
          </div>

          <Field
            label="System prompt"
            error={fieldErrors.system_prompt}
            hint="The exact system prompt the agent runs with — scenarios are generated against this."
          >
            <textarea
              value={agent.system_prompt}
              onChange={update("system_prompt")}
              rows={8}
              placeholder="You are a customer support agent for..."
              className={`mono ${inputClass} ${
                fieldErrors.system_prompt ? "border-signal-danger" : "border-line"
              }`}
            />
          </Field>

          {saveError && <ErrorBanner message={saveError} />}
          {savedNotice && (
            <p className="text-sm font-medium text-signal-safe">Changes saved.</p>
          )}

          <div className="flex items-center justify-end gap-2 border-t border-line pt-4">
            <Button as={Link} to="/agents" variant="secondary" type="button">
              Cancel
            </Button>
            <Button type="submit" loading={saving}>
              {isEditing ? "Save changes" : "Save agent"}
            </Button>
          </div>
        </form>
      </Card>

      <Card>
        <CardHeader
          title="Tools"
          subtitle={
            isEditing
              ? "Tools the agent can call. Mark destructive tools clearly — AgentGuard always calls a mocked version in sandbox runs."
              : "Save the agent first, then come back here to register its tools."
          }
          action={
            isEditing &&
            !showAddTool && (
              <Button size="sm" variant="secondary" onClick={() => setShowAddTool(true)}>
                <Icon name="plus" className="h-3.5 w-3.5" />
                Add tool
              </Button>
            )
          }
        />

        {toolsError && <ErrorBanner message={toolsError} className="mb-3" />}

        {isEditing && showAddTool && (
          <div className="mb-4">
            <AddToolForm onSubmit={handleAddTool} onCancel={() => setShowAddTool(false)} />
          </div>
        )}

        {isEditing ? (
          <Table
            rows={tools}
            emptyMessage="No tools registered yet. Add the tools this agent can call, such as lookup_order or refund_order."
            columns={[
              { key: "name", header: "Name", render: (t) => <span className="mono font-medium text-ink">{t.name}</span> },
              { key: "description", header: "Description", render: (t) => t.description || "—" },
              { key: "risk_level", header: "Risk", render: (t) => <RiskBadge level={t.risk_level} /> },
              { key: "destructive", header: "Destructive", render: (t) => <DestructiveBadge destructive={t.destructive} /> },
            ]}
          />
        ) : (
          <p className="text-sm text-ink-faint">Tool management unlocks once the agent is saved.</p>
        )}

        {isEditing && (
          <div className="mt-4 flex justify-end border-t border-line pt-4">
            <Button as={Link} to={`/scenarios?agentId=${agentId}`} variant="ghost" size="sm">
              Generate test scenarios for this agent
              <Icon name="chevronRight" className="h-3.5 w-3.5" />
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
}
