import { useEffect, useId, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import agentsApi from "../../api/agents";
import scenariosApi from "../../api/scenarios";
import { useRunContext } from "../../context/RunContext";
import Card, { CardHeader } from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import ErrorBanner from "../../components/ui/ErrorBanner";
import EmptyState from "../../components/ui/EmptyState";
import Icon from "../../components/ui/Icon";
import CategoryLegend from "./CategoryLegend";
import ScenarioCard from "./ScenarioCard";

export default function ScenarioGenerationPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { addScenarios } = useRunContext();
  const agentSelectId = useId();
  const countInputId = useId();

  const [agents, setAgents] = useState(null);
  const [agentsError, setAgentsError] = useState("");
  const [selectedAgentId, setSelectedAgentId] = useState(searchParams.get("agentId") || "");
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [agentLoading, setAgentLoading] = useState(false);

  const [numberOfScenarios, setNumberOfScenarios] = useState(8);
  const [generating, setGenerating] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [generateError, setGenerateError] = useState("");
  const [result, setResult] = useState(null); // ScenarioGenerateResponse

  // Scenarios already generated for this agent in a previous session,
  // fetched fresh from the backend (GET /api/agents/{id}/scenarios) so
  // they aren't lost on refresh or when switching agents and back.
  const [existingScenarios, setExistingScenarios] = useState(null);
  const [existingError, setExistingError] = useState("");
  const [existingLoading, setExistingLoading] = useState(false);

  // Load the agent picker.
  useEffect(() => {
    agentsApi
      .list()
      .then(setAgents)
      .catch((err) => setAgentsError(err.message));
  }, []);

  // Load full agent detail (system prompt, tools) whenever the selection changes.
  useEffect(() => {
    if (!selectedAgentId) {
      setSelectedAgent(null);
      return;
    }
    setAgentLoading(true);
    agentsApi
      .get(selectedAgentId)
      .then(setSelectedAgent)
      .catch((err) => setAgentsError(err.message))
      .finally(() => setAgentLoading(false));
  }, [selectedAgentId]);

  // Real elapsed-time counter while the (synchronous) generation call is in
  // flight. This is intentionally NOT a fake percentage/progress bar — the
  // backend generates the whole batch in one blocking LLM call with no
  // progress callbacks, so ticking seconds is the only honest signal we have.
  useEffect(() => {
    if (!generating) return;
    setElapsedSeconds(0);
    const interval = setInterval(() => setElapsedSeconds((s) => s + 1), 1000);
    return () => clearInterval(interval);
  }, [generating]);

  // Fetch previously generated scenarios for this agent whenever the
  // selection changes, so they show up even without generating anything
  // new in this session. Also syncs them into RunContext so other pages
  // (Test Execution, Trace Viewer) can look them up by id.
  useEffect(() => {
    setResult(null);
    if (!selectedAgentId) {
      setExistingScenarios(null);
      return;
    }
    setExistingLoading(true);
    setExistingError("");
    scenariosApi
      .list(selectedAgentId)
      .then((scenarios) => {
        setExistingScenarios(scenarios);
        if (scenarios.length > 0) {
          addScenarios(selectedAgent, scenarios);
        }
      })
      .catch((err) => setExistingError(err.message))
      .finally(() => setExistingLoading(false));
    // selectedAgent is intentionally excluded: it loads asynchronously
    // right after selectedAgentId changes, and we only need whichever
    // value is current at the time addScenarios actually runs above.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedAgentId]);

  const handleGenerate = async () => {
    setGenerateError("");
    setResult(null);
    setGenerating(true);
    try {
      const response = await scenariosApi.generate({
        agentId: selectedAgentId,
        numberOfScenarios: Number(numberOfScenarios),
      });
      setResult(response);
      addScenarios(selectedAgent, response.scenarios);
      // Re-fetch from the backend so `existingScenarios` reflects the full,
      // persisted set (this batch plus any earlier ones) rather than just
      // what this one response returned.
      scenariosApi
        .list(selectedAgentId)
        .then(setExistingScenarios)
        .catch(() => {}); // non-fatal: the "just generated" card below still shows the new batch
    } catch (err) {
      setGenerateError(err.message);
    } finally {
      setGenerating(false);
    }
  };

  const proceedToExecution = () => navigate("/execution");

  if (agentsError) return <ErrorBanner message={agentsError} />;
  if (!agents) return <Spinner label="Loading agents…" />;

  if (agents.length === 0) {
    return (
      <EmptyState
        icon="cpu"
        title="No agents to generate scenarios for"
        description="Configure an agent first — AgentGuard generates scenarios from its system prompt, domain, and registered tools."
        action={
          <Button as={Link} to="/agents/new">
            Configure an agent
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader title="Agent" subtitle="Scenarios are generated from this agent's system prompt, domain, and tools." />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-[280px_1fr]">
          <div>
            <label htmlFor={agentSelectId} className="mb-1 block text-xs font-medium text-ink-soft">
              Select agent
            </label>
            <select
              id={agentSelectId}
              value={selectedAgentId}
              onChange={(e) => {
                setSelectedAgentId(e.target.value);
                setResult(null);
              }}
              className="w-full rounded-md border border-line bg-surface px-3 py-2 text-sm focus:border-accent focus:outline-none"
            >
              <option value="">Choose an agent…</option>
              {agents.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} ({a.domain})
                </option>
              ))}
            </select>

            <label htmlFor={countInputId} className="mb-1 mt-4 block text-xs font-medium text-ink-soft">
              Number of scenarios
            </label>
            <input
              id={countInputId}
              type="number"
              min={1}
              max={30}
              value={numberOfScenarios}
              onChange={(e) => setNumberOfScenarios(e.target.value)}
              aria-describedby={`${countInputId}-hint`}
              className="w-full rounded-md border border-line bg-surface px-3 py-2 text-sm focus:border-accent focus:outline-none"
            />
            <p id={`${countInputId}-hint`} className="mt-1 text-xs text-ink-faint">
              Between 1 and 30.
            </p>
          </div>

          <div>
            {agentLoading && <Spinner label="Loading agent details…" />}
            {!agentLoading && selectedAgent && (
              <div className="rounded-md border border-line bg-canvas p-3">
                <p className="text-sm font-semibold text-ink">{selectedAgent.name}</p>
                <p className="text-xs text-ink-faint">
                  {selectedAgent.domain} · {selectedAgent.version} · {(selectedAgent.tools || []).length} tool
                  {(selectedAgent.tools || []).length === 1 ? "" : "s"}
                </p>
                <p className="mono mt-2 max-h-24 overflow-y-auto whitespace-pre-wrap text-xs text-ink-soft">
                  {selectedAgent.system_prompt}
                </p>
              </div>
            )}
            {!agentLoading && !selectedAgent && (
              <div className="flex h-full items-center justify-center rounded-md border border-dashed border-line p-3 text-sm text-ink-faint">
                Select an agent to see its details.
              </div>
            )}
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader title="Scenario categories" subtitle="Every AgentGuard test run draws from this fixed taxonomy." />
        <CategoryLegend />
      </Card>

      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <CardHeader
            title="Generate test suite"
            subtitle="Calls the configured LLM provider to write realistic and adversarial scenarios for this agent."
          />
          <Button onClick={handleGenerate} disabled={!selectedAgentId} loading={generating}>
            <Icon name="flask" className="h-4 w-4" />
            Generate Test Suite
          </Button>
        </div>

        {generating && (
          <div className="mt-2 flex items-center gap-2 text-sm text-ink-faint">
            <span className="h-2 w-2 animate-pulse rounded-full bg-accent" />
            Generating {numberOfScenarios} scenarios for {selectedAgent?.name || "the selected agent"}… {elapsedSeconds}s
            <span className="text-ink-faint">(this can take up to a minute)</span>
          </div>
        )}

        {generateError && <ErrorBanner message={generateError} className="mt-3" />}
      </Card>

      {existingError && <ErrorBanner message={existingError} />}

      {existingLoading && <Spinner label="Loading previously generated scenarios…" />}

      {!existingLoading && !result && existingScenarios && existingScenarios.length > 0 && (
        <Card>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <CardHeader
              title={`Previously generated scenarios (${existingScenarios.length})`}
              subtitle="Loaded from the database — generated in an earlier session."
            />
            <Button onClick={proceedToExecution} variant="secondary">
              Continue to Test Execution
              <Icon name="chevronRight" className="h-4 w-4" />
            </Button>
          </div>

          <div className="space-y-3">
            {existingScenarios.map((scenario) => (
              <ScenarioCard key={scenario.id} scenario={scenario} />
            ))}
          </div>
        </Card>
      )}

      {result && (
        <Card>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <CardHeader
              title={`Generated scenarios (${result.generated})`}
              subtitle="You'll choose which of these to run on the Test Execution page."
            />
            <Button onClick={proceedToExecution} variant="secondary">
              Continue to Test Execution
              <Icon name="chevronRight" className="h-4 w-4" />
            </Button>
          </div>

          <div className="space-y-3">
            {result.scenarios.map((scenario) => (
              <ScenarioCard key={scenario.id} scenario={scenario} />
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
