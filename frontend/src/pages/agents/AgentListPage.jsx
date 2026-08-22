import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import agentsApi from "../../api/agents";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import Table from "../../components/ui/Table";
import Spinner from "../../components/ui/Spinner";
import ErrorBanner from "../../components/ui/ErrorBanner";
import EmptyState from "../../components/ui/EmptyState";
import Modal from "../../components/ui/Modal";
import Icon from "../../components/ui/Icon";
import { formatDateTime } from "../../utils/format";

export default function AgentListPage() {
  const navigate = useNavigate();
  const [agents, setAgents] = useState(null);
  const [error, setError] = useState("");
  const [pendingDelete, setPendingDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState("");

  const load = () => {
    setError("");
    agentsApi
      .list()
      .then(setAgents)
      .catch((err) => setError(err.message));
  };

  useEffect(load, []);

  const confirmDelete = async () => {
    if (!pendingDelete) return;
    setDeleting(true);
    setDeleteError("");
    try {
      await agentsApi.remove(pendingDelete.id);
      setAgents((prev) => prev.filter((a) => a.id !== pendingDelete.id));
      setPendingDelete(null);
    } catch (err) {
      setDeleteError(err.message);
    } finally {
      setDeleting(false);
    }
  };

  if (error) return <ErrorBanner message={error} />;
  if (!agents) return <Spinner label="Loading agents…" />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-ink-faint">
          {agents.length} agent{agents.length === 1 ? "" : "s"} configured
        </p>
        <Button as={Link} to="/agents/new">
          <Icon name="plus" className="h-4 w-4" />
          New agent
        </Button>
      </div>

      {agents.length === 0 ? (
        <EmptyState
          icon="cpu"
          title="No agents yet"
          description="Register an agent's system prompt, domain, and tools so AgentGuard can generate test scenarios for it."
          action={
            <Button as={Link} to="/agents/new">
              Configure your first agent
            </Button>
          }
        />
      ) : (
        <Card padded={false}>
          <Table
            rows={agents}
            onRowClick={(agent) => navigate(`/agents/${agent.id}`)}
            columns={[
              {
                key: "name",
                header: "Agent",
                render: (a) => (
                  <div>
                    <p className="font-medium text-ink">{a.name}</p>
                    <p className="text-xs text-ink-faint">{a.version}</p>
                  </div>
                ),
              },
              { key: "domain", header: "Domain" },
              {
                key: "tools",
                header: "Tools",
                render: (a) => `${(a.tools || []).length}`,
              },
              {
                key: "destructive",
                header: "Destructive tools",
                render: (a) => (a.tools || []).filter((t) => t.destructive).length,
              },
              {
                key: "created_at",
                header: "Created",
                render: (a) => formatDateTime(a.created_at),
              },
              {
                key: "actions",
                header: "",
                render: (a) => (
                  <div className="flex items-center gap-3">
                    <Link
                      to={`/agents/${a.id}`}
                      onClick={(e) => e.stopPropagation()}
                      className="text-xs font-medium text-accent hover:text-accent-hover"
                    >
                      Edit
                    </Link>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setPendingDelete(a);
                        setDeleteError("");
                      }}
                      className="text-xs font-medium text-signal-danger hover:underline"
                    >
                      Delete
                    </button>
                  </div>
                ),
              },
            ]}
          />
        </Card>
      )}

      <Modal
        open={!!pendingDelete}
        title={`Delete "${pendingDelete?.name}"?`}
        onClose={() => setPendingDelete(null)}
      >
        <p className="text-sm text-ink-soft">
          This permanently removes the agent and its tool configuration. This cannot be undone.
        </p>
        {deleteError && <ErrorBanner message={deleteError} className="mt-3" />}
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setPendingDelete(null)} disabled={deleting}>
            Cancel
          </Button>
          <Button variant="danger" onClick={confirmDelete} loading={deleting}>
            Delete agent
          </Button>
        </div>
      </Modal>
    </div>
  );
}
