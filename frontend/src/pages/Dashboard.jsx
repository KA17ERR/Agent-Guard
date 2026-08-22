import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import agentsApi from "../api/agents";
import Card, { CardHeader } from "../components/ui/Card";
import Button from "../components/ui/Button";
import Spinner from "../components/ui/Spinner";
import ErrorBanner from "../components/ui/ErrorBanner";
import EmptyState from "../components/ui/EmptyState";
import Icon from "../components/ui/Icon";
import { CategoryBars } from "../components/charts/ScoreTrendChart";
import { humanize } from "../utils/format";
import { RISK_LEVELS } from "../utils/constants";

function StatCard({ label, value, hint }) {
  return (
    <Card>
      <p className="text-xs font-medium uppercase tracking-wide text-ink-faint">{label}</p>
      <p className="mt-1.5 text-2xl font-semibold text-ink">{value}</p>
      {hint && <p className="mt-1 text-xs text-ink-faint">{hint}</p>}
    </Card>
  );
}

export default function Dashboard() {
  const [agents, setAgents] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    agentsApi
      .list()
      .then(setAgents)
      .catch((err) => setError(err.message));
  }, []);

  const stats = useMemo(() => {
    if (!agents) return null;
    const allTools = agents.flatMap((a) => a.tools || []);
    const destructive = allTools.filter((t) => t.destructive);
    const byRisk = RISK_LEVELS.map((level) => ({
      label: humanize(level),
      value: allTools.filter((t) => t.risk_level === level).length,
    }));
    return {
      agentCount: agents.length,
      toolCount: allTools.length,
      destructiveCount: destructive.length,
      byRisk,
    };
  }, [agents]);

  if (error) {
    return <ErrorBanner message={error} />;
  }

  if (!agents) {
    return <Spinner label="Loading dashboard…" />;
  }

  if (agents.length === 0) {
    return (
      <EmptyState
        icon="cpu"
        title="No agents configured yet"
        description="Add an agent's system prompt, domain, and tools to start generating reliability test scenarios for it."
        action={
          <Button as={Link} to="/agents/new">
            Configure your first agent
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label="Agents configured" value={stats.agentCount} />
        <StatCard label="Tools registered" value={stats.toolCount} />
        <StatCard
          label="Destructive tools"
          value={stats.destructiveCount}
          hint={stats.destructiveCount > 0 ? "Run in sandbox only" : "None registered"}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader
            title="Tools by risk level"
            subtitle="Across every configured agent"
          />
          <CategoryBars data={stats.byRisk} color="accent" />
        </Card>

        <Card>
          <CardHeader
            title="Agents"
            action={
              <Link to="/agents" className="text-xs font-medium text-accent hover:text-accent-hover">
                View all
              </Link>
            }
          />
          <ul className="divide-y divide-line">
            {agents.slice(0, 6).map((agent) => (
              <li key={agent.id} className="py-2.5 first:pt-0 last:pb-0">
                <Link to={`/agents/${agent.id}`} className="block">
                  <p className="text-sm font-medium text-ink">{agent.name}</p>
                  <p className="text-xs text-ink-faint">
                    {agent.domain} · {(agent.tools || []).length} tool
                    {(agent.tools || []).length === 1 ? "" : "s"}
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <Card>
        <CardHeader
          title="Reliability testing workflow"
          subtitle="Jump to any step — each one operates on real, generated and executed data."
        />
        <div className="flex flex-wrap gap-2">
          {[
            { to: "/scenarios", label: "Generate scenarios", icon: "flask" },
            { to: "/execution", label: "Run test suite", icon: "play" },
            { to: "/results", label: "View results", icon: "list" },
            { to: "/report", label: "Reliability report", icon: "shield" },
            { to: "/regression", label: "Compare versions", icon: "trend" },
          ].map((step) => (
            <Link
              key={step.to}
              to={step.to}
              className="inline-flex items-center gap-1.5 rounded-full border border-line px-3 py-1.5 text-xs font-medium text-ink-soft hover:border-accent hover:text-accent"
            >
              {step.label}
              <Icon name="chevronRight" className="h-3 w-3" />
            </Link>
          ))}
        </div>
      </Card>
    </div>
  );
}
